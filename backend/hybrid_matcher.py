import asyncio
from backend.matcher import JobMatcher
from backend.phi3_matcher import Phi3JobMatcher
from backend.openai_client import get_openai_client
import json

class HybridJobMatcher:
    def __init__(self):
        self.traditional_matcher = JobMatcher()
        self.phi3_matcher = Phi3JobMatcher()
        self.openai_client = get_openai_client()
        
    async def calculate_match_score(self, resume_data, job_data):
        """
        Hybrid matching approach:
        1. Get fast match score from Phi-3
        2. For high-potential matches (>60%), enhance with GPT-4o-mini
        """
        # Step 1: Get Phi-3 match score
        phi3_result = await self.phi3_matcher.calculate_match_score(resume_data, job_data)
        match_score = phi3_result["score"]
        
        # Step 2: For promising matches, enhance with GPT-4o-mini
        if match_score >= 60:
            # Format the data for GPT-4o-mini
            resume_skills = ", ".join(resume_data.get("skills", []))
            job_skills = ", ".join(job_data.get("required_skills", []))
            
            prompt = f"""
            Analyze the match between a candidate and job posting:
            
            Resume skills: {resume_skills}
            Job title: {job_data.get('title', '')}
            Required skills: {job_skills}
            
            Phi-3 gave this match a score of {match_score}%.
            
            Provide:
            1. A refined match score (0-100)
            2. Key strengths (3 points)
            3. Missing skills to develop (if any)
            
            Format as JSON with keys: score, strengths, missing_skills
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert job matching assistant."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            try:
                gpt_result = json.loads(response.choices[0].message.content)
                
                # Combine results, preferring GPT-4o-mini's assessment
                return {
                    "score": gpt_result.get("score", match_score),
                    "details": {
                        "matched_skills": phi3_result["details"]["matched_skills"],
                        "strengths": gpt_result.get("strengths", []),
                        "missing_skills": gpt_result.get("missing_skills", []),
                        "phi3_analysis": phi3_result["details"].get("explanation", "")
                    }
                }
            except:
                # Fallback to Phi-3 result if GPT-4o-mini response isn't valid
                return phi3_result
        
        # For lower matches, just return the Phi-3 result
        return phi3_result
