import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL_NAME = "gemini-2.5-flash-lite"
DEFAULT_FALLBACK_MODEL_NAME = "gemini-2.5-flash"


def _read_env(*keys: str) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value and value.strip():
            return value.strip()
    return None


MODEL_NAME = _read_env(
    "COLCOMMUTE_MODEL",
    "MODEL_NAME",
    "GOOGLE_GENAI_MODEL",
) or DEFAULT_MODEL_NAME

FALLBACK_MODEL_NAME = _read_env(
    "COLCOMMUTE_FALLBACK_MODEL",
    "FALLBACK_MODEL_NAME",
    "GOOGLE_GENAI_FALLBACK_MODEL",
) or DEFAULT_FALLBACK_MODEL_NAME


def get_model_config(use_fallback: bool = False) -> str:
    """Return the configured model name, optionally forcing the fallback model."""
    if use_fallback and FALLBACK_MODEL_NAME:
        return FALLBACK_MODEL_NAME
    return MODEL_NAME or FALLBACK_MODEL_NAME


def get_model_candidates() -> list[str]:
    """Return the primary model followed by the fallback model, without duplicates."""
    candidates: list[str] = []
    for model_name in [MODEL_NAME, FALLBACK_MODEL_NAME]:
        if model_name and model_name not in candidates:
            candidates.append(model_name)
    return candidates
