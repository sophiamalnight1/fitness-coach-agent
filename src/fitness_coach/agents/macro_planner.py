import json
from datetime import datetime, timedelta
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage

from fitness_coach.agents.base import BaseAgent
from fitness_coach.core.state import State


class MacroPlannerAgent(BaseAgent):
    """Creates long-term progression plans."""
    
    def process(self, state: State) -> State:
        """Generate 4-12 week macro progression plan."""
        user_profile = state.get("user_profile", {})
        
        prompt = ChatPromptTemplate.from_template(
            """You are an expert fitness coach specializing in periodization and long-term training planning.
            
            Create a comprehensive macro training plan based on this user profile:
            {user_profile}

            Generate a 12 week macro progression plan that includes:
            
            1. **Periodization Structure**: Break down into phases (base building, strength, peak, recovery)
            2. **Weekly Progression**: How intensity, volume, and focus change each week
            3. **Goal Alignment**: Ensure the plan progresses toward their specific goals
            4. **Adaptation Periods**: Include deload weeks and recovery phases
            5. **Milestone Markers**: Key checkpoints to assess progress
            
            Structure your response as a detailed plan with:
            - Overall timeline and phases
            - Week-by-week progression overview
            - Key principles and adaptations
            - Expected outcomes and milestones
            
            Make it specific to their goals, experience level, and timeline."""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        macro_plan = chain.invoke({"user_profile": json.dumps(user_profile)})
        
        state["current_macro_plan"] = macro_plan
        state["messages"].append(
            AIMessage(content=f"Macro training plan created:\n\n{macro_plan}")
        )
        
        return state
