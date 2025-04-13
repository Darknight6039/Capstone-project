from backend.openai_client import get_openai_client
import json
import re

class ChatbotConversation:
    def __init__(self):
        """
        Initialize the chatbot conversation with GPT-4o optimization
        """
        self.client = get_openai_client()
        self.conversation_history = []
        
        # Enhanced system prompt for career guidance
        self.system_prompt = """You are CareerGPT, an expert AI career coach with access to:
        1. User's resume data (skills, experience, education)
        2. Current job market trends
        3. Latest hiring practices
        4. User's job match results
        
        Your capabilities:
        - Analyze resume-job fit
        - Suggest resume improvements
        - Provide interview preparation tips
        - Offer career path recommendations
        - Explain match scores and skill gaps"""
        
        self.reset_conversation()
        
    def reset_conversation(self):
        """Reset conversation while maintaining system context"""
        self.conversation_history = [
            {
                "role": "system", 
                "content": self.system_prompt
            }
        ]
        
    def update_resume_context(self, resume_data):
        """
        Update conversation with structured resume context
        
        Args:
            resume_data (dict): Parsed resume data
        """
        # Clear previous context
        self.conversation_history = [
            msg for msg in self.conversation_history 
            if not msg.get("metadata") == "resume_context"
        ]
        
        if resume_data:
            # Structure resume data for GPT-4o
            structured_resume = {
                "skills": resume_data.get('skills', []),
                "experience": [
                    f"{exp.get('title', '')} at {exp.get('company', '')} ({exp.get('duration', '')})"
                    for exp in resume_data.get('experience', [])[:3]
                ],
                "education": resume_data.get('education', []),
                "certifications": resume_data.get('certifications', [])
            }
            
            self.conversation_history.append({
                "role": "system",
                "content": f"RESUME_CONTEXT: {json.dumps(structured_resume)}",
                "metadata": "resume_context"
            })
            
    def _enhance_with_job_context(self, job_matches):
        """Add job match context to conversation"""
        if job_matches:
            top_3_matches = [
                f"{job['job_data']['title']} at {job['job_data']['company']} ({job['match_score']}% match)"
                for job in job_matches[:3]
            ]
            return f"TOP JOB MATCHES: {', '.join(top_3_matches)}"
        return ""

    def generate_response(self, message, job_matches=None):
        """
        Generate response with GPT-4o optimizations
        
        Args:
            message (str): User input
            job_matches (list): List of job matches
            
        Returns:
            str: Formatted response
        """
        try:
            # Prepare messages with context
            messages = self.conversation_history.copy()
            
            # Add job context if available
            if job_matches:
                messages.append({
                    "role": "system",
                    "content": self._enhance_with_job_context(job_matches)
                })
                
            messages.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                top_p=0.9,
                frequency_penalty=0.5,
                presence_penalty=0.3
            )
            
            # Process and format response
            raw_response = response.choices[0].message.content
            formatted_response = self._format_response(raw_response)
            
            # Maintain conversation history
            self.conversation_history.extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": formatted_response}
            ])
            
            return formatted_response
            
        except Exception as e:
            print(f"API Error: {str(e)}")
            return "I'm experiencing technical difficulties. Please try again later."

    def _format_response(self, text):
        """Format GPT-4o response for better readability"""
        # Convert markdown to streamlit-friendly format
        text = re.sub(r"\*\*(.*?)\*\*", r"**\1**", text)  # Preserve bold
        text = re.sub(r"\*(.*?)\*", r"*\1*", text)        # Preserve italics
        text = re.sub(r"^-\s+(.*)$", r"• \1", text, flags=re.MULTILINE)  # Bullet points
        return text

    def process_message(self, message, resume_data=None, job_matches=None, **kwargs):
        """
        Enhanced message processing with GPT-4o
        
        Args:
            message (str): User message
            resume_data (dict): Parsed resume data
            job_matches (list): Job matches from matching engine
            
        Returns:
            str: Formatted response
        """
        # Update contexts
        if resume_data:
            self.update_resume_context(resume_data)
            
        # Handle empty resume/job data queries
        if not resume_data and self._is_job_related(message):
            return self._handle_no_resume_case(message)
            
        return self.generate_response(message, job_matches)

    def _is_job_related(self, text):
        """Determine if message requires resume/job context"""
        job_keywords = [
            'resume', 'cv', 'job', 'career', 'application',
            'interview', 'skill gap', 'match score', 'hire'
        ]
        return any(keyword in text.lower() for keyword in job_keywords)

    def _handle_no_resume_case(self, message):
        """Handle queries without resume context"""
        temp_system = """You're a career coach. The user hasn't uploaded a resume yet.
        Respond to general career questions, but politely suggest uploading a resume
        for personalized advice when appropriate."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": temp_system},
                    {"role": "user", "content": message}
                ],
                temperature=0.5,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            return "I can help with general career advice. For personalized suggestions, please upload your resume first."
