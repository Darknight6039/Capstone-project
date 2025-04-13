import streamlit as st
import os
from dotenv import load_dotenv
from frontend.main import run_streamlit_app

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    # Check if OPENAI_API_KEY exists
    api_key = os.getenv("OPENAI_API_KEY")  # Corrected syntax
    if not api_key:
        st.error("🔑 OpenAI API key not found. Please check your .env file.")
        st.stop()
    
    # Run the Streamlit app
    run_streamlit_app()
