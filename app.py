"""Entry point for the AI Fitness Coach Streamlit application."""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fitness_coach.ui.streamlit_app import main

if __name__ == "__main__":
    main()