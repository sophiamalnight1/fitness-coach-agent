"""Streamlit UI for the AI Fitness Coach."""

import streamlit as st
from fitness_coach.core.coach import AIFitnessCoach
from fitness_coach.config.settings import settings


def render_create_plan_tab():
    """Render the create fitness plan tab."""
    st.header("Create Your Personalized Fitness Plan")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("Age", min_value=1, max_value=120, value=25)
    with col2:
        weight = st.number_input("Weight (kg)", min_value=1.0, value=70.0)
    with col3:
        height = st.number_input("Height (cm)", min_value=1.0, value=170.0)
    
    gender = st.radio("Gender", ["Male", "Female", "Other"])
    
    primary_goal = st.selectbox(
        "Primary Goal",
        ["Weight loss", "Muscle gain", "Endurance improvement", "General fitness"]
    )
    
    target_timeframe = st.selectbox(
        "Target Timeframe",
        ["3 months", "6 months", "1 year"]
    )
    
    workout_preferences = st.multiselect(
        "Workout Type Preferences",
        ["Cardio", "Strength training", "Yoga", "Pilates", "Flexibility exercises", "HIIT"]
    )
    
    workout_duration = st.slider(
        "Preferred Workout Duration (minutes)",
        min_value=15,
        max_value=120,
        step=15,
        value=45
    )
    
    workout_days = st.multiselect(
        "Preferred Workout Days",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )
    
    activity_level = st.radio(
        "Current Activity Level",
        ["Sedentary", "Lightly active", "Moderately active", "Highly active"]
    )
    
    health_conditions = st.text_area("Health Conditions or Injuries")
    dietary_preferences = st.text_area("Dietary Preferences (Optional)")
    
    if st.button("Create Fitness Plan", type="primary"):
        user_data = {
            "age": age,
            "weight": weight,
            "height": height,
            "gender": gender,
            "primary_goal": primary_goal,
            "target_timeframe": target_timeframe,
            "workout_preferences": workout_preferences,
            "workout_duration": workout_duration,
            "workout_days": workout_days,
            "activity_level": activity_level,
            "health_conditions": health_conditions,
            "dietary_preferences": dietary_preferences
        }
        
        with st.spinner("Generating your personalized fitness plan..."):
            messages = st.session_state.fitness_coach.run(user_data)
            st.session_state.last_plan = messages
            
        for message in messages:
            if hasattr(message, 'content'):
                st.write(f"**{message.__class__.__name__}:** {message.content}")


def render_update_plan_tab():
    """Render the update fitness plan tab."""
    st.header("Update Your Fitness Plan")
    
    if "last_plan" not in st.session_state:
        st.info("Please create a fitness plan first in the 'Create Fitness Plan' tab.")
        return
    
    feedback = st.text_area("Provide feedback about your current plan:")
    
    if st.button("Update Plan", type="primary"):
        if feedback:
            with st.spinner("Updating your fitness plan..."):
                messages = st.session_state.fitness_coach.run({"feedback": feedback})
                
            for message in messages:
                if hasattr(message, 'content'):
                    st.write(f"**{message.__class__.__name__}:** {message.content}")
        else:
            st.warning("Please provide some feedback before updating the plan.")


def create_app():
    """Create and configure the Streamlit application."""
    st.set_page_config(
        page_title=settings.APP_NAME,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title(f"{settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Sidebar with information
    with st.sidebar:
        st.header("About")
        st.info(
            "AI Fitness Coach helps you create personalized workout plans "
            "tailored to your goals, schedule, and preferences."
        )
        
        st.header("Disclaimer")
        st.warning(
            "This AI-generated fitness advice is for informational purposes only. "
            "Please consult with a healthcare professional before starting any new "
            "fitness program."
        )
    
    # Initialize session state
    if "fitness_coach" not in st.session_state:
        try:
            st.session_state.fitness_coach = AIFitnessCoach()
        except Exception as e:
            st.error(f"Error initializing AI Fitness Coach: {str(e)}")
            st.stop()
    
    # Main content tabs
    tab1, tab2 = st.tabs(["Create Fitness Plan", "Update Fitness Plan"])
    
    with tab1:
        render_create_plan_tab()
    
    with tab2:
        render_update_plan_tab()


def main():
    """Main entry point for the Streamlit application."""
    create_app()


if __name__ == "__main__":
    main()