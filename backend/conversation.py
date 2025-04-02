# backend/conversation.py

from backend.openai_client import get_openai_client
import json

class ChatbotConversation:
    def __init__(self):
        """
        Initialize the chatbot conversation.
        The OpenAI client is imported from a singleton instance.
        """
        self.client = get_openai_client()
        self.conversation_history = []
        
        # Add a system message to provide context
        self.conversation_history.append({
            "role": "system", 
            "content": "You are a career assistant. Help users with job searching, career advice, and resume improvement. When resume data is provided, refer to it in your responses."
        })
        
    def update_resume_context(self, resume_data):
        """
        Update the conversation with resume context
        
        Args:
            resume_data (dict): The parsed resume data
        """
        # Remove any previous resume context
        self.conversation_history = [msg for msg in self.conversation_history 
                                   if not msg.get("content", "").startswith("RESUME_DATA:")]
        
        # Add new resume context
        if resume_data:
            resume_context = f"RESUME_DATA: {json.dumps(resume_data)}"
            self.conversation_history.append({"role": "system", "content": resume_context})
    
    def generate_response(self, message):
        """
        Generate a response using the OpenAI API.
        
        Args:
            message (str): The user message to respond to
            
        Returns:
            str: The generated response
        """
        # Add the message to the conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Generate response using OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=self.conversation_history
        )
        
        # Extract and return the response text
        assistant_message = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
    
    # Method updated to support all necessary parameters
    def process_message(self, message, resume_data=None, job_matches=None, **kwargs):
        """
        Process a message and generate a contextual response
        
        Args:
            message (str): The user message to respond to
            resume_data (dict, optional): Resume data for context-aware responses
            job_matches (list, optional): Job matches for context-aware responses
            **kwargs: Any additional parameters that might be passed
            
        Returns:
            str: The generated response
        """
        # Update resume context if provided
        if resume_data:
            self.update_resume_context(resume_data)
            
        # Determine if the question is job-related
        job_related_keywords = ["job", "career", "work", "position", "employment", "hiring",
                               "skills", "interview", "resume", "application"]
        
        is_job_related = any(keyword in message.lower() for keyword in job_related_keywords)
        
        # Enrich the message with resume and job match context
        context = ""
        
        if resume_data:
            skills = resume_data.get('skills', [])
            if skills:
                context += f"Based on your resume skills: {', '.join(skills)}. "
        
        if job_matches:
            context += f"Considering your {len(job_matches)} job matches. "
            # Add more details about top matches
            if len(job_matches) > 0:
                top_match = job_matches[0]
                context += f"Your top match is {top_match['job_data']['title']} at {top_match['job_data']['company']} with {top_match['match_score']}% match. "
        
        # If job-related but no resume or job matches are available
        if is_job_related and not resume_data and not job_matches:
            system_instruction = """
            You are a career assistant who provides helpful advice about job searching, careers,
            and professional development. If the user asks about specific job matches or their resume,
            kindly explain that you don't have that information yet, but you can still provide
            general career advice and guidance.
            """
            
            temp_messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": message}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=temp_messages
            )
            
            assistant_message = response.choices[0].message.content
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        
        # Add context to the message if it exists
        if context:
            enhanced_message = context + message
            return self.generate_response(enhanced_message)
        
        # Default behavior without additional context
        return self.generate_response(message)
