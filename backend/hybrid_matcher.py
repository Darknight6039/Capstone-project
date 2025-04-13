import asyncio
from backend.matcher import JobMatcher
from backend.gpt4o_matcher import GPT4oMatcher

class HybridJobMatcher:
    def __init__(self):
        self.traditional_matcher = JobMatcher()
        self.gpt4o_matcher = GPT4oMatcher()
        
    async def calculate_match_score(self, resume_data, job_data):
        """
        Hybrid matching approach:
        1. Get fast match score from traditional matcher
        2. For high-potential matches (>60%), enhance with GPT-4o
        """
        # Step 1: Get traditional match score
        trad_result = await self.traditional_matcher.calculate_match_score(resume_data, job_data)
        match_score = trad_result["score"]
        
        # Step 2: For promising matches, enhance with GPT-4o
        if match_score >= 80:
            gpt_result = await self.gpt4o_matcher.calculate_match_score(resume_data, job_data)
            
            # Combine results
            return {
                "score": gpt_result["score"],
                "details": {
                    "matched_skills": gpt_result["details"]["matched_skills"],
                    "missing_skills": gpt_result["details"]["missing_skills"],
                    "explanation": gpt_result["details"]["explanation"],
                    "traditional_score": match_score
                }
            }
        
        # For lower matches, just return the traditional result
        return trad_result
