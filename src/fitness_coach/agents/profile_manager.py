import json
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage

from fitness_coach.agents.base import BaseAgent
from fitness_coach.core.state import State


class ProfileSetupAgent(BaseAgent):
    """Handles user profile creation and updates."""
    
    def process(self, state: State) -> State:
        """Create or update user profile with detailed preferences."""
        prompt = ChatPromptTemplate.from_template(
            """You are an AI fitness coach assistant. Process and structure the following user information 
            into a comprehensive fitness profile:

            User Input: {user_input}

            Create a detailed user profile that includes:
            1. Personal information (age, weight, height, gender)
            2. Fitness history and experience level
            3. Specific goals with timelines
            4. Workout preferences and dislikes
            5. Any health conditions or restrictions
            6. Available time and schedule preferences

            Return the profile as a well-structured JSON object."""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        # Get user input from messages or user_profile
        user_input = state.get("user_profile", {})
        if state.get("messages"):
            latest_message = state["messages"][-1]
            if hasattr(latest_message, 'content'):
                try:
                    user_input.update(json.loads(latest_message.content))
                except (json.JSONDecodeError, TypeError):
                    pass
        
        profile_response = chain.invoke({"user_input": json.dumps(user_input)})
        
        try:
            structured_profile = json.loads(profile_response)
            state["user_profile"] = structured_profile
            
            # Save to storage if available
            if state.get("storage"):
                state["storage"].save_user_profile(structured_profile)
                
        except json.JSONDecodeError:
            # If JSON parsing fails, keep the raw response
            state["user_profile"] = {"raw_profile": profile_response}
        
        state["messages"].append(
            AIMessage(content=f"Profile processed and saved: {json.dumps(state['user_profile'], indent=2)}")
        )
        
        return state


class ProfileUpdateAgent(BaseAgent):
    """Updates existing profile with new preferences."""
    
    def process(self, state: State) -> State:
        """Update specific aspects of user profile."""
        existing_profile = state.get("user_profile", {})
        
        prompt = ChatPromptTemplate.from_template(
            """You are an AI fitness coach assistant. Update the existing user profile with new information:

            Existing Profile: {existing_profile}
            New Information: {new_info}

            Merge the new information with the existing profile, updating any changed fields
            and adding any new information. Keep all existing data that isn't being changed.
            
            Return the updated profile as a JSON object."""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        # Get new information from latest message
        new_info = {}
        if state.get("messages"):
            latest_message = state["messages"][-1]
            if hasattr(latest_message, 'content'):
                try:
                    new_info = json.loads(latest_message.content)
                except (json.JSONDecodeError, TypeError):
                    new_info = {"feedback": latest_message.content}
        
        updated_profile_response = chain.invoke({
            "existing_profile": json.dumps(existing_profile),
            "new_info": json.dumps(new_info)
        })
        
        try:
            updated_profile = json.loads(updated_profile_response)
            state["user_profile"] = updated_profile
            
            # Save to storage if available
            if state.get("storage"):
                state["storage"].save_user_profile(updated_profile)
                
        except json.JSONDecodeError:
            # If parsing fails, merge manually
            existing_profile.update(new_info)
            state["user_profile"] = existing_profile
        
        state["messages"].append(
            AIMessage(content=f"Profile updated successfully: {json.dumps(state['user_profile'], indent=2)}")
        )
        
        return state