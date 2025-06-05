"""Enhanced AIFitnessCoach with persistent storage."""

from datetime import datetime
import json
from typing import Dict, List, Optional
from langchain_core.messages import HumanMessage

from fitness_coach.core.state import State
from fitness_coach.core.graph import create_fitness_coach_graph
from fitness_coach.llm.providers import get_llm
from fitness_coach.storage.persistence import FitnessCoachStorage


class AIFitnessCoach:
    """Complete AI Fitness Coach with all required methods."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the AI Fitness Coach with storage."""
        print("🚀 Initializing AIFitnessCoach with persistent storage...")
        
        # Initialize storage
        self.storage = FitnessCoachStorage(data_dir)
        
        # Initialize LLM and graph
        self.llm = get_llm()
        self.graph = create_fitness_coach_graph(self.llm)
        
        print("✅ AIFitnessCoach initialized successfully")
    
    def get_initial_state(self) -> State:
        """Get initial state with loaded user data."""
        # Load existing user profile
        user_profile = self.storage.load_user_profile()
        
        # Load macro plan
        macro_plan = self.storage.get_active_macro_plan()
        
        # Load schedule history
        schedule_history = self.storage.load_all_schedules()
        
        # Get active schedule
        active_schedule = self.storage.get_active_schedule()
        
        # Determine workflow stage
        if user_profile is None:
            workflow_stage = "profile_setup"
        elif macro_plan is None:
            workflow_stage = "macro_planning"
        elif active_schedule is None:
            workflow_stage = "micro_planning"
        else:
            workflow_stage = "active"
        
        return State(
            user_profile=user_profile,
            user_id=self.storage._get_user_id(),
            current_macro_plan=macro_plan.get("macro_plan") if macro_plan else None,
            current_micro_plan=active_schedule.get("micro_plan") if active_schedule else None,
            user_availability=None,
            active_schedule=active_schedule,
            schedule_history=[item["schedule"] for item in schedule_history],
            latest_feedback=None,
            feedback_history=[],
            workflow_stage=workflow_stage,
            messages=[],
            storage=self.storage
        )
    
    def get_user_stats(self) -> Dict:
        """Get user statistics - MISSING METHOD FIXED."""
        return self.storage.get_user_stats()
    
    def save_profile(self, profile_data: dict) -> str:
        """Save user profile and return user_id."""
        return self.storage.save_user_profile(profile_data)
    
    def save_schedule(self, schedule_data: dict) -> str:
        """Save schedule and return schedule_id."""
        return self.storage.save_weekly_schedule(schedule_data)
    
    def activate_schedule(self, schedule_id: str):
        """Set a schedule as active."""
        self.storage.set_schedule_active(schedule_id)
    
    def save_feedback(self, schedule_id: str, feedback_data: dict):
        """Save user feedback."""
        self.storage.save_feedback(schedule_id, feedback_data)
    
    def create_macro_plan(self, user_profile: dict) -> str:
        """Create a new macro plan."""
        print("🎯 Creating macro plan...")
        
        initial_state = self.get_initial_state()
        initial_state["workflow_stage"] = "macro_planning"
        initial_state["user_profile"] = user_profile
        
        # Run macro planning
        final_state = self.graph.invoke(initial_state)
        
        # Extract and save macro plan
        macro_plan = final_state.get("current_macro_plan", "")
        if macro_plan:
            plan_id = self.storage.save_macro_plan(macro_plan)
            print(f"✅ Macro plan created: {plan_id}")
            return macro_plan
        
        return "Failed to create macro plan"
    
    def create_weekly_schedule(self, availability: dict, preferences: dict = None) -> dict:
        """Create a weekly schedule based on availability and macro plan with debugging."""
        print("📅 Creating weekly schedule...")
        print(f"Debug - Availability: {availability}")
        print(f"Debug - Preferences: {preferences}")
        
        try:
            initial_state = self.get_initial_state()
            print(f"Debug - Initial state workflow stage: {initial_state['workflow_stage']}")
            print(f"Debug - Has macro plan: {initial_state.get('current_macro_plan') is not None}")
            
            initial_state["workflow_stage"] = "micro_planning"
            initial_state["user_availability"] = availability
            
            # Add preferences to the message
            schedule_input = {
                "action": "create_weekly_schedule",
                "availability": availability,
                "preferences": preferences or {}
            }
            
            print(f"Debug - Schedule input: {schedule_input}")
            
            initial_state["messages"].append(
                HumanMessage(content=json.dumps(schedule_input))
            )
            
            print("Debug - About to invoke graph...")
            
            # Run micro planning
            final_state = self.graph.invoke(initial_state)
            
            print("Debug - Graph invocation completed")
            print(f"Debug - Final state keys: {list(final_state.keys())}")
            print(f"Debug - Current micro plan: {final_state.get('current_micro_plan')}")
            
            # Get the created schedule
            print("Debug - Retrieving active schedule...")
            active_schedule = self.storage.get_active_schedule()
            print(f"Debug - Retrieved schedule: {active_schedule is not None}")
            
            if active_schedule:
                print(f"✅ Weekly schedule created: {active_schedule.get('schedule_id')}")
                return active_schedule
            else:
                print("❌ No active schedule found after creation")
                
                # Try to manually create schedule from final state
                if final_state.get("current_micro_plan"):
                    print("Debug - Attempting manual schedule creation from final state")
                    manual_schedule = {
                        "schedule_id": f"week_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "micro_plan": final_state["current_micro_plan"],
                        "user_availability": availability,
                        "preferences": preferences,
                        "status": "draft"
                    }
                    
                    # Save manually
                    schedule_id = self.storage.save_weekly_schedule(manual_schedule)
                    return manual_schedule
            
            return {}
            
        except Exception as e:
            print(f"❌ Error in create_weekly_schedule: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_macro_plan(self) -> Optional[Dict]:
        """Get current macro plan."""
        return self.storage.get_active_macro_plan()
    
    def get_recent_schedules(self) -> List[Dict]:
        """Get recent weekly schedules."""
        return self.storage.get_recent_schedules()
    
    def run_workflow(self, user_input: dict) -> list:
        """Run the fitness coach workflow with current state."""
        print("🏃‍♂️ Running AIFitnessCoach workflow...")
        
        # Get current state
        current_state = self.get_initial_state()
        
        # Add user input to state
        if user_input:
            current_state["messages"].append(HumanMessage(content=json.dumps(user_input)))
        
        print(f"📊 Current workflow stage: {current_state['workflow_stage']}")
        
        # Run the graph
        final_state = self.graph.invoke(current_state)
        
        print("✅ Workflow completed")
        return final_state["messages"]