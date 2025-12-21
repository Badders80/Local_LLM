import asyncio
import uuid
from typing import Optional

from adapters.groq import groq_infer
from adapters.gemini import gemini_audit
from config import settings
from orchestrator.merge import merge_answers


CONFIDENCE_THRESHOLD = 0.70


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

    request_id = packet.get("request_id", str(uuid.uuid4()))
    prompt = packet["prompt"]
    # Groq fast path
    groq_out, _ = await groq_infer(prompt)

    confidence = estimate_confidence(prompt, groq_out)

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
        audit_prompt = f"""
USER PROMPT:
{prompt_text}

GROQ ANSWER:
{groq_answer}
"""
        gemini_result = gemini_audit(audit_prompt)
        holder["merge"] = merge_answers(groq_answer, gemini_result)
        holder["request_id"] = request_id_value
        holder["reason"] = reason

    # Fire Gemini asynchronously if required
    if need_watchdog and settings.ENABLE_GEMINI_WATCHDOG:
        gemini_task = asyncio.create_task(
            run_gemini_merge(
                prompt,
                groq_out,
                request_id,
                watchdog_reason,
                result_holder,
            )
        )
        watchdog_status = "pending"
    elif need_watchdog:
        watchdog_status = "skipped"

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
        "gemini_task": gemini_task,
        "merge_result_holder": result_holder,
    }
