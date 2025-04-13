# backend/openai_resume_extractor.py

import os
import tempfile
import PyPDF2
import docx2txt
from backend.openai_client import get_openai_client
import json

class OpenAIResumeExtractor:
    def __init__(self):
        """Initialize the OpenAI-based resume extraction agent."""
        self.client = get_openai_client()
    
    def extract_from_file(self, file_path):
        """
        Extract information from a resume file using OpenAI.
        
        Args:
            file_path (str): Path to the resume file
            
        Returns:
            dict: Extracted resume information
        """
        try:
            # Extract text from file
            text = self._extract_text_from_file(file_path)
            
            # Use OpenAI to extract structured information
            return self._extract_with_openai(text)
        except Exception as e:
            print(f"Error extracting resume data: {str(e)}")
            return {"error": str(e)}
    
    def extract_from_uploaded_file(self, uploaded_file):
        """
        Extract information from a Streamlit uploaded file.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            dict: Extracted resume information
        """
        try:
            # Create a temporary file to save the uploaded content
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_path = temp_file.name
            
            # Extract data from the temporary file
            data = self.extract_from_file(temp_path)
            
            # Clean up the temporary file
            os.unlink(temp_path)
            
            return data
        except Exception as e:
            print(f"Error processing uploaded file: {str(e)}")
            return {"error": str(e)}
    
    def _extract_text_from_file(self, file_path):
        """Extract text from PDF or DOCX file."""
        if file_path.lower().endswith('.pdf'):
            return self._extract_from_pdf(file_path)
        elif file_path.lower().endswith(('.docx', '.doc')):
            return self._extract_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format. Please use PDF or DOCX.")
    
    def _extract_from_pdf(self, file_path):
        """Extract text from PDF file."""
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_from_docx(self, file_path):
        """Extract text from DOCX file."""
        return docx2txt.process(file_path)
    
    def _extract_with_openai(self, resume_text):
        """Extract structured information from resume text using OpenAI."""
        try:
            prompt = """
            Extract the following information from this resume in JSON format:
            - personal_info:
              - name: Full name of the candidate
              - email: Email address
              - phone: Phone number
              - linkedin: LinkedIn profile (if present)
              - github: GitHub profile (if present)
            - skills: List of technical and soft skills
            - experience: List of professional experiences, each with:
              - company: Company name
              - title: Job title
              - duration: Duration (e.g., "2019-2022")
              - description: Description of responsibilities
            - education: List of education entries, each with:
              - institution: Name of the institution
              - degree: Degree obtained
              - field: Field of study
              - year: Year of completion
            - languages: List of languages spoken with proficiency level
            - certifications: List of certifications obtained
            
            Return ONLY the JSON, with no other text.
            
            RESUME:
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an assistant specialized in extracting information from resumes."},
                    {"role": "user", "content": prompt + resume_text}
                ],
                temperature=0.1
            )  # Added missing closing parenthesis
            
            result = response.choices[0].message.content
            
            # Parse the response as JSON
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw result
                return {"raw_content": result}
                
        except Exception as e:
            print(f"Error extracting with OpenAI: {str(e)}")
            return {"error": str(e)}