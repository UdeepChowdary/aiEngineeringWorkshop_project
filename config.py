import os
from typing import Tuple
from google import genai
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

def get_gemini_api_key(manual_key: str = None) -> str:
    """Retrieves Gemini API key with priority: manual BYOK input > st.secrets > os.environ."""
    if manual_key and manual_key.strip():
        return manual_key.strip()

    # Check Streamlit Cloud secrets if running within Streamlit
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key.strip()

    return ""

# High-speed reliable Gemini models for multi-agent reasoning
MODELS = ["gemini-3.5-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]
DEFAULT_MODEL = os.getenv("EXAM_SENTINEL_MODEL", MODELS[0])

def get_gemini_client(manual_key: str = None) -> genai.Client:
    """Returns an authenticated official Google GenAI Client."""
    api_key = get_gemini_api_key(manual_key)
    if not api_key:
        raise ValueError(
            "No API key provided! Please enter your Gemini API key in the sidebar "
            "or set GEMINI_API_KEY in your environment/secrets."
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
        return True, "Key is authentic and active!"
    except Exception as e:
        return False, str(e)
