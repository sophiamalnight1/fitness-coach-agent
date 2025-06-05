"""Progress monitoring agent."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage

from fitness_coach.agents.base import BaseAgent
from fitness_coach.core.state import State


class ProgressMonitoringAgent(BaseAgent):
    """Agent for monitoring user progress."""
    
    def process(self, state: State) -> State:
        """Monitor and report on user progress."""
        prompt = ChatPromptTemplate.from_template(
            """You are an AI fitness progress tracker. Review the user's progress and provide encouragement or suggestions:

            User Data: {user_data}
            Current Plan: {current_plan}
            Progress History: {progress_history}

            Provide a summary of the user's progress, offer encouragement, and suggest any new challenges or adjustments."""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        progress_update = chain.invoke({
            "user_data": str(state["user_data"]),
            "current_plan": state["fitness_plan"],
            "progress_history": str(state["progress"])
        })
        
        state["progress"].append(progress_update)
        state["messages"].append(AIMessage(content=f"Progress update: {progress_update}"))
        return state