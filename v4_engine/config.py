import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# --- THE VAULT PROTOCOL ---
# Based on your screenshot, the vault is in /mnt/scratch/vault/
vault_path = Path("/mnt/scratch/vault/central_keys.env")

if not vault_path.exists():
    print(f"CRITICAL: Vault not found at {vault_path}")
    sys.exit(1)

load_dotenv(vault_path)


class Config:
    PROJECT_ROOT = Path(__file__).parent.parent
    MODELS_DIR = PROJECT_ROOT / "models"
    ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

    # API Keys - Matching your screenshot exactly
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    # For LM Studio, we just need a placeholder
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")

    @classmethod
    def validate(cls):
        required_dirs = [cls.MODELS_DIR, cls.ARTIFACTS_DIR]
        for d in required_dirs:
            if not d.exists():
                print(f"ERROR: Missing directory {d}")
                sys.exit(1)

        if not cls.GROQ_API_KEY:
            print("ERROR: GROQ_API_KEY missing from vault.")
            sys.exit(1)

        return True
