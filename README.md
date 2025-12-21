# Hybrid LLM Orchestrator (v0.1)

This service is a low-latency hybrid LLM engine that prioritizes speed
while maintaining optional factual validation.

## Architecture

- Primary model: Groq (llama-3.3-70b-versatile)
- Confidence-gated execution
- Optional Gemini watchdog (async, non-blocking)
- FastAPI service

## Request Flow

1. User prompt -> Groq (fast path)
2. Confidence estimated locally
3. Gemini watchdog triggered only if:
   - confidence < threshold
   - or verify=true
4. Groq response returned immediately
5. Gemini runs in background (audit / future merge)

## Endpoints

- `GET /health`
- `POST /hybrid-chat`
- `GET /docs` (Swagger UI)

## Configuration

Environment variables are loaded from:

`~/.config/evo-secrets/.env`

Key flags:
- `ENABLE_GEMINI_WATCHDOG=true|false`
- `GROQ_MODEL=llama-3.3-70b-versatile`

## Guarantees

- Sub-second response on Groq path
- No blocking on Gemini
- Clear routing metadata

## Non-Goals (v0.1)

- No automatic answer replacement
- No streaming yet
- No persistent memory

This is an intentionally minimal, observable foundation.
