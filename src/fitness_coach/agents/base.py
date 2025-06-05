"""Base agent functionality."""

from abc import ABC, abstractmethod
from typing import Any
from fitness_coach.core.state import State


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, llm: Any):
        """Initialize the agent with an LLM."""
        self.llm = llm
    
    @abstractmethod
    def process(self, state: State) -> State:
        """Process the state and return updated state."""
        pass