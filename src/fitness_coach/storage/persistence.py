# Complete src/fitness_coach/storage/persistence.py with ALL methods

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import hashlib


class FitnessCoachStorage:
    """Complete storage with all required methods."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize storage with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.data_dir / "profiles").mkdir(exist_ok=True)
        (self.data_dir / "schedules").mkdir(exist_ok=True)
        (self.data_dir / "macro_plans").mkdir(exist_ok=True)
        (self.data_dir / "feedback").mkdir(exist_ok=True)
    
    def _get_user_id(self) -> str:
        """Get or create a unique user ID for this browser session."""
        user_file = self.data_dir / "current_user.txt"
        
        if user_file.exists():
            with open(user_file, 'r') as f:
                return f.read().strip()
        else:
            # Generate new user ID
            user_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
            with open(user_file, 'w') as f:
                f.write(user_id)
            return user_id
    
    def save_user_profile(self, profile: Dict) -> str:
        """Save user profile and return user_id."""
        user_id = self._get_user_id()
        profile_file = self.data_dir / "profiles" / f"profile_{user_id}.json"
        
        # Add metadata
        profile_data = {
            "user_id": user_id,
            "profile": profile,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f, indent=2, default=str)
        
        print(f"✅ Profile saved for user {user_id}")
        return user_id
    
    def load_user_profile(self) -> Optional[Dict]:
        """Load user profile for current user."""
        user_id = self._get_user_id()
        profile_file = self.data_dir / "profiles" / f"profile_{user_id}.json"
        
        if profile_file.exists():
            with open(profile_file, 'r') as f:
                data = json.load(f)
                print(f"✅ Profile loaded for user {user_id}")
                return data.get("profile", {})
        
        print(f"ℹ️ No profile found for user {user_id}")
        return None
    
    def save_macro_plan(self, macro_plan: str) -> str:
        """Save macro plan and return plan_id."""
        user_id = self._get_user_id()
        plan_id = f"macro_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        macro_data = {
            "user_id": user_id,
            "plan_id": plan_id,
            "macro_plan": macro_plan,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Deactivate old macro plans
        for file in (self.data_dir / "macro_plans").glob(f"macro_{user_id}_*.json"):
            with open(file, 'r') as f:
                data = json.load(f)
            data["status"] = "inactive"
            with open(file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        # Save new macro plan
        macro_file = self.data_dir / "macro_plans" / f"macro_{user_id}_{plan_id}.json"
        with open(macro_file, 'w') as f:
            json.dump(macro_data, f, indent=2, default=str)
        
        print(f"✅ Macro plan saved: {plan_id}")
        return plan_id
    
    def get_active_macro_plan(self) -> Optional[Dict]:
        """Get the currently active macro plan."""
        user_id = self._get_user_id()
        
        for file in (self.data_dir / "macro_plans").glob(f"macro_{user_id}_*.json"):
            with open(file, 'r') as f:
                data = json.load(f)
            if data.get("status") == "active":
                return data
        
        return None
    
    def save_weekly_schedule(self, schedule: Dict) -> str:
        """Enhanced weekly schedule saving with macro plan reference."""
        user_id = self._get_user_id()
        
        # Generate schedule ID if not provided
        if "schedule_id" not in schedule:
            schedule["schedule_id"] = f"week_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get active macro plan
        macro_plan = self.get_active_macro_plan()
        if macro_plan:
            schedule["macro_plan_id"] = macro_plan["plan_id"]
            schedule["macro_plan"] = macro_plan["macro_plan"]
        
        schedule_file = self.data_dir / "schedules" / f"schedule_{user_id}_{schedule['schedule_id']}.json"
        
        # Add metadata
        schedule_data = {
            "user_id": user_id,
            "schedule": schedule,
            "created_at": datetime.now().isoformat(),
            "status": schedule.get("status", "draft")
        }
        
        with open(schedule_file, 'w') as f:
            json.dump(schedule_data, f, indent=2, default=str)
        
        print(f"✅ Schedule saved: {schedule['schedule_id']}")
        
        # Clean up old schedules (keep only last 4 weeks)
        self._cleanup_old_schedules()
        
        return schedule["schedule_id"]
    
    def load_all_schedules(self) -> List[Dict]:
        """Load all schedules for current user."""
        user_id = self._get_user_id()
        schedules = []
        
        schedule_pattern = f"schedule_{user_id}_*.json"
        for file in (self.data_dir / "schedules").glob(schedule_pattern):
            with open(file, 'r') as f:
                data = json.load(f)
                schedules.append(data)
        
        # Sort by creation date (newest first)
        schedules.sort(key=lambda x: x["created_at"], reverse=True)
        print(f"✅ Loaded {len(schedules)} schedules for user {user_id}")
        return schedules
    
    def get_active_schedule(self) -> Optional[Dict]:
        """Get the currently active schedule with macro plan."""
        user_id = self._get_user_id()
        schedules = []
        
        schedule_pattern = f"schedule_{user_id}_*.json"
        for file in (self.data_dir / "schedules").glob(schedule_pattern):
            with open(file, 'r') as f:
                data = json.load(f)
                schedules.append(data)
        
        # Sort by creation date (newest first)
        schedules.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Return the most recent active schedule, or just the most recent
        for schedule_data in schedules:
            if schedule_data.get("status") == "active":
                return schedule_data["schedule"]
        
        # If no active schedule, return the most recent one
        if schedules:
            return schedules[0]["schedule"]
        
        return None
    
    def set_schedule_active(self, schedule_id: str):
        """Mark a specific schedule as active."""
        user_id = self._get_user_id()
        
        # First, deactivate all schedules
        for file in (self.data_dir / "schedules").glob(f"schedule_{user_id}_*.json"):
            with open(file, 'r') as f:
                data = json.load(f)
            data["status"] = "inactive"
            with open(file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        # Then activate the specified schedule
        schedule_file = self.data_dir / "schedules" / f"schedule_{user_id}_{schedule_id}.json"
        if schedule_file.exists():
            with open(schedule_file, 'r') as f:
                data = json.load(f)
            data["status"] = "active"
            with open(schedule_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"✅ Schedule {schedule_id} set as active")
    
    def get_recent_schedules(self, limit: int = 4) -> List[Dict]:
        """Get the most recent schedules (last 4 weeks)."""
        user_id = self._get_user_id()
        schedules = []
        
        schedule_pattern = f"schedule_{user_id}_*.json"
        for file in (self.data_dir / "schedules").glob(schedule_pattern):
            with open(file, 'r') as f:
                data = json.load(f)
                schedules.append(data)
        
        # Sort by creation date (newest first) and limit
        schedules.sort(key=lambda x: x["created_at"], reverse=True)
        return schedules[:limit]
    
    def _cleanup_old_schedules(self):
        """Keep only the last 4 weekly schedules."""
        user_id = self._get_user_id()
        schedule_files = list((self.data_dir / "schedules").glob(f"schedule_{user_id}_*.json"))
        
        # Sort by creation date
        schedule_data = []
        for file in schedule_files:
            with open(file, 'r') as f:
                data = json.load(f)
                data["file_path"] = file
                schedule_data.append(data)
        
        schedule_data.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Keep only the 4 most recent, delete the rest
        for old_schedule in schedule_data[4:]:
            old_schedule["file_path"].unlink()
            print(f"🗑️ Cleaned up old schedule: {old_schedule['schedule']['schedule_id']}")
    
    def save_feedback(self, schedule_id: str, feedback: Dict):
        """Save user feedback for a specific schedule."""
        user_id = self._get_user_id()
        
        feedback_data = {
            "user_id": user_id,
            "schedule_id": schedule_id,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        feedback_file = self.data_dir / "feedback" / f"feedback_{user_id}_{schedule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(feedback_file, 'w') as f:
            json.dump(feedback_data, f, indent=2, default=str)
        
        print(f"✅ Feedback saved for schedule {schedule_id}")
    
    def get_user_stats(self) -> Dict:
        """Get basic stats about user's data."""
        user_id = self._get_user_id()
        
        profile_exists = (self.data_dir / "profiles" / f"profile_{user_id}.json").exists()
        num_schedules = len(list((self.data_dir / "schedules").glob(f"schedule_{user_id}_*.json")))
        num_feedback = len(list((self.data_dir / "feedback").glob(f"feedback_{user_id}_*.json")))
        
        return {
            "user_id": user_id,
            "has_profile": profile_exists,
            "total_schedules": num_schedules,
            "total_feedback": num_feedback
        }
    
    def save_calendar_preferences(self, preferences: Dict) -> str:
        """Save calendar and work hour preferences."""
        user_id = self._get_user_id()
        prefs_file = self.data_dir / "profiles" / f"calendar_prefs_{user_id}.json"
        
        prefs_data = {
            "user_id": user_id,
            "preferences": preferences,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        with open(prefs_file, 'w') as f:
            json.dump(prefs_data, f, indent=2, default=str)
        
        print(f"✅ Calendar preferences saved for user {user_id}")
        return user_id

    def load_calendar_preferences(self) -> Optional[Dict]:
        """Load calendar and work hour preferences."""
        user_id = self._get_user_id()
        prefs_file = self.data_dir / "profiles" / f"calendar_prefs_{user_id}.json"
        
        if prefs_file.exists():
            with open(prefs_file, 'r') as f:
                data = json.load(f)
                print(f"✅ Calendar preferences loaded for user {user_id}")
                return data.get("preferences", {})
        
        print(f"ℹ️ No calendar preferences found for user {user_id}")
        return None