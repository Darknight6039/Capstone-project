# data/__init__.py
# This file marks the data directory as a Python package
# Can be empty or include data loading utilities
import os

# Define data paths
SKILLS_DB_PATH = os.path.join(os.path.dirname(__file__), "skills_database.json")
TEMPLATE_RESPONSES_PATH = os.path.join(os.path.dirname(__file__), "template_responses.json")
