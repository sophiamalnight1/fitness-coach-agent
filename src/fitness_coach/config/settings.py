"""Configuration settings for the fitness coach application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)


class Settings:
    """Application settings."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0"))
    
    # Ollama Configuration
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "tinyllama")
    USE_OLLAMA: bool = os.getenv("USE_OLLAMA", "false").lower() == "true"
    
    # Application Settings
    APP_NAME: str = "AI Fitness Coach"
    APP_VERSION: str = "0.1.0"
    
    # Google Calendar Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_CALENDAR_ENABLED: bool = os.getenv("GOOGLE_CALENDAR_ENABLED", "true").lower() == "true"
    
    # Default work hours
    DEFAULT_WORK_START: str = os.getenv("DEFAULT_WORK_START", "09:00")
    DEFAULT_WORK_END: str = os.getenv("DEFAULT_WORK_END", "17:00")
    DEFAULT_WORK_DAYS: str = os.getenv("DEFAULT_WORK_DAYS", "Monday,Tuesday,Wednesday,Thursday,Friday")


settings = Settings()