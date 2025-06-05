"""Enhanced Streamlit UI with persistent storage."""

import streamlit as st
from datetime import datetime
from fitness_coach.core.coach import AIFitnessCoach
from fitness_coach.config.settings import settings
from langgraph.graph import StateGraph, END


def initialize_app():
    """Initialize the app with persistent storage and proper session state."""
    
    # Initialize fitness coach first
    if "fitness_coach" not in st.session_state:
        try:
            st.session_state.fitness_coach = AIFitnessCoach()
            print("✅ Fitness coach initialized")
        except Exception as e:
            st.error(f"Error initializing AI Fitness Coach: {str(e)}")
            st.stop()
    
    # Initialize user stats
    if "user_stats" not in st.session_state:
        try:
            st.session_state.user_stats = st.session_state.fitness_coach.get_user_stats()
            print(f"✅ User stats loaded: {st.session_state.user_stats}")
        except Exception as e:
            st.error(f"Error loading user stats: {str(e)}")
            st.session_state.user_stats = {
                "user_id": "unknown",
                "has_profile": False,
                "total_schedules": 0,
                "total_feedback": 0
            }
    
    # Initialize user profile
    if "user_profile" not in st.session_state:
        try:
            # Try to load existing profile
            initial_state = st.session_state.fitness_coach.get_initial_state()
            st.session_state.user_profile = initial_state.get("user_profile")
            print(f"✅ User profile loaded: {'exists' if st.session_state.user_profile else 'none'}")
        except Exception as e:
            st.error(f"Error loading user profile: {str(e)}")
            st.session_state.user_profile = None
    
    # Initialize active schedule
    if "active_schedule" not in st.session_state:
        try:
            active_schedule = st.session_state.fitness_coach.storage.get_active_schedule()
            st.session_state.active_schedule = active_schedule
            print(f"✅ Active schedule loaded: {'exists' if active_schedule else 'none'}")
        except Exception as e:
            st.error(f"Error loading active schedule: {str(e)}")
            st.session_state.active_schedule = None
    
    # Initialize schedule history
    if "schedule_history" not in st.session_state:
        try:
            all_schedules = st.session_state.fitness_coach.storage.load_all_schedules()
            st.session_state.schedule_history = [item.get("schedule", {}) for item in all_schedules]
            print(f"✅ Schedule history loaded: {len(st.session_state.schedule_history)} schedules")
        except Exception as e:
            st.error(f"Error loading schedule history: {str(e)}")
            st.session_state.schedule_history = []
    
    # Initialize other session state variables
    if "current_macro_plan" not in st.session_state:
        st.session_state.current_macro_plan = None
    
    if "updating_profile" not in st.session_state:
        st.session_state.updating_profile = False

    # Initialize macro plan feedback state
    if "newly_created_macro_plan" not in st.session_state:
        st.session_state.newly_created_macro_plan = None
    
    if "reference_week_index" not in st.session_state:
        st.session_state.reference_week_index = None


def render_profile_setup():
    """Enhanced profile setup with persistence and safe None handling."""
    st.header("🏋️‍♂️ Your Fitness Profile")
    
    # Show current status - safely handle None
    if st.session_state.user_profile is not None:
        st.success(f"✅ Profile exists for user: {st.session_state.user_stats['user_id']}")
        with st.expander("Current Profile Summary"):
            st.json(st.session_state.user_profile)
        
        if st.button("Update Profile"):
            st.session_state.updating_profile = True
            st.rerun()
    else:
        st.info("👋 Welcome! Let's create your fitness profile.")
    
    # Profile form (show if no profile or updating)
    if st.session_state.user_profile is None or st.session_state.get("updating_profile", False):
        
        # Use existing profile data as defaults - safely handle None
        existing = st.session_state.user_profile or {}
        existing_personal = existing.get("personal_info", {})
        existing_prefs = existing.get("preferences", {})
        
        # Personal Information
        with st.expander("Personal Information", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Age", value=existing_personal.get("age", 25), min_value=16, max_value=100)
                weight = st.number_input("Weight (kg)", value=existing_personal.get("weight", 70.0), min_value=30.0, max_value=200.0)
            with col2:
                height = st.number_input("Height (cm)", value=existing_personal.get("height", 170.0), min_value=100.0, max_value=250.0)
                
                # Safely get gender with fallback
                current_gender = existing_personal.get("gender", "Male")
                gender_options = ["Male", "Female", "Other"]
                try:
                    gender_index = gender_options.index(current_gender)
                except ValueError:
                    gender_index = 0
                gender = st.selectbox("Gender", gender_options, index=gender_index)
        
        # Fitness History & Goals
        with st.expander("Fitness History & Goals", expanded=True):
            fitness_history = st.text_area(
                "Tell me about your fitness journey",
                value=existing.get("fitness_history", ""),
                placeholder="e.g., Never been a runner but want to complete a 10km race in 6 months...",
                height=100
            )
            
            primary_goal = st.text_input(
                "Primary Goal (be specific)",
                value=existing.get("primary_goal", ""),
                placeholder="e.g., Run 10km while maintaining current strength"
            )
            
            # Safely get timeline
            current_timeline = existing.get("timeline", "6 months")
            timeline_options = ["3 months", "6 months", "1 year", "Ongoing"]
            try:
                timeline_index = timeline_options.index(current_timeline)
            except ValueError:
                timeline_index = 1  # Default to "6 months"
            timeline = st.selectbox("Timeline", timeline_options, index=timeline_index)
        
        # Detailed Preferences
        with st.expander("Workout Preferences", expanded=True):
            cardio_prefs = st.text_area(
                "Cardio Preferences",
                value=existing_prefs.get("cardio", ""),
                placeholder="e.g., No running initially, love cycling, want to build up to running"
            )
            
            strength_prefs = st.text_area(
                "Strength Training Preferences", 
                value=existing_prefs.get("strength", ""),
                placeholder="e.g., Prefer push/pull/legs split, have access to home gym"
            )
            
            flexibility_prefs = st.text_area(
                "Flexibility/Recovery Preferences",
                value=existing_prefs.get("flexibility", ""),
                placeholder="e.g., Love yin yoga, need help with hip mobility"
            )
            
            dislikes = st.text_area(
                "What you want to avoid",
                value=existing_prefs.get("dislikes", ""),
                placeholder="e.g., No HIIT classes, don't like swimming"
            )
        
        # Save Profile Button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Profile", type="primary"):
                # Create comprehensive profile
                profile_data = {
                    "personal_info": {
                        "age": age,
                        "weight": weight,
                        "height": height,
                        "gender": gender
                    },
                    "fitness_history": fitness_history,
                    "primary_goal": primary_goal,
                    "timeline": timeline,
                    "preferences": {
                        "cardio": cardio_prefs,
                        "strength": strength_prefs,
                        "flexibility": flexibility_prefs,
                        "dislikes": dislikes
                    }
                }
                
                try:
                    # Save to storage
                    user_id = st.session_state.fitness_coach.save_profile(profile_data)
                    
                    # Update session state
                    st.session_state.user_profile = profile_data
                    st.session_state.user_stats = st.session_state.fitness_coach.get_user_stats()
                    st.session_state.updating_profile = False
                    
                    st.success(f"✅ Profile saved successfully! User ID: {user_id}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error saving profile: {str(e)}")
        
        with col2:
            if st.session_state.get("updating_profile", False):
                if st.button("Cancel Update"):
                    st.session_state.updating_profile = False
                    st.rerun()


def render_current_schedule():
    """Enhanced current schedule display with macro and micro plans."""
    st.header("📅 Current Week's Schedule")
    
    if not st.session_state.active_schedule:
        st.info("No active schedule found. Create a new weekly schedule first!")
        
        # Show macro plan if it exists
        macro_plan = st.session_state.fitness_coach.get_macro_plan()
        if macro_plan:
            with st.expander("📈 Your Macro Plan", expanded=True):
                st.write(macro_plan["macro_plan"])
                st.caption(f"Created: {macro_plan['created_at'][:10]}")
        
        return
    
    schedule = st.session_state.active_schedule
    
    # Display schedule header
    st.subheader(f"Week: {schedule.get('schedule_id', 'Unknown')}")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"Created: {schedule.get('created_at', 'Unknown')[:10]}")
    with col2:
        if st.button("🔄 Create New Week"):
            st.switch_page("Create New Schedule")  # Switch to creation tab
    
    # Display macro plan context
    if schedule.get("macro_plan"):
        with st.expander("📈 Macro Plan Context", expanded=True):
            st.write(schedule["macro_plan"])
            if schedule.get("macro_plan_id"):
                st.caption(f"Plan ID: {schedule['macro_plan_id']}")
    
    # Display weekly schedule
    if schedule.get("micro_plan"):
        st.subheader("🗓️ This Week's Workouts")
        
        for day, workout in schedule["micro_plan"].items():
            # Color code based on workout type
            if workout.get("type") == "Rest":
                icon = "🛌"
                color = "gray"
            elif "Cardio" in workout.get("type", ""):
                icon = "🏃‍♂️"
                color = "blue"
            elif "Strength" in workout.get("type", ""):
                icon = "💪"
                color = "red"
            elif "Yoga" in workout.get("type", "") or "Flexibility" in workout.get("type", ""):
                icon = "🧘‍♀️"
                color = "green"
            else:
                icon = "🏋️‍♂️"
                color = "orange"
            
            with st.expander(f"{icon} {day} - {workout.get('type', 'Rest')}", expanded=False):
                if workout.get("type") != "Rest":
                    # Workout details
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**⏰ Duration:** {workout.get('duration', 'N/A')}")
                        st.write(f"**🎯 Focus:** {workout.get('focus', 'N/A')}")
                    with col2:
                        st.write(f"**📍 Location:** {workout.get('location', 'Flexible')}")
                        st.write(f"**💪 Intensity:** {workout.get('intensity', 'Moderate')}")
                    
                    st.write(f"**📝 Details:**")
                    st.write(workout.get('details', 'No details provided'))
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"📅 Add to Calendar", key=f"cal_{day}"):
                            # TODO: Add Google Calendar integration
                            st.success(f"✅ {day}'s workout added to calendar!")
                    with col2:
                        if st.button(f"✅ Mark Complete", key=f"complete_{day}"):
                            st.success(f"✅ {day}'s workout completed!")
                    with col3:
                        if st.button(f"💬 Feedback", key=f"feedback_{day}"):
                            st.info("Feedback feature coming soon!")
                else:
                    st.write("🛌 Rest and recovery day - take care of your body!")
    
    # Show recent schedules summary
    st.subheader("📚 Recent Weeks")
    recent_schedules = st.session_state.fitness_coach.get_recent_schedules()
    
    if len(recent_schedules) > 1:
        for i, schedule_data in enumerate(recent_schedules[1:], 1):  # Skip current week
            schedule_info = schedule_data["schedule"]
            with st.expander(f"Week {i+1} ago - {schedule_info.get('schedule_id', 'Unknown')}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Created:** {schedule_data['created_at'][:10]}")
                    st.write(f"**Status:** {schedule_data.get('status', 'Unknown')}")
                with col2:
                    if st.button(f"🔄 Reactivate", key=f"reactivate_recent_{i}"):
                        st.session_state.fitness_coach.activate_schedule(schedule_info["schedule_id"])
                        st.session_state.active_schedule = schedule_info
                        st.success("✅ Schedule reactivated!")
                        st.rerun()


def render_schedule_history():
    """Display schedule history."""
    st.header("📚 Schedule History")
    
    if not st.session_state.schedule_history:
        st.info("No schedule history found.")
        return
    
    st.write(f"Total schedules: {len(st.session_state.schedule_history)}")
    
    for i, schedule in enumerate(st.session_state.schedule_history):
        schedule_id = schedule.get("schedule_id", f"Schedule {i+1}")
        created_date = schedule.get("created_at", "Unknown date")
        
        with st.expander(f"📋 {schedule_id} - {created_date}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Macro Plan:**")
                st.write(schedule.get("macro_plan", "No macro plan"))
            
            with col2:
                if st.button(f"🔄 Reactivate", key=f"reactivate_{i}"):
                    st.session_state.fitness_coach.activate_schedule(schedule_id)
                    st.session_state.active_schedule = schedule
                    st.success(f"✅ {schedule_id} reactivated!")
                    st.rerun()
            
            if schedule.get("micro_plan"):
                st.write("**Weekly Plan:**")
                for day, workout in schedule["micro_plan"].items():
                    st.write(f"- **{day}**: {workout.get('type', 'Rest')} ({workout.get('duration', 'N/A')})")


def render_schedule_creation():
    """Enhanced schedule creation with proper routing."""
    st.header("🆕 Create New Schedule")
    
    if not st.session_state.user_profile:
        st.error("❌ Please complete your profile first!")
        return
    
    # Check if macro plan exists
    macro_plan = st.session_state.fitness_coach.get_macro_plan()
    
    # Option selection
    st.subheader("🎯 What would you like to create?")
    
    creation_option = st.radio(
        "Choose your option:",
        [
            "📅 Create new weekly schedule (following current macro plan)",
            "🔄 Create new weekly schedule (building from last week)",
            "📈 Create new macro plan (will replace current plan)"
        ],
        key="creation_option_radio"  # Add unique key
    )
    
    # Route based on selection
    if "Create new macro plan" in creation_option:
        # Macro plan creation
        render_macro_plan_creation()
    
    elif "following current macro plan" in creation_option:
        # Weekly schedule following macro plan
        if not macro_plan:
            st.warning("⚠️ No macro plan found. Please create a macro plan first.")
            st.info("👆 Select 'Create new macro plan' option above to get started.")
        else:
            render_weekly_schedule_creation(mode="macro")
    
    elif "building from last week" in creation_option:
        # Weekly schedule building from previous week
        recent_schedules = st.session_state.fitness_coach.get_recent_schedules()
        if not recent_schedules:
            st.warning("⚠️ No previous schedules found. Creating fresh schedule.")
            render_weekly_schedule_creation(mode="fresh")
        else:
            render_weekly_schedule_creation(mode="progressive")

def render_macro_plan_creation():
    """Enhanced macro plan creation with feedback and regeneration."""
    st.subheader("📈 Create New Macro Plan")
    
    # Show current macro plan if exists
    current_macro = st.session_state.fitness_coach.get_macro_plan()
    if current_macro:
        with st.expander("⚠️ Current Macro Plan (will be replaced)", expanded=False):
            st.write(current_macro["macro_plan"])
            st.caption(f"Created: {current_macro['created_at'][:10]}")
    
    # Check if we just created a macro plan (stored in session state)
    if st.session_state.get("newly_created_macro_plan"):
        render_macro_plan_feedback()
    else:
        # Initial macro plan creation
        st.info("This will create a new long-term training progression plan (4-12 weeks).")
        
        # Additional preferences for macro plan
        with st.expander("🎯 Macro Plan Preferences", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                plan_duration = st.selectbox(
                    "Plan Duration:",
                    ["4 weeks", "6 weeks", "8 weeks", "12 weeks"],
                    index=1
                )
                
                periodization_type = st.selectbox(
                    "Periodization Style:",
                    ["Linear progression", "Undulating", "Block periodization", "Flexible"]
                )
            
            with col2:
                primary_emphasis = st.selectbox(
                    "Primary Emphasis:",
                    ["Balanced fitness", "Strength focus", "Endurance focus", "Weight loss", "Sport-specific"]
                )
                
                experience_level = st.selectbox(
                    "Training Experience:",
                    ["Beginner", "Intermediate", "Advanced"]
                )
        
        # Special considerations
        special_considerations = st.text_area(
            "Special Considerations:",
            placeholder="e.g., upcoming events, injury history, specific goals, time constraints..."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Generate Macro Plan", type="primary", key="generate_macro_btn"):
                with st.spinner("Creating your macro training plan..."):
                    try:
                        # Enhanced user profile with macro plan preferences
                        enhanced_profile = st.session_state.user_profile.copy()
                        enhanced_profile["macro_preferences"] = {
                            "duration": plan_duration,
                            "periodization": periodization_type,
                            "emphasis": primary_emphasis,
                            "experience": experience_level,
                            "considerations": special_considerations
                        }
                        
                        macro_plan = st.session_state.fitness_coach.create_macro_plan(enhanced_profile)
                        
                        if macro_plan and macro_plan != "Failed to create macro plan":
                            # Store the newly created plan for feedback
                            st.session_state.newly_created_macro_plan = macro_plan
                            st.session_state.current_macro_plan = macro_plan
                            st.success("✅ Macro plan created successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to create macro plan. Please try again.")
                            
                    except Exception as e:
                        st.error(f"Error creating macro plan: {str(e)}")
                        st.write("Debug info:", str(e))
        
        with col2:
            if st.button("❌ Cancel", key="cancel_macro_btn"):
                st.rerun()

def render_macro_plan_feedback():
    """Handle feedback and regeneration for newly created macro plan."""
    st.subheader("📈 Your New Macro Plan")
    
    macro_plan = st.session_state.newly_created_macro_plan
    
    # Display the created macro plan
    with st.expander("📋 Generated Macro Plan", expanded=True):
        st.write(macro_plan)
    
    st.subheader("💬 Provide Feedback")
    st.info("Review your macro plan above. You can provide feedback to refine it or accept it as-is.")
    
    # Feedback options
    feedback_type = st.radio(
        "How do you feel about this macro plan?",
        [
            "✅ Perfect! I'm ready to use this plan",
            "🔧 Good, but needs some adjustments",
            "🔄 Not quite right, please regenerate"
        ],
        key="macro_feedback_radio"
    )
    
    if "Perfect" in feedback_type:
        # Accept the plan
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Accept & Activate Plan", type="primary", key="accept_macro_btn"):
                # Clear the temporary storage and activate
                st.session_state.newly_created_macro_plan = None
                st.success("🎉 Macro plan activated! You can now create weekly schedules.")
                
                # Auto-switch to weekly schedule creation
                if st.button("📅 Create First Weekly Schedule", key="create_first_weekly_btn"):
                    st.session_state.creation_option_radio = "📅 Create new weekly schedule (following current macro plan)"
                    st.rerun()
        
        with col2:
            if st.button("🔄 Make Changes First", key="modify_macro_btn"):
                # Keep in feedback mode
                pass
    
    elif "adjustments" in feedback_type:
        # Specific feedback for adjustments
        st.subheader("🔧 What adjustments would you like?")
        
        adjustment_areas = st.multiselect(
            "Select areas that need adjustment:",
            [
                "Exercise selection/types",
                "Training frequency",
                "Intensity progression", 
                "Duration/time commitment",
                "Recovery periods",
                "Specific goals focus",
                "Periodization structure"
            ]
        )
        
        specific_feedback = st.text_area(
            "Specific feedback and requests:",
            placeholder="e.g., 'I prefer more strength training and less cardio', 'Need shorter workouts', 'Want more recovery time'...",
            height=100
        )
        
        if st.button("🔧 Regenerate with Adjustments", type="primary", key="regenerate_adjusted_btn"):
            if specific_feedback or adjustment_areas:
                with st.spinner("Refining your macro plan based on feedback..."):
                    try:
                        # Create feedback-enhanced profile
                        enhanced_profile = st.session_state.user_profile.copy()
                        enhanced_profile["macro_feedback"] = {
                            "previous_plan": macro_plan,
                            "adjustment_areas": adjustment_areas,
                            "specific_feedback": specific_feedback,
                            "feedback_type": "adjustments"
                        }
                        
                        refined_plan = st.session_state.fitness_coach.create_macro_plan(enhanced_profile)
                        
                        if refined_plan and refined_plan != "Failed to create macro plan":
                            st.session_state.newly_created_macro_plan = refined_plan
                            st.session_state.current_macro_plan = refined_plan
                            st.success("✅ Macro plan refined based on your feedback!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to refine macro plan. Please try again.")
                            
                    except Exception as e:
                        st.error(f"Error refining macro plan: {str(e)}")
            else:
                st.warning("⚠️ Please provide some feedback before regenerating.")
    
    elif "regenerate" in feedback_type:
        # Complete regeneration
        st.subheader("🔄 Regenerate Macro Plan")
        
        regeneration_reason = st.text_area(
            "What didn't work about this plan?",
            placeholder="e.g., 'Too intense for my schedule', 'Doesn't match my goals', 'Need different approach'...",
            height=80
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Generate Completely New Plan", type="primary", key="regenerate_new_btn"):
                if regeneration_reason:
                    with st.spinner("Creating a completely new macro plan..."):
                        try:
                            # Create feedback-enhanced profile for regeneration
                            enhanced_profile = st.session_state.user_profile.copy()
                            enhanced_profile["macro_feedback"] = {
                                "previous_plan": macro_plan,
                                "regeneration_reason": regeneration_reason,
                                "feedback_type": "regenerate"
                            }
                            
                            new_plan = st.session_state.fitness_coach.create_macro_plan(enhanced_profile)
                            
                            if new_plan and new_plan != "Failed to create macro plan":
                                st.session_state.newly_created_macro_plan = new_plan
                                st.session_state.current_macro_plan = new_plan
                                st.success("✅ New macro plan generated!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to generate new macro plan. Please try again.")
                                
                        except Exception as e:
                            st.error(f"Error generating new macro plan: {str(e)}")
                else:
                    st.warning("⚠️ Please explain what didn't work before regenerating.")
        
        with col2:
            if st.button("⬅️ Go Back to Adjustments", key="back_to_adjustments_btn"):
                st.session_state.macro_feedback_radio = "🔧 Good, but needs some adjustments"
                st.rerun()
    
    # Option to start over completely
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Discard & Start Over", key="discard_macro_btn"):
            st.session_state.newly_created_macro_plan = None
            st.session_state.current_macro_plan = None
            st.info("Macro plan discarded. You can create a new one.")
            st.rerun()
    
    with col2:
        if st.button("💾 Save Draft & Continue Later", key="save_draft_btn"):
            st.session_state.newly_created_macro_plan = None
            st.success("Draft saved! You can continue refining later.")
            st.rerun()



def render_weekly_schedule_creation(mode: str = "macro"):
    """Create weekly schedule with different modes - FIXED ROUTING."""
    st.subheader("📅 Create Weekly Schedule")
    
    if mode == "macro":
        macro_plan = st.session_state.fitness_coach.get_macro_plan()
        if macro_plan:
            st.success("📈 Using your active macro plan for progression")
            with st.expander("📋 Current Macro Plan Context", expanded=False):
                st.write(macro_plan["macro_plan"])
        else:
            st.error("❌ No macro plan found! Please create a macro plan first.")
            return
            
    elif mode == "progressive":
        st.info("🔄 Building upon your previous week's progress")
    else:
        st.info("🆕 Creating fresh schedule")
    
    # Week selection for progressive mode
    if mode == "progressive":
        recent_schedules = st.session_state.fitness_coach.get_recent_schedules()
        if recent_schedules:
            reference_week = st.selectbox(
                "Build from which week?",
                options=[(i, f"Week {i+1} ago - {sched['schedule']['schedule_id']}") 
                        for i, sched in enumerate(recent_schedules)],
                format_func=lambda x: x[1]
            )
            st.session_state.reference_week_index = reference_week[0]
    
    # Availability input
    st.subheader("🗓️ Your Availability This Week")
    
    # Quick setup or detailed setup
    setup_type = st.radio(
        "How would you like to set your availability?",
        ["⚡ Quick Setup (same pattern)", "🔧 Detailed Setup (day by day)"],
        key="availability_setup_type"
    )
    
    availability = {}
    
    if "Quick Setup" in setup_type:
        # Quick availability setup
        col1, col2, col3 = st.columns(3)
        
        with col1:
            workout_days = st.number_input(
                "Workouts per week:",
                min_value=1, max_value=7, value=3
            )
            
        with col2:
            workout_duration = st.selectbox(
                "Workout duration:",
                ["30 minutes", "45 minutes", "60 minutes", "90 minutes"],
                index=1
            )
            
        with col3:
            preferred_time = st.selectbox(
                "Preferred time:",
                ["Early Morning (6-8 AM)", "Morning (8-10 AM)", "Lunch (12-2 PM)", 
                 "Afternoon (3-5 PM)", "Evening (6-8 PM)", "Night (8-10 PM)"],
                index=4
            )
        
        # Auto-assign days
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Suggest optimal days based on workout count
        if workout_days == 3:
            suggested_days = ["Monday", "Wednesday", "Friday"]
        elif workout_days == 4:
            suggested_days = ["Monday", "Tuesday", "Thursday", "Friday"]
        elif workout_days == 5:
            suggested_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        elif workout_days == 6:
            suggested_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        else:
            suggested_days = day_names[:workout_days]
        
        selected_days = st.multiselect(
            "Workout days:",
            day_names,
            default=suggested_days[:workout_days]
        )
        
        # Build availability
        for day in day_names:
            if day in selected_days:
                availability[day] = {
                    "available": True,
                    "preferred_time": preferred_time,
                    "duration": workout_duration
                }
            else:
                availability[day] = {"available": False}
                
    else:
        # Detailed day-by-day setup
        st.write("**Set availability for each day:**")
        
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col1:
                available = st.checkbox(f"**{day}**", key=f"available_{day}")
            
            with col2:
                if available:
                    time_slot = st.selectbox(
                        "Time:",
                        ["Early Morning", "Morning", "Lunch", "Afternoon", "Evening", "Night"],
                        key=f"time_{day}"
                    )
                else:
                    time_slot = None
            
            with col3:
                if available:
                    duration = st.selectbox(
                        "Duration:",
                        ["30 min", "45 min", "60 min", "90 min"],
                        key=f"duration_{day}"
                    )
                else:
                    duration = None
            
            availability[day] = {
                "available": available,
                "preferred_time": time_slot,
                "duration": duration
            } if available else {"available": False}
    
    # Show availability summary
    with st.expander("📋 Availability Summary", expanded=True):
        workout_count = sum(1 for day_avail in availability.values() if day_avail.get("available"))
        st.write(f"**Total workout days:** {workout_count}")
        
        for day, avail in availability.items():
            if avail["available"]:
                st.write(f"✅ **{day}**: {avail['duration']} at {avail['preferred_time']}")
            else:
                st.write(f"🛌 **{day}**: Rest day")
    
    # Additional preferences
    st.subheader("🎯 This Week's Focus")
    
    col1, col2 = st.columns(2)
    with col1:
        focus_areas = st.multiselect(
            "Focus areas:",
            ["Cardio/Endurance", "Strength Training", "Flexibility/Yoga", "Recovery", "Sport-Specific"],
            default=["Strength Training", "Cardio/Endurance"]
        )
        
    with col2:
        intensity_level = st.selectbox(
            "Overall intensity:",
            ["Light/Recovery", "Moderate", "High", "Peak Training"],
            index=1
        )
    
    # Special notes
    special_notes = st.text_area(
        "Special notes for this week:",
        placeholder="e.g., feeling tired, have an event coming up, want to try something new, sore from last week...",
        height=80
    )
    
    # Build preferences
    preferences = {
        "mode": mode,
        "focus_areas": focus_areas,
        "intensity_level": intensity_level,
        "special_notes": special_notes
    }
    
    if mode == "progressive" and st.session_state.get("reference_week_index") is not None:
        preferences["reference_week_index"] = st.session_state.reference_week_index
    
    # Generate button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Generate Weekly Schedule", type="primary", key="generate_weekly_btn"):
            # Validate availability
            workout_days = sum(1 for day_avail in availability.values() if day_avail.get("available"))
            if workout_days == 0:
                st.error("❌ Please select at least one workout day!")
                return
                
            with st.spinner("Creating your personalized weekly schedule..."):
                try:
                    print("UI: Starting schedule creation...")
                    print(f"UI: Availability = {availability}")
                    print(f"UI: Preferences = {preferences}")
                    
                    # Create the schedule
                    schedule = st.session_state.fitness_coach.create_weekly_schedule(
                        availability, preferences
                    )
                    
                    print(f"UI: Schedule result = {schedule}")
                    print(f"UI: Schedule has micro_plan = {schedule.get('micro_plan') is not None}")
                    
                    if schedule and schedule.get("micro_plan"):
                        st.success("✅ Weekly schedule created successfully!")
                        
                        # Update session state
                        st.session_state.active_schedule = schedule
                        
                        # Show preview
                        render_schedule_preview(schedule)
                        
                    elif schedule:
                        st.warning("⚠️ Schedule was created but may be incomplete. Please check the details.")
                        st.write("Debug - Schedule data:", schedule)
                        
                        if schedule.get("micro_plan"):
                            st.session_state.active_schedule = schedule
                            render_schedule_preview(schedule)
                        
                    else:
                        st.error("❌ Failed to create schedule. Please try again.")
                        
                        # Show debug information
                        with st.expander("🔍 Debug Information"):
                            st.write("**User Profile:**", st.session_state.user_profile is not None)
                            st.write("**Macro Plan:**", st.session_state.fitness_coach.get_macro_plan() is not None)
                            st.write("**Availability:**", availability)
                            st.write("**Preferences:**", preferences)
                        
                except Exception as e:
                    st.error(f"❌ Error creating schedule: {str(e)}")
                    
                    # Show detailed error information
                    with st.expander("🔍 Error Details"):
                        st.code(str(e))
                        import traceback
                        st.code(traceback.format_exc())
    
    with col2:
        if st.button("🔙 Back to Options", key="back_to_options_btn"):
            st.rerun()

def render_schedule_preview(schedule):
    """Show preview of created schedule with activation option."""
    st.subheader("📅 Schedule Preview")
    
    # Summary stats
    col1, col2, col3 = st.columns(3)
    
    workout_days = sum(1 for workout in schedule["micro_plan"].values() 
                      if workout.get("type") != "Rest")
    total_time = sum(int(workout.get("duration", "0").split()[0]) 
                    for workout in schedule["micro_plan"].values() 
                    if workout.get("type") != "Rest" and workout.get("duration"))
    
    with col1:
        st.metric("Workout Days", workout_days)
    with col2:
        st.metric("Total Time", f"{total_time} min")
    with col3:
        st.metric("Avg. Per Session", f"{total_time//workout_days if workout_days > 0 else 0} min")
    
    # Daily breakdown
    for day, workout in schedule["micro_plan"].items():
        if workout.get("type") != "Rest":
            with st.expander(f"🏋️‍♂️ {day} - {workout.get('type', 'Workout')}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**⏰ Duration:** {workout.get('duration', 'N/A')}")
                    st.write(f"**🎯 Focus:** {workout.get('focus', 'N/A')}")
                with col2:
                    st.write(f"**💪 Intensity:** {workout.get('intensity', 'Moderate')}")
                    st.write(f"**📍 Location:** {workout.get('location', 'Flexible')}")
                
                st.write(f"**📝 Details:** {workout.get('details', 'No details provided')}")
        else:
            st.write(f"🛌 **{day}**: Rest and recovery day")
    
    # Activation buttons
    st.subheader("🎯 Next Steps")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Activate This Schedule", type="primary", key="activate_schedule_btn"):
            st.session_state.fitness_coach.activate_schedule(schedule["schedule_id"])
            st.success("🎉 Schedule activated! Check 'Current Schedule' tab.")
            st.balloons()
            
            # Option to switch to current schedule tab
            if st.button("📅 View Active Schedule", key="view_active_btn"):
                st.switch_page("📅 Current Schedule")
    
    with col2:
        if st.button("🔄 Generate Different Schedule", key="regenerate_schedule_btn"):
            st.info("Modify your preferences above and generate again.")
            st.rerun()
    
    with col3:
        if st.button("💬 I need to adjust this", key="feedback_schedule_btn"):
            st.info("Schedule feedback feature coming soon!")


def create_app():
    """Enhanced Streamlit app with proper session state initialization."""
    st.set_page_config(
        page_title=settings.APP_NAME,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize app FIRST - this sets up all session state variables
    initialize_app()
    
    st.title(f"🏋️‍♂️ {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Now we can safely access session state variables
    # Sidebar with user stats
    with st.sidebar:
        st.header("👤 User Info")
        stats = st.session_state.user_stats  # This is now safely initialized
        st.info(f"""
        **User ID:** {stats['user_id']}
        **Profile:** {'✅' if stats['has_profile'] else '❌'}
        **Schedules:** {stats['total_schedules']}
        **Feedback:** {stats['total_feedback']}
        """)
        
        st.header("ℹ️ About")
        st.info(
            "Your data is saved locally and will persist between sessions. "
            "All your preferences and schedules are remembered!"
        )
        
        st.header("⚠️ Disclaimer")
        st.warning(
            "This AI-generated fitness advice is for informational purposes only. "
            "Please consult with a healthcare professional before starting any new "
            "fitness program."
        )
    
    # Main navigation - now safe to check user_profile
    if st.session_state.user_profile is None:
        # Force profile setup first
        render_profile_setup()
    else:
        # Show full navigation
        tab1, tab2, tab3, tab4 = st.tabs([
            "👤 Profile", 
            "📅 Current Schedule", 
            "🆕 Create New Schedule",
            "📚 History"
        ])
        
        with tab1:
            render_profile_setup()
        
        with tab2:
            render_current_schedule()
        
        with tab3:
            render_schedule_creation()
        
        with tab4:
            render_schedule_history()


def main():
    """Main entry point."""
    create_app()


if __name__ == "__main__":
    main()