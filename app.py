import os
import streamlit as st
from frontend.main import run_streamlit_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    # Set environment variables if needed
    # Note: Arbeitnow doesn't require an API key
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "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")
    
    # Run the Streamlit app
    run_streamlit_app()
