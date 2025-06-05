import json
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage

from fitness_coach.agents.base import BaseAgent
from fitness_coach.core.state import State


class FeedbackProcessorAgent(BaseAgent):
    """Processes user feedback and adjusts plans."""
    
    def process(self, state: State) -> State:
        """Analyze feedback and suggest schedule modifications."""
        current_schedule = state.get("current_micro_plan", {})
        feedback_history = state.get("feedback_history", [])
        
        # Extract latest feedback from messages
        latest_feedback = ""
        if state.get("messages"):
            for message in reversed(state["messages"]):
                if isinstance(message, HumanMessage):
                    latest_feedback = message.content
                    break
        
        prompt = ChatPromptTemplate.from_template(
            """You are an expert fitness coach analyzing user feedback to improve their workout plan.
            
            Current Schedule: {current_schedule}
            Latest Feedback: {latest_feedback}
            Previous Feedback: {feedback_history}
            
            Analyze the feedback and:
            1. Identify specific issues or concerns
            2. Determine what's working well
            3. Suggest specific modifications to address concerns
            4. Maintain overall training goals and progression
            5. Ensure modifications are realistic and achievable
            
            Categories of feedback to consider:
            - Time constraints (too long/short)
            - Difficulty level (too easy/hard)
            - Exercise preferences (likes/dislikes)
            - Physical discomfort or limitations
            - Schedule conflicts
            - Motivation and enjoyment
            
            Provide:
            1. Summary of feedback analysis
            2. Specific recommended changes
            3. Rationale for each change
            4. Updated schedule if modifications are needed
            
            Be encouraging while addressing concerns constructively."""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        feedback_analysis = chain.invoke({
            "current_schedule": json.dumps(current_schedule),
            "latest_feedback": latest_feedback,
            "feedback_history": json.dumps(feedback_history)
        })
        
        # Store feedback with timestamp
        feedback_entry = {
            "feedback": latest_feedback,
            "analysis": feedback_analysis,
            "timestamp": datetime.now().isoformat(),
            "schedule_version": state.get("active_schedule", {}).get("schedule_id", "unknown")
        }
        
        # Update feedback history
        if not state.get("feedback_history"):
            state["feedback_history"] = []
        state["feedback_history"].append(feedback_entry)
        
        # Save feedback to storage if available
        if state.get("storage") and state.get("active_schedule"):
            schedule_id = state["active_schedule"].get("schedule_id", "unknown")
            state["storage"].save_feedback(schedule_id, feedback_entry)
        
        state["latest_feedback"] = feedback_entry
        state["messages"].append(
            AIMessage(content=f"Feedback analyzed and processed:\n\n{feedback_analysis}")
        )
        
        return state