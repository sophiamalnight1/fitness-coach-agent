"""Agent implementations for the fitness coach."""

from fitness_coach.agents.user_input import UserInputAgent
from fitness_coach.agents.routine_generation import RoutineGenerationAgent
from fitness_coach.agents.feedback import FeedbackCollectionAgent, RoutineAdjustmentAgent
from fitness_coach.agents.progress import ProgressMonitoringAgent
from fitness_coach.agents.motivation import MotivationalAgent

__all__ = [
    "UserInputAgent",
    "RoutineGenerationAgent",
    "FeedbackCollectionAgent",
    "RoutineAdjustmentAgent",
    "ProgressMonitoringAgent",
    "MotivationalAgent",
]