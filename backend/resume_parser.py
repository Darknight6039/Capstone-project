import json
import re
import streamlit as st
from backend.openai_client import get_openai_client

class ResumeParser:
    def __init__(self):
        """Initialize the resume parser."""
        self.client = get_openai_client()

    def parse_resume(self, resume_text):
        """
        Parse a resume using OpenAI.
        
        Args:
            resume_text (str): The text content of the resume
            
        Returns:
            str: JSON string containing structured resume information
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
                    You are a resume parsing expert. Extract structured information from this resume into VALID JSON format:
                    
                    {
                      "personal_info": {"name": "", "email": "", "phone": "", "linkedin": ""},
                      "skills": ["skill1", "skill2"],
                      "experience": [{"company": "", "title": "", "duration": "", "description": ""}],
                      "education": [{"institution": "", "degree": "", "field": "", "year": ""}],
                      "languages": [{"language": "", "proficiency": ""}],
                      "certifications": []
                    }
                    
                    IMPORTANT: Return ONLY valid JSON with no explanations or additional text.
                    """},
                    {"role": "user", "content": resume_text}
                ],
                temperature=0.1  # Lower temperature for more structured output
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Error calling OpenAI API: {str(e)}")
            return json.dumps(self._create_empty_structure())

    def parse_document(self, resume_text, file_path=None):
        """
        Parse resume document and extract structured information.
        
        Args:
            resume_text (str): The text content of the resume
            
        Returns:
            dict: Structured resume information
        """
        try:
            raw_result = self.parse_resume(resume_text)
            cleaned_json = self._clean_json_response(raw_result)
            parsed_data = json.loads(cleaned_json)
            
            st.session_state.resume_data = parsed_data
            
            return parsed_data
            
        except Exception as e:
            st.error(f"Error processing resume: {str(e)}")
            return self._create_empty_structure()

    def _clean_json_response(self, text):
        """
        Clean the JSON response to handle special objects and formatting issues.
        
        Args:
            text (str): Raw JSON text from API
            
        Returns:
            str: Cleaned JSON string
        """
        if not isinstance(text, str):
            return json.dumps(self._create_empty_structure())
            
        text = re.sub(r'\[\s*\.\.\.\s*\]', '[]', text)  # Replace [...] with []
        text = re.sub(r'"\.\.\."|\'\.\.\.\'', '""', text)  # Replace ellipsis with empty strings
        
        json_match = re.search(r'({[\s\S]*})', text)
        if json_match:
            text = json_match.group(1)
            
        return text

    def _create_empty_structure(self):
        """Create a fallback empty structure."""
        return {
            "personal_info": {"name": "", "email": "", "phone": "", "linkedin": ""},
            "skills": ["Erreur d'analyse"],
            "experience": [{"company": "Erreur technique", "title": "Veuillez réessayer"}],
            "education": [],
            "languages": [],
            "certifications": []
        }
