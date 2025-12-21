from google import genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)


def gemini_audit(prompt: str) -> dict:
    """
    Gemini watchdog:
    - verifies factual accuracy
    - suggests correction ONLY if necessary
    """

    system_prompt = (
        "You are a factual auditor.\n\n"
        "Rules:\n"
        "- If the answer is correct, respond with:\n"
        "  STATUS: OK\n\n"
        "- If incorrect or hallucinated, respond with:\n"
        "  STATUS: CORRECT\n"
        "  FIXED_ANSWER: <corrected answer>\n\n"
        "Be concise. No commentary."
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            {
                "role": "user",
                "parts": [
                    {"text": system_prompt},
                    {"text": "\n\n"},
                    {"text": prompt},
                ],
            }
        ],
    )

    text = response.text.strip()

    if text.startswith("STATUS: OK"):
        return {"status": "ok"}

    if text.startswith("STATUS: CORRECT"):
        fixed = text.split("FIXED_ANSWER:", 1)[-1].strip()
        return {
            "status": "corrected",
            "fixed_answer": fixed,
        }

    # Failsafe
    return {"status": "unknown", "raw": text}
