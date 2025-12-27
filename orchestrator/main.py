from fastapi import FastAPI
from orchestrator.router import route_request, get_watchdog_result
from orchestrator.schemas import (
    HybridChatRequest, 
    HybridResponse, 
    WatchdogResult,
    OpenAIChatRequest,
    OpenAIChatResponse,
    ChatCompletionChoice,
    ChatMessage,
    ChatCompletionUsage
)
import time
import uuid

app = FastAPI()


@app.get("/")
def root():
    return {
        "service": "Hybrid LLM Orchestrator",
        "status": "running",
        "endpoints": [
            "/health", 
            "/hybrid-chat", 
            "/watchdog/{request_id}", 
            "/v1/chat/completions (OpenAI-compatible)",
            "/docs"
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/hybrid-chat", response_model=HybridResponse)
async def hybrid_chat(payload: HybridChatRequest):
    result = await route_request(payload.dict())
    result.pop("gemini_task", None)
    result.pop("merge_result_holder", None)
    return result


@app.get("/watchdog/{request_id}", response_model=WatchdogResult)
def get_watchdog(request_id: str):
    """Get the completed Gemini watchdog result for a request"""
    return get_watchdog_result(request_id)


@app.post("/v1/chat/completions", response_model=OpenAIChatResponse)
async def openai_chat_completions(payload: OpenAIChatRequest):
    """OpenAI-compatible endpoint for VS Code and other tools"""
    # Extract the last user message as the prompt
    user_messages = [msg for msg in payload.messages if msg.role == "user"]
    if not user_messages:
        prompt = ""
    else:
        prompt = user_messages[-1].content
    
    # Route through hybrid system
    result = await route_request({
        "prompt": prompt,
        "verify": False  # Default to fast mode for coding
    })
    
    # Convert to OpenAI format
    response = OpenAIChatResponse(
        id=f"chatcmpl-{result['request_id']}",
        created=int(time.time()),
        model="hybrid-groq-gemini",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=result["content"]
                ),
                finish_reason="stop"
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(result["content"].split()),
            total_tokens=len(prompt.split()) + len(result["content"].split())
        )
    )
    
    return response
