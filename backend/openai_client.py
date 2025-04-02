# backend/openai_client.py

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Create a single client instance
client = OpenAI(api_key=api_key)

# Simple function to get the client
def get_openai_client():
    return client
