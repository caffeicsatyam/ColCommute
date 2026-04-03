import os
from dotenv import load_dotenv

load_dotenv()

def get_model_config():
    """Returns the shared model configuration for all agents."""
    return {
        "model": "gemini-2.5-flash",
        "api_key": os.getenv("GOOGLE_API_KEY")
    }
