"""Routine generation agent."""

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage

from fitness_coach.agents.base import BaseAgent
from fitness_coach.core.state import State


class RoutineGenerationAgent(BaseAgent):
    """Agent for generating fitness routines."""
    
    def process(self, state: State) -> State:
        """Generate personalized fitness routine."""
        prompt = ChatPromptTemplate.from_template(
            """You are an AI fitness coach. Create a personalized fitness routine based on the following user data:

            {user_data}

            Create a detailed weekly fitness plan that includes:
            1. Types of exercises
            2. Duration and frequency of workouts
            3. Intensity levels
            4. Rest days
            5. Any dietary recommendations

            Present the plan in a clear, structured format."""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        plan = chain.invoke({"user_data": json.dumps(state["user_data"])})
        
        state["fitness_plan"] = plan
        state["messages"].append(AIMessage(content=f"Generated fitness plan: {plan}"))
        return state