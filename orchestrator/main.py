from fastapi import FastAPI
from orchestrator.router import route_request
from orchestrator.schemas import HybridChatRequest, HybridResponse

app = FastAPI()


@app.get("/")
def root():
    return {
        "service": "Hybrid LLM Orchestrator",
        "status": "running",
        "endpoints": ["/health", "/hybrid-chat", "/docs"],
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
