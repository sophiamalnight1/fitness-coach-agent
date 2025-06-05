"""Motivational agent."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage

from fitness_coach.agents.base import BaseAgent
from fitness_coach.core.state import State


class MotivationalAgent(BaseAgent):
    """Agent for providing motivation and encouragement."""
    
    def process(self, state: State) -> State:
        """Generate motivational message."""
        prompt = ChatPromptTemplate.from_template(
            """You are an AI motivational coach for fitness. Provide encouragement, tips, or reminders to the user:

            User Data: {user_data}
            Current Plan: {current_plan}
            Recent Progress: {recent_progress}

            Generate a motivational message, helpful tip, or reminder to keep the user engaged and committed to their fitness goals."""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        motivation = chain.invoke({
            "user_data": str(state["user_data"]),
            "current_plan": state["fitness_plan"],
            "recent_progress": state["progress"][-1] if state["progress"] else ""
        })
        
        state["messages"].append(AIMessage(content=f"Motivation: {motivation}"))
        return state