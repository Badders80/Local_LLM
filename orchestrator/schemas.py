from pydantic import BaseModel
from typing import Optional


class HybridChatRequest(BaseModel):
    prompt: str
    verify: Optional[bool] = False


class WatchdogInfo(BaseModel):
    enabled: bool
    reason: Optional[str] = None
    status: Optional[str] = None  # pending | completed | skipped


class HybridResponse(BaseModel):
    request_id: str
    primary_model: str
    confidence: float
    watchdog: WatchdogInfo
    content: str
