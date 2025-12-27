from pydantic import BaseModel
from typing import Optional, List
import time
import uuid


class HybridChatRequest(BaseModel):
    prompt: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    verify: Optional[bool] = False


# OpenAI-compatible schemas
class ChatMessage(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    stream: Optional[bool] = False


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage


class TimingInfo(BaseModel):
    groq_ms: float
    total_ms: float


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
    timing: TimingInfo


class WatchdogResult(BaseModel):
    request_id: str
    status: str
    gemini_status: Optional[str] = None
    final_answer: Optional[str] = None
    merge_explanation: Optional[str] = None
    gemini_ms: Optional[float] = None
