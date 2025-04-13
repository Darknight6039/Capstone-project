import os
from dotenv import load_dotenv
import streamlit as st
# Load environment variables from .env file
load_dotenv()

# API Keys
ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"
# No API key needed for Arbeitnow

# Use environment variable and fallback to config only for development
# Gestion des secrets Streamlit ou fallback sur .env
def get_openai_api_key():
    if "openai" in st.secrets:
        return st.secrets["openai"]["api_key"]
    return os.getenv("OPENAI_API_KEY")

# Configuration settings
OPENAI_API_KEY = get_openai_api_key()
MAX_JOBS_TO_FETCH = 25
# OpenAI Settings
OPENAI_MODEL = "gpt-4o-mini"  # Can be replaced with gpt-3.5-turbo for cost saving
OPENAI_TEMPERATURE = 0.0  # Lower for more consistent, deterministic outputs

# Application Settings
MAX_JOBS_TO_FETCH = 25
DEFAULT_LOCATION = "Paris, France"
DEFAULT_JOB_KEYWORDS = "Data Scientist"

# File Storage
UPLOADS_FOLDER = "data/user_data/uploads/"
SKILLS_DATABASE_PATH = "data/skills_database.json"
