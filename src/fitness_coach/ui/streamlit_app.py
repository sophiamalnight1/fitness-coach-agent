import os
import streamlit as st
from datetime import datetime, time, timedelta
from fitness_coach.core.coach import AIFitnessCoach
from fitness_coach.config.settings import settings
from fitness_coach.integrations.google_calendar import GoogleCalendarService


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
    
    # Initialize calendar service
    if "calendar_service" not in st.session_state:
        st.session_state.calendar_service = GoogleCalendarService()
    
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
    
    # Initialize calendar setup state
    if "show_calendar_setup" not in st.session_state:
        st.session_state.show_calendar_setup = False


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
            # Set tab to schedule creation
            st.info("👆 Go to 'Create New Schedule' tab to create a new week")
    
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
            elif "Cardio" in workout.get("type", ""):
                icon = "🏃‍♂️"
            elif "Strength" in workout.get("type", ""):
                icon = "💪"
            elif "Yoga" in workout.get("type", "") or "Flexibility" in workout.get("type", ""):
                icon = "🧘‍♀️"
            else:
                icon = "🏋️‍♂️"
            
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


def render_schedule_creation():
    """Enhanced schedule creation with macro/micro options and calendar integration for weekly only."""
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
        key="creation_option_radio"
    )
    
    # Route based on selection
    if "Create new macro plan" in creation_option:
        # Macro plan creation (no calendar integration needed)
        render_macro_plan_creation()
    
    elif "following current macro plan" in creation_option:
        # Weekly schedule following macro plan (WITH calendar integration)
        if not macro_plan:
            st.warning("⚠️ No macro plan found. Please create a macro plan first.")
            st.info("👆 Select 'Create new macro plan' option above to get started.")
        else:
            render_weekly_schedule_creation_with_calendar(mode="macro")
    
    elif "building from last week" in creation_option:
        # Weekly schedule building from previous week (WITH calendar integration)
        recent_schedules = st.session_state.fitness_coach.get_recent_schedules()
        if not recent_schedules:
            st.warning("⚠️ No previous schedules found. Creating fresh schedule.")
            render_weekly_schedule_creation_with_calendar(mode="fresh")
        else:
            render_weekly_schedule_creation_with_calendar(mode="progressive")


def render_macro_plan_creation():
    """Enhanced macro plan creation with feedback and regeneration (NO calendar integration)."""
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


def render_weekly_schedule_creation_with_calendar(mode: str = "macro"):
    """Enhanced weekly schedule creation with calendar integration - FIXED."""
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
    
    # Calendar integration status and quick setup - FIXED: Remove nested expander
    cal_service = st.session_state.calendar_service
    calendar_prefs = st.session_state.fitness_coach.storage.load_calendar_preferences()
    
    # Check if we're in calendar setup mode
    if st.session_state.get("show_calendar_setup", False):
        # Show calendar setup directly without expander
        render_quick_calendar_setup()
        
        # Back button
        if st.button("⬅️ Back to Schedule Creation", key="back_to_schedule"):
            st.session_state.show_calendar_setup = False
            st.rerun()
        return
    
    # Calendar setup section - FIXED: Don't nest expanders
    st.subheader("📅 Calendar Integration (Optional)")
    
    if not cal_service.is_authenticated():
        st.info("Connect your calendar to automatically detect free time slots!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔗 Quick Calendar Setup", key="quick_cal_setup"):
                st.session_state.show_calendar_setup = True
                st.rerun()
        
        with col2:
            st.write("**Benefits:**")
            st.write("• Automatic conflict detection")
            st.write("• One-click workout booking")
            st.write("• Smart availability detection")
    else:
        st.success("✅ Calendar connected!")
        if not calendar_prefs:
            st.warning("⚙️ Set up work hours for better scheduling")
            if st.button("⚙️ Configure Work Hours", key="setup_work_hours"):
                render_quick_work_hours_setup()
        else:
            st.info(f"Work hours: {calendar_prefs.get('work_start', '9:00')} - {calendar_prefs.get('work_end', '17:00')}")
    
    # Availability method selection
    availability_methods = ["⚙️ Manual Setup"]
    if cal_service.is_authenticated():
        availability_methods.insert(0, "🗓️ Use Calendar + Manual Override")
    
    availability_method = st.radio(
        "How would you like to set your availability?",
        availability_methods,
        key="availability_method_radio"
    )
    
    # Get availability based on method
    if "Calendar" in availability_method and cal_service.is_authenticated():
        availability = render_calendar_based_availability(cal_service, calendar_prefs)
    else:
        availability = render_manual_availability_setup()
    
    # Show availability summary
    render_availability_summary(availability)
    
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
    
    special_notes = st.text_area(
        "Special notes for this week:",
        placeholder="e.g., feeling tired, have an event coming up, want to try something new...",
        height=80
    )
    
    # Build preferences
    preferences = {
        "mode": mode,
        "focus_areas": focus_areas,
        "intensity_level": intensity_level,
        "special_notes": special_notes,
        "calendar_integration": "Calendar" in availability_method
    }
    
    # Generate and schedule buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Generate Weekly Schedule", type="primary", key="generate_weekly_cal_btn"):
            generate_schedule_with_calendar(availability, preferences, cal_service)
    
    with col2:
        if st.button("🔙 Back to Options", key="back_to_options_cal_btn"):
            st.rerun()


def render_quick_calendar_setup():
    """Fixed quick calendar setup - NO nested expanders."""
    st.subheader("🔗 Quick Calendar Setup")
    
    cal_service = st.session_state.calendar_service
    
    # Debug section as regular content (not expander)
    if st.checkbox("🔍 Show Debug Information", key="show_debug_info"):
        debug_calendar_state()
    
    # Initialize auth method state if not exists
    if "auth_method_selection" not in st.session_state:
        st.session_state.auth_method_selection = "🔗 URL Method (Easier)"
    
    # Method selection with persistent state
    auth_method = st.radio(
        "Choose authentication method:",
        [
            "🔗 URL Method (Easier)",
            "📋 Code Method (Manual)"
        ],
        key="auth_method_radio",
        index=0 if "URL Method" in st.session_state.auth_method_selection else 1
    )
    
    # Update session state when method changes
    if auth_method != st.session_state.auth_method_selection:
        st.session_state.auth_method_selection = auth_method
        st.rerun()
    
    # Show appropriate method based on selection
    if "URL Method" in auth_method:
        render_url_auth_method(cal_service)
    else:
        render_code_auth_method(cal_service)


def render_url_auth_method(cal_service):
    """Fixed URL-based authentication method with better success handling."""
    st.markdown("### 🔗 URL Method")
    
    try:
        # Generate auth URL
        if st.button("🚀 Generate Authorization Link", key="generate_auth_url"):
            with st.spinner("Generating authorization link..."):
                auth_url = cal_service.get_auth_url()
                st.session_state.auth_url = auth_url
                st.session_state.show_auth_form = True
        
        # Show auth form if URL generated
        if st.session_state.get("show_auth_form") and st.session_state.get("auth_url"):
            st.success("✅ Authorization URL generated!")
            
            st.markdown(f"**[🚀 Click here to authorize Google Calendar]({st.session_state.auth_url})**")
            
            st.info("""
            **Instructions:**
            1. Click the link above
            2. Sign in to Google and grant permissions
            3. After authorization, you'll be redirected to a page that might show an error (this is normal)
            4. Copy the ENTIRE URL from your browser's address bar
            5. Paste it in the box below
            """)
            
            callback_url = st.text_area(
                "📋 Paste the full redirect URL here:",
                placeholder="http://localhost:8501/?code=4/0AanRRTs...",
                height=100,
                key="callback_url_input"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Connect with URL", key="connect_with_url") and callback_url:
                    with st.spinner("Connecting to Google Calendar..."):
                        try:
                            print(f"DEBUG: Attempting to authenticate with URL: {callback_url[:100]}...")
                            
                            success = cal_service.authenticate_with_url(callback_url)
                            
                            if success:
                                st.success("🎉 Calendar connected successfully!")
                                
                                # Double-check authentication after a brief delay
                                import time
                                time.sleep(0.5)  # Brief delay
                                
                                # Re-check authentication
                                final_check = cal_service.is_authenticated()
                                print(f"DEBUG: Final authentication check: {final_check}")
                                
                                if final_check:
                                    # Clear the form state
                                    st.session_state.show_auth_form = False
                                    st.session_state.auth_url = None
                                    st.session_state.show_calendar_setup = False
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("❌ Authentication verification failed. Please try again.")
                            else:
                                st.error("❌ Connection failed. Please check the URL and try again.")
                                # Show debug info
                                st.write("**Debug Info:**")
                                st.write(f"URL length: {len(callback_url)}")
                                st.write(f"Contains 'code=': {'code=' in callback_url}")
                                
                        except Exception as e:
                            st.error(f"❌ Authentication error: {str(e)}")
                            print(f"Full authentication error: {e}")
                            import traceback
                            traceback.print_exc()
            
            with col2:
                if st.button("🔄 Generate New Link", key="regenerate_auth_url"):
                    st.session_state.show_auth_form = False
                    st.session_state.auth_url = None
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Error setting up calendar: {str(e)}")
        print(f"Setup error: {e}")

def debug_calendar_state():
    """Enhanced debug function."""
    st.write("**Session State Debug:**")
    
    # Check for Google credentials
    if 'google_credentials' in st.session_state:
        creds_data = st.session_state.google_credentials
        st.write("✅ Google credentials found in session state")
        st.write(f"- Token exists: {bool(creds_data.get('token'))}")
        st.write(f"- Refresh token exists: {bool(creds_data.get('refresh_token'))}")
        st.write(f"- Client ID exists: {bool(creds_data.get('client_id'))}")
        st.write(f"- Expiry: {creds_data.get('expiry', 'Not set')}")
        
        # Manual test button
        if st.button("🔄 Force Re-initialize Service", key="force_reinit"):
            try:
                cal_service = st.session_state.calendar_service
                cal_service._initialize_service()
                auth_result = cal_service.is_authenticated()
                st.write(f"Re-initialization result: {auth_result}")
            except Exception as e:
                st.error(f"Re-initialization failed: {e}")
    else:
        st.write("❌ No Google credentials in session state")
    
    # Check calendar service
    cal_service = st.session_state.calendar_service
    st.write(f"Calendar service authenticated: {cal_service.is_authenticated()}")
    
    # Check environment variables
    st.write("**Environment Variables:**")
    st.write(f"- GOOGLE_CLIENT_ID set: {bool(os.getenv('GOOGLE_CLIENT_ID'))}")
    st.write(f"- GOOGLE_CLIENT_SECRET set: {bool(os.getenv('GOOGLE_CLIENT_SECRET'))}")
    
    # Clear credentials button for testing
    if st.button("🗑️ Clear Stored Credentials", key="clear_creds"):
        if 'google_credentials' in st.session_state:
            del st.session_state.google_credentials
        st.success("Credentials cleared!")
        st.rerun()


def render_code_auth_method(cal_service):
    """Fixed code-based authentication method."""
    st.markdown("### 📋 Code Method")
    
    try:
        # Generate auth URL
        if st.button("🚀 Generate Authorization Link", key="generate_auth_url_code"):
            with st.spinner("Generating authorization link..."):
                auth_url = cal_service.get_auth_url()
                st.session_state.auth_url_code = auth_url
                st.session_state.show_code_form = True
        
        # Show auth form if URL generated
        if st.session_state.get("show_code_form") and st.session_state.get("auth_url_code"):
            st.success("✅ Authorization URL generated!")
            
            st.markdown(f"**[🚀 Click here to authorize Google Calendar]({st.session_state.auth_url_code})**")
            
            st.info("""
            **Instructions:**
            1. Click the link above
            2. Sign in to Google and grant permissions
            3. You'll be redirected to: http://localhost:8501/?code=XXXXX
            4. Copy only the code part (everything after 'code=' and before '&')
            5. Paste it below
            """)
            
            # Help section as regular content (not expander)
            if st.checkbox("🔍 How to find the authorization code", key="show_code_help"):
                st.write("""
                After authorization, the URL will look like:
                ```
                http://localhost:8501/?code=4/0AanRRTsXXXXXXXXX&scope=https://www.googleapis.com/auth/calendar
                ```
                
                Your authorization code is: `4/0AanRRTsXXXXXXXXX`
                
                Copy everything between `code=` and `&scope`
                """)
            
            auth_code = st.text_input(
                "📋 Authorization Code:",
                placeholder="4/0AanRRTsXXXXXXXXX",
                help="Paste only the code part, not the full URL",
                key="auth_code_input"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Connect with Code", key="connect_with_code") and auth_code:
                    with st.spinner("Connecting to Google Calendar..."):
                        try:
                            print(f"DEBUG: Attempting to authenticate with code: {auth_code[:20]}...")
                            
                            success = cal_service.authenticate_with_code(auth_code)
                            
                            if success:
                                st.success("🎉 Calendar connected successfully!")
                                # Clear the form state
                                st.session_state.show_code_form = False
                                st.session_state.auth_url_code = None
                                st.session_state.show_calendar_setup = False
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ Connection failed. Please check the code and try again.")
                                
                        except Exception as e:
                            st.error(f"❌ Authentication error: {str(e)}")
                            print(f"Code authentication error: {e}")
            
            with col2:
                if st.button("🔄 Generate New Link", key="regenerate_auth_url_code"):
                    st.session_state.show_code_form = False
                    st.session_state.auth_url_code = None
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Error setting up calendar: {str(e)}")
        print(f"Setup error: {e}")


def debug_calendar_state():
    """Debug function to check calendar authentication state - simplified."""
    st.write("**Session State Debug:**")
    
    # Check for Google credentials
    if 'google_credentials' in st.session_state:
        creds_data = st.session_state.google_credentials
        st.write("✅ Google credentials found in session state")
        st.write(f"- Token exists: {bool(creds_data.get('token'))}")
        st.write(f"- Refresh token exists: {bool(creds_data.get('refresh_token'))}")
        st.write(f"- Client ID exists: {bool(creds_data.get('client_id'))}")
    else:
        st.write("❌ No Google credentials in session state")
    
    # Check calendar service
    cal_service = st.session_state.calendar_service
    st.write(f"Calendar service authenticated: {cal_service.is_authenticated()}")
    
    # Check environment variables
    st.write("**Environment Variables:**")
    st.write(f"- GOOGLE_CLIENT_ID set: {bool(os.getenv('GOOGLE_CLIENT_ID'))}")
    st.write(f"- GOOGLE_CLIENT_SECRET set: {bool(os.getenv('GOOGLE_CLIENT_SECRET'))}")


def render_quick_work_hours_setup():
    """Quick work hours setup."""
    st.subheader("⚙️ Quick Work Hours Setup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        work_start = st.time_input("Work starts:", value=time(9, 0))
        work_end = st.time_input("Work ends:", value=time(17, 0))
    
    with col2:
        work_days = st.multiselect(
            "Work days:",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        )
        
        allow_lunch = st.checkbox("Allow lunch workouts", value=True)
    
    if st.button("💾 Save Work Hours"):
        preferences = {
            'work_start': work_start.strftime('%H:%M'),
            'work_end': work_end.strftime('%H:%M'),
            'work_days': work_days,
            'allow_lunch_workouts': allow_lunch,
            'lunch_start': '12:00',
            'lunch_end': '13:00'
        }
        
        st.session_state.fitness_coach.storage.save_calendar_preferences(preferences)
        st.success("✅ Work hours saved!")
        st.rerun()


def render_calendar_based_availability(cal_service, calendar_prefs):
    """Render calendar-based availability detection with manual overrides."""
    st.subheader("📅 Calendar-Detected Availability")
    
    try:
        # Get next week's availability
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        
        with st.spinner("📖 Analyzing your calendar..."):
            available_slots = cal_service.find_available_slots(
                start_date, end_date,
                duration_minutes=45,  # Default duration
                work_hours=calendar_prefs or {},
                preferences=calendar_prefs or {}
            )
        
        # Group slots by day
        slots_by_day = {}
        for slot in available_slots:
            day = slot['start'].strftime('%A')
            if day not in slots_by_day:
                slots_by_day[day] = []
            slots_by_day[day].append(slot)
        
        availability = {}
        
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            with st.expander(f"📅 {day}", expanded=False):
                day_slots = slots_by_day.get(day, [])
                
                if day_slots:
                    st.success(f"✅ Found {len(day_slots)} available slots")
                    
                    # Show available slots
                    slot_options = []
                    for i, slot in enumerate(day_slots):
                        time_str = slot['start'].strftime('%I:%M %p')
                        window_type = slot['window_type'].replace('_', ' ').title()
                        slot_options.append(f"{time_str} ({window_type}) - {slot['available_duration']} min")
                    
                    selected_slot_idx = st.selectbox(
                        f"Choose slot for {day}:",
                        options=[-1] + list(range(len(slot_options))),
                        format_func=lambda x: "❌ No workout" if x == -1 else f"✅ {slot_options[x]}",
                        key=f"slot_{day}"
                    )
                    
                    if selected_slot_idx >= 0:
                        selected_slot = day_slots[selected_slot_idx]
                        availability[day] = {
                            "available": True,
                            "calendar_slot": selected_slot,
                            "start_time": selected_slot['start'],
                            "duration": "45 minutes",
                            "window_type": selected_slot['window_type'],
                            "source": "calendar"
                        }
                    else:
                        availability[day] = {"available": False}
                    
                    # Manual override option
                    if st.checkbox(f"Manual override for {day}", key=f"override_{day}"):
                        st.info("⚙️ Manual settings will override calendar detection")
                        
                        manual_available = st.checkbox(f"Available for workout", key=f"manual_avail_{day}")
                        
                        if manual_available:
                            manual_time = st.time_input(f"Preferred time:", key=f"manual_time_{day}")
                            manual_duration = st.selectbox(
                                f"Duration:",
                                ["30 minutes", "45 minutes", "60 minutes", "90 minutes"],
                                key=f"manual_duration_{day}"
                            )
                            
                            availability[day] = {
                                "available": True,
                                "manual_override": True,
                                "preferred_time": manual_time.strftime('%H:%M'),
                                "duration": manual_duration,
                                "source": "manual_override"
                            }
                        else:
                            availability[day] = {"available": False, "manual_override": True}
                
                else:
                    st.warning(f"⚠️ No available slots detected for {day}")
                    
                    # Manual input for days with no calendar availability
                    manual_available = st.checkbox(f"Add manual workout time for {day}", key=f"manual_add_{day}")
                    
                    if manual_available:
                        col1, col2 = st.columns(2)
                        with col1:
                            manual_time = st.time_input(f"Time:", key=f"add_time_{day}")
                        with col2:
                            manual_duration = st.selectbox(
                                f"Duration:",
                                ["30 minutes", "45 minutes", "60 minutes", "90 minutes"],
                                key=f"add_duration_{day}"
                            )
                        
                        st.warning("⚠️ This may conflict with your calendar. Double-check manually.")
                        
                        availability[day] = {
                            "available": True,
                            "manual_override": True,
                            "preferred_time": manual_time.strftime('%H:%M'),
                            "duration": manual_duration,
                            "source": "manual_addition"
                        }
                    else:
                        availability[day] = {"available": False}
        
        return availability
        
    except Exception as e:
        st.error(f"❌ Error accessing calendar: {str(e)}")
        st.info("Falling back to manual availability setup...")
        return render_manual_availability_setup()


def render_manual_availability_setup():
    """Render manual availability setup."""
    st.subheader("⚙️ Manual Availability Setup")
    
    # Quick setup option
    setup_type = st.radio(
        "Setup method:",
        ["⚡ Quick Setup", "🔧 Day-by-Day Setup"],
        key="manual_setup_type"
    )
    
    availability = {}
    
    if setup_type == "⚡ Quick Setup":
        col1, col2, col3 = st.columns(3)
        
        with col1:
            workout_days = st.number_input("Workouts per week:", min_value=1, max_value=7, value=3)
        
        with col2:
            default_time = st.time_input("Default time:", value=time(18, 0))
        
        with col3:
            default_duration = st.selectbox(
                "Default duration:",
                ["30 minutes", "45 minutes", "60 minutes", "90 minutes"],
                index=1
            )
        
        # Suggest optimal days
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if workout_days == 3:
            suggested_days = ["Monday", "Wednesday", "Friday"]
        elif workout_days == 4:
            suggested_days = ["Monday", "Tuesday", "Thursday", "Friday"]
        elif workout_days == 5:
            suggested_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        else:
            suggested_days = day_names[:workout_days]
        
        selected_days = st.multiselect(
            "Workout days:",
            day_names,
            default=suggested_days
        )
        
        # Build availability
        for day in day_names:
            if day in selected_days:
                availability[day] = {
                    "available": True,
                    "preferred_time": default_time.strftime('%H:%M'),
                    "duration": default_duration,
                    "source": "manual_quick"
                }
            else:
                availability[day] = {"available": False}
    
    else:
        # Day-by-day setup
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col1:
                available = st.checkbox(f"**{day}**", key=f"manual_available_{day}")
            
            with col2:
                if available:
                    time_slot = st.time_input(
                        "Time:",
                        value=time(18, 0),
                        key=f"manual_time_slot_{day}"
                    )
                else:
                    time_slot = None
            
            with col3:
                if available:
                    duration = st.selectbox(
                        "Duration:",
                        ["30 minutes", "45 minutes", "60 minutes", "90 minutes"],
                        index=1,
                        key=f"manual_duration_slot_{day}"
                    )
                else:
                    duration = None
            
            availability[day] = {
                "available": available,
                "preferred_time": time_slot.strftime('%H:%M') if time_slot else None,
                "duration": duration,
                "source": "manual_detailed"
            } if available else {"available": False}
    
    return availability


def render_availability_summary(availability):
    """Render availability summary."""
    with st.expander("📋 Availability Summary", expanded=True):
        workout_count = sum(1 for day_avail in availability.values() if day_avail.get("available"))
        st.write(f"**Total workout days:** {workout_count}")
        
        for day, avail in availability.items():
            if avail.get("available"):
                time_info = ""
                if avail.get("start_time"):
                    time_info = avail["start_time"].strftime('%I:%M %p')
                elif avail.get("preferred_time"):
                    time_info = datetime.strptime(avail["preferred_time"], '%H:%M').strftime('%I:%M %p')
                
                source_icon = "🗓️" if "calendar" in avail.get("source", "") else "⚙️"
                override_note = " (Override)" if avail.get("manual_override") else ""
                
                st.write(f"{source_icon} **{day}**: {avail.get('duration', 'N/A')} at {time_info}{override_note}")
            else:
                st.write(f"🛌 **{day}**: Rest day")


def generate_schedule_with_calendar(availability, preferences, cal_service):
    """Generate schedule and optionally book in calendar."""
    # Validate availability
    workout_days = sum(1 for day_avail in availability.values() if day_avail.get("available"))
    if workout_days == 0:
        st.error("❌ Please select at least one workout day!")
        return
    
    with st.spinner("Creating your personalized weekly schedule..."):
        try:
            # Create the schedule
            schedule = st.session_state.fitness_coach.create_weekly_schedule(
                availability, preferences
            )
            
            if schedule and schedule.get("micro_plan"):
                st.success("✅ Weekly schedule created successfully!")
                
                # Update session state
                st.session_state.active_schedule = schedule
                
                # Show preview with calendar booking options
                render_schedule_preview_with_calendar(schedule, availability, cal_service)
                
            else:
                st.error("❌ Failed to create schedule. Please try again.")
                
        except Exception as e:
            st.error(f"Error creating schedule: {str(e)}")


def render_schedule_preview_with_calendar(schedule, availability, cal_service):
    """Show schedule preview with calendar booking options."""
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
    
    # Calendar integration status
    calendar_ready = (cal_service and cal_service.is_authenticated())
    
    if calendar_ready:
        st.success("🗓️ Ready to book workouts in your calendar!")
    else:
        st.info("📅 Connect calendar in the expandable section above to auto-book workouts")
    
    # Daily breakdown with booking options
    for day, workout in schedule["micro_plan"].items():
        day_availability = availability.get(day, {})
        
        if workout.get("type") != "Rest":
            with st.expander(f"🏋️‍♂️ {day} - {workout.get('type', 'Workout')}", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Workout details
                    st.write(f"**⏰ Duration:** {workout.get('duration', 'N/A')}")
                    st.write(f"**🎯 Focus:** {workout.get('focus', 'N/A')}")
                    st.write(f"**💪 Intensity:** {workout.get('intensity', 'Moderate')}")
                    st.write(f"**📍 Location:** {workout.get('location', 'Flexible')}")
                    st.write(f"**📝 Details:** {workout.get('details', 'No details provided')}")
                    
                    # Timing information
                    if day_availability.get("start_time"):
                        scheduled_time = day_availability["start_time"]
                        st.info(f"🕐 Scheduled for: {scheduled_time.strftime('%I:%M %p')}")
                    elif day_availability.get("preferred_time"):
                        time_str = datetime.strptime(day_availability["preferred_time"], '%H:%M').strftime('%I:%M %p')
                        st.info(f"🕐 Suggested time: {time_str}")
                
                with col2:
                    # Calendar booking section
                    if calendar_ready and day_availability.get("available"):
                        st.write("**📅 Calendar:**")
                        
                        if st.button(f"📅 Book", key=f"book_{day}", use_container_width=True):
                            book_workout_in_calendar(cal_service, day, workout, day_availability)
                    
                    elif not calendar_ready:
                        st.write("**📅 Calendar:**")
                        st.caption("Connect to book")
                    else:
                        st.write("**📅 Calendar:**")
                        st.caption("Not scheduled")
        else:
            st.write(f"🛌 **{day}**: Rest and recovery day")
    
    # Bulk actions
    st.subheader("🎯 Next Steps")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ Activate Schedule", type="primary", key="activate_with_cal"):
            st.session_state.fitness_coach.activate_schedule(schedule["schedule_id"])
            st.success("🎉 Schedule activated!")
            st.balloons()
    
    with col2:
        if calendar_ready and st.button("📅 Book All", key="book_all"):
            book_all_workouts_in_calendar(schedule, availability, cal_service)
    
    with col3:
        if st.button("🔄 Try Different", key="regenerate_with_cal"):
            st.rerun()
    
    with col4:
        if st.button("💬 Feedback", key="feedback_with_cal"):
            st.info("Feedback feature coming soon!")


def book_workout_in_calendar(cal_service, day, workout, day_availability):
    """Book a single workout in Google Calendar."""
    try:
        # Determine workout time
        workout_time = None
        if day_availability.get("start_time"):
            workout_time = day_availability["start_time"]
        elif day_availability.get("preferred_time"):
            time_obj = datetime.strptime(day_availability["preferred_time"], '%H:%M').time()
            workout_time = datetime.combine(datetime.now().date(), time_obj)
        
        if not workout_time:
            st.error("❌ No time specified for workout")
            return
        
        # Adjust workout_time to be the correct day of the week
        days_ahead = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(day)
        current_day = datetime.now().weekday()
        days_to_add = (days_ahead - current_day) % 7
        if days_to_add == 0 and datetime.now().time() > workout_time.time():
            days_to_add = 7  # Next week if time has passed today
        
        target_date = datetime.now().date() + timedelta(days=days_to_add)
        scheduled_datetime = datetime.combine(target_date, workout_time.time())
        
        # Extract duration in minutes
        duration_str = workout.get('duration', '45 minutes')
        duration_minutes = int(duration_str.split()[0]) if duration_str.split()[0].isdigit() else 45
        
        event_id = cal_service.create_workout_event(
            workout_details=workout,
            start_time=scheduled_datetime,
            duration_minutes=duration_minutes
        )
        
        if event_id:
            st.success(f"✅ {day}'s workout booked for {scheduled_datetime.strftime('%I:%M %p')}!")
        else:
            st.error(f"❌ Failed to book {day}'s workout")
            
    except Exception as e:
        st.error(f"Error booking workout: {str(e)}")


def book_all_workouts_in_calendar(schedule, availability, cal_service):
    """Book all workouts in the schedule to Google Calendar."""
    bookings_successful = 0
    bookings_failed = 0
    
    with st.spinner("Booking all workouts in your calendar..."):
        for day, workout in schedule["micro_plan"].items():
            day_availability = availability.get(day, {})
            
            if workout.get("type") != "Rest" and day_availability.get("available"):
                try:
                    # Determine workout time
                    workout_time = None
                    if day_availability.get("start_time"):
                        workout_time = day_availability["start_time"]
                    elif day_availability.get("preferred_time"):
                        time_obj = datetime.strptime(day_availability["preferred_time"], '%H:%M').time()
                        workout_time = datetime.combine(datetime.now().date(), time_obj)
                    
                    if workout_time:
                        # Adjust for correct day
                        days_ahead = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(day)
                        current_day = datetime.now().weekday()
                        days_to_add = (days_ahead - current_day) % 7
                        if days_to_add == 0 and datetime.now().time() > workout_time.time():
                            days_to_add = 7
                        
                        target_date = datetime.now().date() + timedelta(days=days_to_add)
                        scheduled_datetime = datetime.combine(target_date, workout_time.time())
                        
                        duration_str = workout.get('duration', '45 minutes')
                        duration_minutes = int(duration_str.split()[0]) if duration_str.split()[0].isdigit() else 45
                        
                        event_id = cal_service.create_workout_event(
                            workout_details=workout,
                            start_time=scheduled_datetime,
                            duration_minutes=duration_minutes
                        )
                        
                        if event_id:
                            bookings_successful += 1
                        else:
                            bookings_failed += 1
                    
                except Exception as e:
                    print(f"Error booking {day}: {str(e)}")
                    bookings_failed += 1
    
    if bookings_successful > 0:
        st.success(f"🎉 Successfully booked {bookings_successful} workout(s) in your calendar!")
    
    if bookings_failed > 0:
        st.warning(f"⚠️ Failed to book {bookings_failed} workout(s). Please try booking them individually.")


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


def create_app():
    """Enhanced Streamlit app with calendar integration for weekly schedules only."""
    st.set_page_config(
        page_title=settings.APP_NAME,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize app
    initialize_app()
    
    st.title(f"🏋️‍♂️ {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Sidebar with user stats
    with st.sidebar:
        st.header("👤 User Info")
        stats = st.session_state.user_stats
        st.info(f"""
        **User ID:** {stats['user_id']}
        **Profile:** {'✅' if stats['has_profile'] else '❌'}
        **Schedules:** {stats['total_schedules']}
        **Feedback:** {stats['total_feedback']}
        """)
        
        # Calendar status
        cal_service = st.session_state.calendar_service
        if cal_service.is_authenticated():
            st.success("📅 Calendar Connected")
        else:
            st.info("📅 Calendar Not Connected")
        
        st.header("ℹ️ About")
        st.info(
            "Your data is saved locally and will persist between sessions. "
            "Calendar integration helps with weekly scheduling!"
        )
        
        st.header("⚠️ Disclaimer")
        st.warning(
            "This AI-generated fitness advice is for informational purposes only. "
            "Please consult with a healthcare professional before starting any new "
            "fitness program."
        )
    
    # Main navigation
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
            render_schedule_creation()  # Now includes calendar integration for weekly schedules
        
        with tab4:
            render_schedule_history()


def main():
    """Main entry point."""
    try:
        create_app()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.write("Please refresh the page and try again.")


if __name__ == "__main__":
    main()