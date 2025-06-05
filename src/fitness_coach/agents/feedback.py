"""Feedback processing agents."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage

from fitness_coach.agents.base import BaseAgent
from fitness_coach.core.state import State


class FeedbackCollectionAgent(BaseAgent):
    """Agent for collecting and analyzing user feedback."""
    
    def process(self, state: State) -> State:
        """Analyze user feedback."""
        prompt = ChatPromptTemplate.from_template(
            """You are an AI fitness coach assistant. Analyze the following user feedback on their recent workout session:

            Current fitness plan: {current_plan}
            User feedback: {user_feedback}

            Summarize the user's feedback and suggest any immediate adjustments."""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        feedback_summary = chain.invoke({
            "current_plan": state["fitness_plan"],
            "user_feedback": state["feedback"]
        })
        
        state["messages"].append(AIMessage(content=f"Feedback analysis: {feedback_summary}"))
        return state


class RoutineAdjustmentAgent(BaseAgent):
    """Agent for adjusting routines based on feedback."""
    
    def process(self, state: State) -> State:
        """Adjust fitness plan based on feedback."""
        prompt = ChatPromptTemplate.from_template(
            """You are an AI fitness coach. Adjust the current fitness plan based on the user's feedback:

            Current Plan:
            {current_plan}

            User Feedback:
            {feedback}

            Provide an updated weekly fitness plan that addresses the user's feedback while maintaining the overall structure and goals."""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        updated_plan = chain.invoke({
            "current_plan": state["fitness_plan"],
            "feedback": state["feedback"]
        })
        
        state["fitness_plan"] = updated_plan
        state["messages"].append(AIMessage(content=f"Updated fitness plan: {updated_plan}"))
        return state