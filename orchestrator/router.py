import asyncio
import time
import uuid
from typing import Optional

from adapters.groq import groq_infer
from adapters.gemini import gemini_audit
from config import settings
from orchestrator.merge import merge_answers


CONFIDENCE_THRESHOLD = 0.70

# In-memory storage for watchdog results
WATCHDOG_RESULTS = {}


def estimate_confidence(prompt: str, groq_output: str) -> float:
    """
    Very lightweight confidence estimator (v1).
    No external calls. No dependencies.
    """

    length_penalty = min(len(prompt) / 4000, 1.0)
    base_confidence = 0.85

    confidence = base_confidence - (0.3 * length_penalty)

    return round(max(confidence, 0.0), 2)


async def route_request(packet: dict) -> dict:
    """
    Hybrid routing logic:
    - Groq fast path by default
    - Optional Gemini watchdog (async)
    """
    start_time = time.time()
    
    request_id = packet.get("request_id", str(uuid.uuid4()))
    
    # Support both prompt (legacy) and messages (proper chat)
    messages = packet.get("messages")
    prompt = packet.get("prompt")
    
    # Groq fast path
    groq_start = time.time()
    if messages:
        groq_out, _ = await groq_infer(messages=messages)
        # Extract last user message for confidence estimation
        user_messages = [m for m in messages if m.get("role") == "user"]
        prompt_for_confidence = user_messages[-1].get("content", "") if user_messages else ""
    else:
        groq_out, _ = await groq_infer(prompt=prompt)
        prompt_for_confidence = prompt
    groq_time_ms = (time.time() - groq_start) * 1000

    confidence = estimate_confidence(prompt_for_confidence, groq_out)

    need_watchdog = False
    watchdog_reason = None
    watchdog_status = "skipped"

    if packet.get("verify"):
        need_watchdog = True
        watchdog_reason = "forced_by_user"
    elif confidence < CONFIDENCE_THRESHOLD:
        need_watchdog = True
        watchdog_reason = "low_confidence"

    if need_watchdog:
        watchdog_status = "pending"

    gemini_task: Optional[asyncio.Task] = None
    result_holder = {}

    async def run_gemini_merge(
        prompt_text,
        groq_answer,
        request_id_value,
        reason,
        holder,
    ):
        gemini_start = time.time()
        audit_prompt = f"""
USER PROMPT:
{prompt_text}

GROQ ANSWER:
{groq_answer}
"""
        gemini_result = await gemini_audit(audit_prompt)
        gemini_time_ms = (time.time() - gemini_start) * 1000
        
        merge_result = merge_answers(groq_answer, gemini_result)
        holder["merge"] = merge_result
        holder["request_id"] = request_id_value
        holder["reason"] = reason
        holder["gemini_ms"] = gemini_time_ms
        
        # Store result for later retrieval
        WATCHDOG_RESULTS[request_id_value] = {
            "request_id": request_id_value,
            "status": "completed",
            "gemini_status": gemini_result.get("status"),
            "final_answer": merge_result.get("final_answer"),
            "merge_explanation": merge_result.get("explanation"),
            "gemini_ms": gemini_time_ms,
        }

    # Fire Gemini asynchronously if required
    if need_watchdog and settings.ENABLE_GEMINI_WATCHDOG:
        gemini_task = asyncio.create_task(
            run_gemini_merge(
                prompt_for_confidence,  # Use the extracted prompt
                groq_out,
                request_id,
                watchdog_reason,
                result_holder,
            )
        )
        watchdog_status = "pending"
    elif need_watchdog:
        watchdog_status = "skipped"

    total_time_ms = (time.time() - start_time) * 1000
    
    # Return immediately (Gemini may still be running)
    return {
        "request_id": request_id,
        "primary_model": settings.GROQ_MODEL,
        "confidence": confidence,
        "watchdog": {
            "enabled": need_watchdog,
            "reason": watchdog_reason,
            "status": watchdog_status,
        },
        "content": groq_out,
        "timing": {
            "groq_ms": round(groq_time_ms, 2),
            "total_ms": round(total_time_ms, 2),
        },
        "gemini_task": gemini_task,
        "merge_result_holder": result_holder,
    }


def get_watchdog_result(request_id: str) -> dict:
    """Retrieve completed watchdog result by request_id"""
    if request_id in WATCHDOG_RESULTS:
        return WATCHDOG_RESULTS[request_id]
    return {
        "request_id": request_id,
        "status": "not_found",
        "gemini_status": None,
        "final_answer": None,
        "merge_explanation": None,
        "gemini_ms": None,
    }
