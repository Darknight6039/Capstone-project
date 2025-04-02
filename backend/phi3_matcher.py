import asyncio
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import re

class Phi3JobMatcher:
    def __init__(self):
        # Load your fine-tuned model
        self.tokenizer = AutoTokenizer.from_pretrained("./phi3-cv-finetuned", trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            "./phi3-cv-finetuned",
            torch_dtype="auto",
            trust_remote_code=True
        )
        
    async def calculate_match_score(self, resume_data, job_data):
        """Calculate match score between resume and job using fine-tuned Phi-3"""
        # Format skills for better prompting
        resume_skills = ", ".join(resume_data.get("skills", []))
        job_skills = ", ".join(job_data.get("required_skills", []))
        
        # Create prompt for the model
        prompt = f"""<|user|>
        Calculate a match percentage between this candidate's resume and job posting.
        
        Resume Skills: {resume_skills}
        
        Job Title: {job_data.get('title', '')}
        Required Skills: {job_skills}
        
        Provide a match percentage (0-100) and brief explanation.
        <|assistant|>
        """
        
        # Generate response from the model
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            inputs.input_ids,
            max_new_tokens=256,
            temperature=0.1
        )
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract match percentage from response
        match_pattern = re.search(r'(\d+)%', response)
        match_score = int(match_pattern.group(1)) if match_pattern else 50
        
        # Extract matched skills
        matched_skills = []
        for skill in resume_data.get("skills", []):
            if skill.lower() in [s.lower() for s in job_data.get("required_skills", [])]:
                matched_skills.append(skill)
        
        return {
            "score": match_score,
            "details": {
                "matched_skills": matched_skills,
                "explanation": response
            }
        }
