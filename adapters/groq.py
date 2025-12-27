from groq import AsyncGroq
from config.settings import GROQ_API_KEY, GROQ_MODEL
import logging

logger = logging.getLogger(__name__)
client = AsyncGroq(api_key=GROQ_API_KEY)


async def groq_infer(prompt: str = None, messages: list = None, temperature: float = 0.7, max_tokens: int = 1024):
    """
    Real Groq API call using llama-3.3-70b-versatile
    Returns (answer, confidence_score)
    
    Args:
        prompt: Simple string prompt (legacy - converted to user message)
        messages: Full message array [{"role": "...", "content": "..."}]
        temperature: Model temperature
        max_tokens: Maximum tokens in response
    """
    try:
        # Build messages array
        if messages:
            # Use provided messages array
            groq_messages = messages
        elif prompt:
            # Legacy mode: convert prompt string to user message
            groq_messages = [{"role": "user", "content": prompt}]
        else:
            raise ValueError("Either 'prompt' or 'messages' must be provided")
        
        chat_completion = await client.chat.completions.create(
            messages=groq_messages,
            model=GROQ_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        output = chat_completion.choices[0].message.content
        
        # Estimate confidence based on finish_reason and response quality
        finish_reason = chat_completion.choices[0].finish_reason
        confidence = 0.85 if finish_reason == "stop" else 0.65

        return output, confidence
    
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        raise Exception(f"Groq inference failed: {str(e)}")
