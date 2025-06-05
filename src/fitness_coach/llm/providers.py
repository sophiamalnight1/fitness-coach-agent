"""LLM provider implementations."""

from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from fitness_coach.config.settings import settings


def get_openai_llm():
    """Get OpenAI LLM instance."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
    
    return ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE
    )


def get_ollama_llm(model_name: str = None):
    """Get Ollama LLM instance."""
    model = model_name or settings.OLLAMA_MODEL
    print(f"Creating ChatOllama with model: {model}")
    return ChatOllama(model=model)


def get_llm():
    """Get the configured LLM instance."""
    if settings.USE_OLLAMA:
        return get_ollama_llm()
    return get_openai_llm()