"""State definition for the fitness coach workflow."""

from typing import Annotated, TypedDict, List
from langgraph.graph.message import add_messages


class State(TypedDict):
    """State definition for the fitness coach workflow."""
    user_data: dict
    fitness_plan: str
    feedback: str
    progress: List[str]
    messages: Annotated[list, add_messages]