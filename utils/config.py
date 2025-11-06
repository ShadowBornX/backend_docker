# python_backend/utils/config.py
import os
from dotenv import load_dotenv
from typing import Optional, List

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Centralized configuration class for the backend.
    Loads environment variables and provides easy access to them.
    """
    # OpenAI API Key
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    # Default OpenAI Model
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # CORS Origins for Frontend (comma-separated string in .env)
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(',')

    # Optional: Database URL (if you decide to use a database later)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # Optional: Other configuration settings
    APP_VERSION: str = "1.0.0"
    APP_NAME: str = "Asistente Untels Backend"

    def __init__(self):
        if not self.OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY is not set. OpenAI API calls might fail.")
        if not self.CORS_ORIGINS:
            print("Warning: CORS_ORIGINS is not set. Cross-origin requests might be blocked.")

# Singleton instance
settings = Config()
