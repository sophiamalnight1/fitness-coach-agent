"""Graph construction for the fitness coach workflow."""

from langgraph.graph import StateGraph, END
from fitness_coach.core.state import State


def create_fitness_coach_graph(llm):
    """Create enhanced fitness coach workflow with proper routing fix."""
    print("🔗 Creating fitness coach workflow graph...")
    
    workflow = StateGraph(State)
    
    # Initialize all agents with proper imports
    try:
        from fitness_coach.agents.profile_manager import ProfileSetupAgent, ProfileUpdateAgent
        from fitness_coach.agents.macro_planner import MacroPlannerAgent
        from fitness_coach.agents.micro_planner import MicroPlannerAgent
        from fitness_coach.agents.schedule_optimizer import ScheduleOptimizerAgent
        from fitness_coach.agents.feedback_processor import FeedbackProcessorAgent
        
        print("✅ All agents imported successfully")
        
        profile_setup = ProfileSetupAgent(llm)
        profile_update = ProfileUpdateAgent(llm)
        macro_planner = MacroPlannerAgent(llm)
        micro_planner = MicroPlannerAgent(llm)
        schedule_optimizer = ScheduleOptimizerAgent(llm)
        feedback_processor = FeedbackProcessorAgent(llm)
        
        print("✅ All agents initialized successfully")
        
    except ImportError as e:
        print(f"❌ Error importing agents: {e}")
        raise
    
    # Add nodes
    workflow.add_node("profile_setup", profile_setup.process)
    workflow.add_node("profile_update", profile_update.process)
    workflow.add_node("macro_planning", macro_planner.process)
    workflow.add_node("micro_planning", micro_planner.process)
    workflow.add_node("schedule_optimization", schedule_optimizer.process)
    workflow.add_node("feedback_processing", feedback_processor.process)
    
    print("✅ All nodes added to workflow")
    
    # FIXED: Simplified routing function that goes to END after micro_planning
    def route_workflow(state: State) -> str:
        """Route based on workflow stage with proper END handling."""
        stage = state.get("workflow_stage", "profile_setup")
        print(f"🔀 Routing from stage: {stage}")
        
        if stage == "profile_setup":
            return "profile_setup"
        elif stage == "profile_update":
            return "profile_update"
        elif stage == "macro_planning":
            return "macro_planning"
        elif stage == "micro_planning":
            return "micro_planning"
        elif stage == "schedule_optimization":
            return "schedule_optimization"
        elif stage == "feedback":
            return "feedback_processing"
        else:
            print(f"🏁 Ending workflow from stage: {stage}")
            return END
    
    # FIXED: After micro_planning, always go to schedule_optimization, then END
    def route_after_micro_planning(state: State) -> str:
        """Route after micro planning - always go to schedule optimization."""
        print("🔀 Routing after micro_planning -> schedule_optimization")
        return "schedule_optimization"
    
    def route_after_macro_planning(state: State) -> str:
        """Route after macro planning."""
        # Check if we need to go to micro planning or end
        if state.get("workflow_stage") == "micro_planning":
            print("🔀 Routing after macro_planning -> micro_planning")
            return "micro_planning"
        else:
            print("🔀 Routing after macro_planning -> END")
            return END
    
    # Set entry point
    workflow.set_entry_point("profile_setup")
    
    # FIXED: Proper conditional edges with all possible destinations
    workflow.add_conditional_edges(
        "profile_setup",
        route_workflow,
        {
            "profile_setup": "profile_setup",
            "macro_planning": "macro_planning",
            "micro_planning": "micro_planning",
            "schedule_optimization": "schedule_optimization",
            END: END
        }
    )
    
    # FIXED: Route after macro planning
    workflow.add_conditional_edges(
        "macro_planning",
        route_after_macro_planning,
        {
            "micro_planning": "micro_planning",
            END: END
        }
    )
    
    # FIXED: After micro planning, always go to schedule optimization
    workflow.add_conditional_edges(
        "micro_planning",
        route_after_micro_planning,
        {
            "schedule_optimization": "schedule_optimization"
        }
    )
    
    # Simple edges that always go to END
    workflow.add_edge("schedule_optimization", END)
    workflow.add_edge("feedback_processing", "micro_planning")
    workflow.add_edge("profile_update", END)
    
    print("✅ Workflow edges configured")
    
    compiled_graph = workflow.compile()
    print("✅ Workflow compiled successfully")
    
    return compiled_graph
