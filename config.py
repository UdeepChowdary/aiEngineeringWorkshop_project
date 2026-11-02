import os
from typing import Tuple
from google import genai
from dotenv import load_dotenv

load_dotenv()

# High-speed reliable Gemini models for multi-agent reasoning
MODELS = ["gemini-3.5-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]
DEFAULT_MODEL = os.getenv("EXAM_SENTINEL_MODEL", MODELS[0])

def get_gemini_api_key(manual_key: str = None) -> str:
    """Retrieves Gemini API key. Strictly prioritizes manual user BYOK key."""
    if manual_key and manual_key.strip():
        return manual_key.strip()

    # Optional local CLI fallback only (never used if running in strict BYOK web mode)
    env_key = os.getenv("GEMINI_API_KEY")
    return env_key.strip() if env_key else ""

def get_gemini_client(manual_key: str = None) -> genai.Client:
    """Returns an authenticated official Google GenAI Client with the user's BYOK key."""
    api_key = get_gemini_api_key(manual_key)
    if not api_key:
        raise ValueError(
            "Missing Gemini API Key! Please enter your personal Google Gemini API key "
            "in the sidebar to summon the multi-agent committee."
        )
    return genai.Client(api_key=api_key)

def verify_gemini_key(api_key: str) -> Tuple[bool, str]:
    """Tests if a user-supplied API key is authentic and active."""
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty."
    try:
        client = genai.Client(api_key=api_key.strip())
        res = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents="ping",
        )
        return True, "Key is authentic, active, and has tokens!"
    except Exception as e:
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg or "400" in err_msg:
            return False, "Invalid API key. Please check that you copied the complete key."
        elif "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            return False, "Rate limit / quota exceeded on this key."
        return False, err_msg
