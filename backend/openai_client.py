import os
from dotenv import load_dotenv
import streamlit as st

import streamlit as st

def get_openai_client():
    """Initialize and return the OpenAI client."""
    if "openai" in st.secrets:
        # Load API key from Streamlit secrets
        api_key = st.secrets["openai"]["api_key"]
    else:
        raise ValueError("OpenAI API key not found in Streamlit secrets.")
    
    # Set up OpenAI client
    import openai
    openai.api_key = api_key
    return openai
