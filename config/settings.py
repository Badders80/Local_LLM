import os
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.config/evo-secrets/.env"))

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
ENABLE_GEMINI_WATCHDOG = os.getenv("ENABLE_GEMINI_WATCHDOG", "true").lower() in (
    "1",
    "true",
    "yes",
    "on",
)

# General
ENV = os.getenv("ENV", "dev")
