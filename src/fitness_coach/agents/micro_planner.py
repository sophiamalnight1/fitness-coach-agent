import json
from datetime import datetime, timedelta
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import AIMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Dict, List

from fitness_coach.agents.base import BaseAgent
from fitness_coach.core.state import State


class DailyWorkout(BaseModel):
    """Structure for a daily workout."""
    type: str = Field(description="Type of workout (e.g., 'Strength', 'Cardio', 'Yoga', 'Rest')")
    duration: str = Field(description="Duration of workout (e.g., '45 min', '1 hour')")
    focus: str = Field(description="Main focus area (e.g., 'Upper body', 'Endurance', 'Flexibility')")
    intensity: str = Field(description="Intensity level (e.g., 'Low', 'Moderate', 'High')")
    details: str = Field(description="Specific workout details and exercises")
    location: str = Field(description="Where to do the workout (e.g., 'Gym', 'Home', 'Outdoors')")


class WeeklyPlan(BaseModel):
    """Structure for weekly workout plan."""
    Monday: DailyWorkout
    Tuesday: DailyWorkout
    Wednesday: DailyWorkout
    Thursday: DailyWorkout
    Friday: DailyWorkout
    Saturday: DailyWorkout
    Sunday: DailyWorkout


class MicroPlannerAgent(BaseAgent):
    """Creates specific weekly schedules based on availability with improved error handling."""
    
    def process(self, state: State) -> State:
        """Generate specific weekly schedule fitting user's availability."""
        print("🔄 MicroPlannerAgent: Starting process...")
        
        user_profile = state.get("user_profile", {})
        macro_plan = state.get("current_macro_plan", "")
        user_availability = state.get("user_availability", {})
        
        print(f"Debug - User profile exists: {user_profile is not None}")
        print(f"Debug - Macro plan exists: {bool(macro_plan)}")
        print(f"Debug - User availability: {user_availability}")
        
        # Create a simpler prompt that's more likely to succeed
        prompt = ChatPromptTemplate.from_template(
            """You are an expert fitness coach creating a weekly workout schedule.
            
            User Profile: {user_profile}
            Macro Plan Context: {macro_plan}
            User Availability: {user_availability}
            
            Create a weekly workout schedule that fits the user's available time slots.
            
            For each day of the week, provide:
            - type: The type of workout (Strength, Cardio, Yoga, Rest)
            - duration: How long the workout should be
            - focus: What the main focus is
            - intensity: Low, Moderate, or High
            - details: Specific exercises or activities
            - location: Where to do it (Home, Gym, Outdoors)
            
            Return ONLY a JSON object with this exact structure:
            {{
                "Monday": {{"type": "...", "duration": "...", "focus": "...", "intensity": "...", "details": "...", "location": "..."}},
                "Tuesday": {{"type": "...", "duration": "...", "focus": "...", "intensity": "...", "details": "...", "location": "..."}},
                "Wednesday": {{"type": "...", "duration": "...", "focus": "...", "intensity": "...", "details": "...", "location": "..."}},
                "Thursday": {{"type": "...", "duration": "...", "focus": "...", "intensity": "...", "details": "...", "location": "..."}},
                "Friday": {{"type": "...", "duration": "...", "focus": "...", "intensity": "...", "details": "...", "location": "..."}},
                "Saturday": {{"type": "...", "duration": "...", "focus": "...", "intensity": "...", "details": "...", "location": "..."}},
                "Sunday": {{"type": "...", "duration": "...", "focus": "...", "intensity": "...", "details": "...", "location": "..."}}
            }}
            
            For days when the user is not available, use "type": "Rest".
            """
        )
        
        # Use string output parser and manual JSON parsing for better error handling
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            print("Debug - Invoking LLM chain...")
            
            weekly_schedule_response = chain.invoke({
                "user_profile": json.dumps(user_profile) if user_profile else "No profile available",
                "macro_plan": macro_plan or "No macro plan available",
                "user_availability": json.dumps(user_availability) if user_availability else "No availability set"
            })
            
            print(f"Debug - LLM response received: {len(weekly_schedule_response)} characters")
            print(f"Debug - Response preview: {weekly_schedule_response[:200]}...")
            
            # Try to extract JSON from response
            try:
                # Find JSON in the response
                json_start = weekly_schedule_response.find('{')
                json_end = weekly_schedule_response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = weekly_schedule_response[json_start:json_end]
                    weekly_schedule = json.loads(json_str)
                    print("✅ Successfully parsed JSON from LLM response")
                else:
                    raise ValueError("No JSON found in response")
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ JSON parsing failed: {e}")
                print("🔄 Creating fallback schedule...")
                
                # Create a fallback schedule based on availability
                weekly_schedule = self._create_fallback_schedule(user_availability)
            
            # Validate the schedule structure
            weekly_schedule = self._validate_schedule(weekly_schedule)
            
            state["current_micro_plan"] = weekly_schedule
            
            # Create and save schedule object
            schedule_data = {
                "schedule_id": f"week_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "macro_plan": macro_plan,
                "micro_plan": weekly_schedule,
                "user_availability": user_availability,
                "created_at": datetime.now().isoformat(),
                "status": "draft"
            }
            
            print("Debug - About to save schedule to storage...")
            
            # Save to storage if available
            if state.get("storage"):
                schedule_id = state["storage"].save_weekly_schedule(schedule_data)
                print(f"✅ Schedule saved with ID: {schedule_id}")
                
                # Update state with saved schedule
                state["active_schedule"] = schedule_data
            else:
                print("⚠️ No storage available in state")
            
            state["messages"].append(
                AIMessage(content=f"Weekly schedule created successfully:\n\n{json.dumps(weekly_schedule, indent=2)}")
            )
            
            print("✅ MicroPlannerAgent: Process completed successfully")
            
        except Exception as e:
            print(f"❌ Error in MicroPlannerAgent: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Create emergency fallback
            fallback_schedule = self._create_emergency_fallback()
            state["current_micro_plan"] = fallback_schedule
            
            state["messages"].append(
                AIMessage(content=f"Created basic fallback schedule due to error: {str(e)}")
            )
        
        return state
    
    def _create_fallback_schedule(self, user_availability: dict) -> dict:
        """Create a basic schedule based on availability when LLM fails."""
        print("🔄 Creating fallback schedule...")
        
        schedule = {}
        workout_types = ["Strength", "Cardio", "Flexibility"]
        workout_index = 0
        
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            day_avail = user_availability.get(day, {})
            
            if day_avail.get("available", False):
                workout_type = workout_types[workout_index % len(workout_types)]
                workout_index += 1
                
                schedule[day] = {
                    "type": workout_type,
                    "duration": day_avail.get("duration", "45 minutes"),
                    "focus": f"{workout_type} training",
                    "intensity": "Moderate",
                    "details": f"Basic {workout_type.lower()} workout routine",
                    "location": "Home or Gym"
                }
            else:
                schedule[day] = {
                    "type": "Rest",
                    "duration": "N/A",
                    "focus": "Recovery",
                    "intensity": "Rest",
                    "details": "Rest and recovery day",
                    "location": "N/A"
                }
        
        return schedule
    
    def _create_emergency_fallback(self) -> dict:
        """Create an emergency schedule when everything fails."""
        print("🚨 Creating emergency fallback schedule...")
        
        return {
            "Monday": {"type": "Strength", "duration": "45 min", "focus": "Upper body", "intensity": "Moderate", "details": "Basic strength training", "location": "Home"},
            "Tuesday": {"type": "Rest", "duration": "N/A", "focus": "Recovery", "intensity": "Rest", "details": "Rest day", "location": "N/A"},
            "Wednesday": {"type": "Cardio", "duration": "30 min", "focus": "Endurance", "intensity": "Moderate", "details": "Basic cardio workout", "location": "Home"},
            "Thursday": {"type": "Rest", "duration": "N/A", "focus": "Recovery", "intensity": "Rest", "details": "Rest day", "location": "N/A"},
            "Friday": {"type": "Strength", "duration": "45 min", "focus": "Lower body", "intensity": "Moderate", "details": "Basic strength training", "location": "Home"},
            "Saturday": {"type": "Flexibility", "duration": "30 min", "focus": "Mobility", "intensity": "Low", "details": "Stretching and mobility", "location": "Home"},
            "Sunday": {"type": "Rest", "duration": "N/A", "focus": "Recovery", "intensity": "Rest", "details": "Rest day", "location": "N/A"}
        }
    
    def _validate_schedule(self, schedule: dict) -> dict:
        """Validate and fix schedule structure."""
        required_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        required_fields = ["type", "duration", "focus", "intensity", "details", "location"]
        
        validated_schedule = {}
        
        for day in required_days:
            if day in schedule and isinstance(schedule[day], dict):
                day_workout = schedule[day].copy()
                
                # Ensure all required fields exist
                for field in required_fields:
                    if field not in day_workout:
                        day_workout[field] = "N/A"
                
                validated_schedule[day] = day_workout
            else:
                # Create rest day if missing
                validated_schedule[day] = {
                    "type": "Rest",
                    "duration": "N/A",
                    "focus": "Recovery",
                    "intensity": "Rest",
                    "details": "Rest and recovery day",
                    "location": "N/A"
                }
        
        return validated_schedule
    