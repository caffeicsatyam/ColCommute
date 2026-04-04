import os
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"

def get_model_config():
    """Returns the shared model configuration for all agents."""
    return {
        "model": MODEL_NAME,
        "api_key": os.getenv("GOOGLE_API_KEY")
    }
