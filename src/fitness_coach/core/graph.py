"""Graph construction for the fitness coach workflow."""

from langgraph.graph import StateGraph, END

from fitness_coach.core.state import State
from fitness_coach.agents import (
    UserInputAgent,
    RoutineGenerationAgent,
    FeedbackCollectionAgent,
    RoutineAdjustmentAgent,
    ProgressMonitoringAgent,
    MotivationalAgent,
)


def create_fitness_coach_graph(llm):
    """Create the fitness coach workflow graph."""
    workflow = StateGraph(State)
    
    # Initialize agents
    user_input_agent = UserInputAgent(llm)
    routine_generation_agent = RoutineGenerationAgent(llm)
    feedback_collection_agent = FeedbackCollectionAgent(llm)
    routine_adjustment_agent = RoutineAdjustmentAgent(llm)
    progress_monitoring_agent = ProgressMonitoringAgent(llm)
    motivational_agent = MotivationalAgent(llm)
    
    # Define nodes
    workflow.add_node("user_input", user_input_agent.process)
    workflow.add_node("routine_generation", routine_generation_agent.process)
    workflow.add_node("feedback_collection", feedback_collection_agent.process)
    workflow.add_node("routine_adjustment", routine_adjustment_agent.process)
    workflow.add_node("progress_monitoring", progress_monitoring_agent.process)
    workflow.add_node("motivation", motivational_agent.process)
    
    # Define edges
    workflow.add_edge("user_input", "routine_generation")
    workflow.add_edge("routine_generation", "feedback_collection")
    workflow.add_edge("feedback_collection", "routine_adjustment")
    workflow.add_edge("routine_adjustment", "progress_monitoring")
    workflow.add_edge("progress_monitoring", "motivation")
    workflow.add_edge("motivation", END)
    
    # Set entry point
    workflow.set_entry_point("user_input")
    
    return workflow.compile()