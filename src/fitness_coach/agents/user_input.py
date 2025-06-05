"""User input processing agent."""

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage

from fitness_coach.agents.base import BaseAgent
from fitness_coach.core.state import State


class UserInputAgent(BaseAgent):
    """Agent for processing user input."""
    
    def process(self, state: State) -> State:
        """Process user input and create structured profile."""
        prompt = ChatPromptTemplate.from_template(
            """You are an AI fitness coach assistant. Process the following user information:

            {user_input}

            Create a structured user profile based on this information. Include all relevant details for creating a personalized fitness plan.
            Return the profile as a valid JSON string."""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        user_profile = chain.invoke({"user_input": json.dumps(state["user_data"])})
        
        try:
            state["user_data"] = json.loads(user_profile)
        except json.JSONDecodeError:
            pass
        
        state["messages"].append(
            AIMessage(content=f"Processed user profile: {json.dumps(state['user_data'], indent=2)}")
        )
        return state