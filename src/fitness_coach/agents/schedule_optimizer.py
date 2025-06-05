import json
from datetime import datetime, time
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import AIMessage
from typing import Dict, List

from fitness_coach.agents.base import BaseAgent
from fitness_coach.core.state import State


class ScheduleOptimizerAgent(BaseAgent):
    """Optimizes schedule based on calendar availability."""
    
    def process(self, state: State) -> State:
        """Adjust workout timing based on calendar constraints."""
        current_schedule = state.get("current_micro_plan", {})
        user_availability = state.get("user_availability", {})
        
        # TODO: Integrate with Google Calendar API to get real availability
        # For now, use the user_availability from profile
        
        prompt = ChatPromptTemplate.from_template(
            """You are a scheduling optimization expert. Optimize the workout schedule to fit 
            the user's real availability constraints.
            
            Current Weekly Schedule: {current_schedule}
            User Availability: {user_availability}
            
            Optimize the schedule by:
            1. Moving workouts to available time slots
            2. Adjusting workout duration to fit available time
            3. Suggesting alternative workout types if needed
            4. Maintaining training balance and progression
            5. Ensuring adequate rest between intense sessions
            
            If conflicts exist, provide alternative solutions and explain the trade-offs.
            
            Return the optimized schedule with specific timing for each workout."""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        optimized_schedule = chain.invoke({
            "current_schedule": json.dumps(current_schedule),
            "user_availability": json.dumps(user_availability)
        })
        
        # Try to parse as JSON, fallback to text
        try:
            if optimized_schedule.strip().startswith('{'):
                optimized_data = json.loads(optimized_schedule)
                state["current_micro_plan"] = optimized_data
            else:
                # Keep existing schedule but add optimization notes
                if isinstance(current_schedule, dict):
                    current_schedule["optimization_notes"] = optimized_schedule
                    state["current_micro_plan"] = current_schedule
        except json.JSONDecodeError:
            # Add optimization as notes
            if isinstance(current_schedule, dict):
                current_schedule["optimization_notes"] = optimized_schedule
                state["current_micro_plan"] = current_schedule
        
        state["messages"].append(
            AIMessage(content=f"Schedule optimized for your availability:\n\n{optimized_schedule}")
        )
        
        return state