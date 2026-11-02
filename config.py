import os
from google import genai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set! Please add it to your .env file:\n"
        "GEMINI_API_KEY=your_gemini_api_key_here"
    )

# High-speed reliable Gemini models for multi-agent reasoning
MODELS = ["gemini-3.5-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]
DEFAULT_MODEL = os.getenv("EXAM_SENTINEL_MODEL", MODELS[0])

def get_gemini_client() -> genai.Client:
    """Returns an authenticated official Google GenAI Client."""
    return genai.Client(api_key=GEMINI_API_KEY)
