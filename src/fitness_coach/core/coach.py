"""Main AIFitnessCoach class."""

import json
from langchain_core.messages import HumanMessage

from fitness_coach.core.state import State
from fitness_coach.core.graph import create_fitness_coach_graph
from fitness_coach.llm.providers import get_llm


class AIFitnessCoach:
    """Main AI Fitness Coach class."""
    
    def __init__(self):
        """Initialize the AI Fitness Coach."""
        print("Initializing AIFitnessCoach")
        self.llm = get_llm()
        self.graph = create_fitness_coach_graph(self.llm)
        print("AIFitnessCoach initialized")
    
    def run(self, user_input: dict) -> list:
        """Run the fitness coach workflow."""
        print("Running AIFitnessCoach")
        
        initial_state = State(
            user_data=user_input,
            fitness_plan="",
            feedback=user_input.get("feedback", ""),
            progress=[],
            messages=[HumanMessage(content=json.dumps(user_input))]
        )
        
        print(f"Initial state: {initial_state}")
        final_state = self.graph.invoke(initial_state)
        print(f"Final state: {final_state}")
        
        return final_state["messages"]