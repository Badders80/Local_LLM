import asyncio
import random
from config.settings import GROQ_MODEL


async def groq_infer(prompt: str):
    """
    Simulated Groq call (replace with real SDK later)
    """
    await asyncio.sleep(0.05)

    output = f"[Groq:{GROQ_MODEL}] {prompt}"
    confidence = round(random.uniform(0.25, 0.9), 2)

    return output, confidence
