import os
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gemini-2.5-flash-lite"

def get_model_config():
    """Returns the model name string for all agents."""
    return MODEL_NAME