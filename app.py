import os
import streamlit as st
from dotenv import load_dotenv
from frontend.main import run_streamlit_app

# Load environment variables
load_dotenv()

# Main application entry point
if __name__ == "__main__":
    try:
        # Run the Streamlit app
        run_streamlit_app()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.stop()
