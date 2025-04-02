# backend/resume_parser.py

from backend.openai_client import get_openai_client
import json
import streamlit as st
import re

class ResumeParser:
    def __init__(self):
        """
        Initialize the resume parser.
        """
        self.client = get_openai_client()
    
    def parse_resume(self, resume_text):
        """
        Parse a resume using OpenAI.
        
        Args:
            resume_text (str): The text content of the resume
            
        Returns:
            dict: Structured resume information
        """
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """
                You are a resume parsing expert. Extract the following information from the resume into VALID JSON format:
                
                {
                  "personal_info": {"name": "", "email": "", "phone": "", "linkedin": ""},
                  "skills": ["skill1", "skill2", ...],
                  "experience": [{"company": "", "title": "", "duration": "", "description": ""}],
                  "education": [{"institution": "", "degree": "", "field": "", "year": ""}],
                  "languages": [{"language": "", "proficiency": ""}],
                  "certifications": ["cert1", "cert2", ...]
                }
                
                IMPORTANT: Return ONLY valid JSON with no explanations or additional text. Ensure all fields are present even if empty.
                """},
                {"role": "user", "content": resume_text}
            ],
            temperature=0.1  # Lower temperature for more structured output
        )  # Added missing closing parenthesis
        
        # Process and return the parsed resume data
        return response.choices[0].message.content
    
    def parse_document(self, resume_text, file_path=None):
        """
        Alias for parse_resume
        
        Args:
            resume_text (str): The text content of the resume
            file_path (str, optional): Path to the resume file (ignored)
            
        Returns:
            dict: Structured resume information
        """
        result = self.parse_resume(resume_text)
        
        try:
            # Try to clean the result before parsing JSON
            # Sometimes GPT adds explanations before/after the JSON
            if isinstance(result, str):
                # Try to find JSON block
                json_match = re.search(r'({[\s\S]*})', result)
                if json_match:
                    result = json_match.group(1)
                parsed_data = json.loads(result)
            else:
                parsed_data = result
            
            # Store in session state
            st.session_state.resume_data = parsed_data
            
            # Update conversation context with new resume data
            try:
                from backend.conversation import ChatbotConversation
                conversation = ChatbotConversation()
                conversation.update_resume_context(parsed_data)
            except ImportError:
                # Handle case where ChatbotConversation might not be available yet
                pass
            
            return parsed_data
        except Exception as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Raw content: {result}")
            # Create a basic structured format to prevent display errors
            raw_result = {
                "raw_content": result,
                "error": str(e),
                "skills": ["Parsing Failed"],
                "experience": [{"title": "Parsing Failed", "company": "Please try again", "duration": ""}]
            }
            st.session_state.resume_data = raw_result
            return raw_result
