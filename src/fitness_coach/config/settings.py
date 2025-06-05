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
    
    # Future integrations
    GOOGLE_CALENDAR_ENABLED: bool = os.getenv("GOOGLE_CALENDAR_ENABLED", "false").lower() == "true"
    TERRA_API_KEY: str = os.getenv("TERRA_API_KEY", "")
    TERRA_WEBHOOK_SECRET: str = os.getenv("TERRA_WEBHOOK_SECRET", "")


settings = Settings()