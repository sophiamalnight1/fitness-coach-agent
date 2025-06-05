"""Enhanced state definition with storage integration."""

from typing import Annotated, TypedDict, List, Optional, Dict
from langgraph.graph.message import add_messages
from datetime import datetime


class State(TypedDict):
    """Enhanced state for fitness coach workflow."""
    # User data
    user_profile: Optional[Dict]
    user_id: Optional[str]
    
    # Planning data
    current_macro_plan: Optional[str]
    current_micro_plan: Optional[Dict]
    user_availability: Optional[Dict]
    
    # Schedule management
    active_schedule: Optional[Dict]
    schedule_history: List[Dict]
    
    # Feedback and interaction
    latest_feedback: Optional[Dict]
    feedback_history: List[Dict]
    
    # Workflow control
    workflow_stage: str  # "profile_setup", "macro_planning", "micro_planning", "feedback", "active"
    messages: Annotated[list, add_messages]
    
    # Storage instance (not serialized)
    storage: Optional[object]