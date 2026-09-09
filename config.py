import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)

    if not value or value.startswith("your_"):
        raise RuntimeError(
            f"{name} is missing. Add a valid value to your .env file."
        )

    return value


GROQ_API_KEY = require_env("GROQ_API_KEY")
MEM0_API_KEY = require_env("MEM0_API_KEY")

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MEM0_USER_ID = os.getenv("MEM0_USER_ID", "demo-user")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SQLITE_PATH = DATA_DIR / "checkpoints.sqlite"
MEMORY_TOP_K = 3