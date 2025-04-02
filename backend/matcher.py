import openai
import os
import json
import asyncio
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from backend.openai_client import get_openai_client

class JobMatcher:
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    async def calculate_match_score(self, resume_data, job_data):
        """Calculate overall match percentage"""
        # Check if we have valid data
        if not resume_data or not job_data:
            return {"score": 0, "details": {"matched_skills": [], "missing_skills": [], "comments": "No resume data provided."}}
        
        # Compare resume and job requirements
        skills_match = await self.evaluate_skills_match(
            resume_data.get("skills", []),
            job_data.get("required_skills", [])
        )
        
        experience_match = await self.evaluate_experience_match(
            resume_data.get("experience", []),
            job_data.get("experience_required", "")
        )
        
        education_match = await self.evaluate_education_match(
            resume_data.get("education", []),
            job_data.get("education_required", "")
        )
        
        # Calculate overall score (weighted average)
        weights = {
            "skills": 0.5,
            "experience": 0.3,
            "education": 0.2
        }
        
        # Use OpenAI for more nuanced matching
        client = get_openai_client()
        profile_summary = f"""
        Skills: {', '.join(resume_data.get('skills', [])[:10])}
        Experience: {len(resume_data.get('experience', []))} positions
        Education: {', '.join([f"{edu.get('degree', '')} in {edu.get('field', '')}" for edu in resume_data.get('education', [])])}
        """
        
        job_summary = f"""
        Title: {job_data.get('title', 'Unknown')}
        Company: {job_data.get('company', 'Unknown')}
        Required Skills: {', '.join(job_data.get('required_skills', []))}
        Experience Required: {job_data.get('experience_required', 'Not specified')}
        Education Required: {job_data.get('education_required', 'Not specified')}
        """
        
        prompt = f"""
        Analyze the match between a candidate's profile and a job posting.
        
        Resume summary:
        {profile_summary}
        
        Job summary:
        {job_summary}
        
        Calculate a match score percentage (0-100) based on how well the candidate's skills, 
        experience, and education align with the job requirements.
        
        Format your response as a single number representing the percentage match score.
        If the candidate seems highly qualified, score above 80%.
        If there's a moderate match with some gaps, score 60-80%.
        If there's a weak match with significant gaps, score 30-60%.
        If there's a poor match, score below 30%.
        """
        
        try:
            ai_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI assistant specialized in job matching."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Extract match score from response
            ai_score_text = ai_response.choices[0].message.content.strip()
            try:
                # Try to extract a number from the response
                import re
                ai_score_match = re.search(r'(\d+)', ai_score_text)
                if ai_score_match:
                    ai_score = int(ai_score_match.group(1))
                    if 0 <= ai_score <= 100:
                        # Use AI score if it's valid
                        score = ai_score
                    else:
                        # Fallback to calculated score
                        score = (
                            skills_match.get("score", 0) * weights["skills"] +
                            experience_match.get("relevance", 0) * weights["experience"] +
                            (education_match.get("degree_match", 0) + education_match.get("field_match", 0)) * weights["education"] / 2
                        ) * 100
                else:
                    # Fallback to calculated score
                    score = (
                        skills_match.get("score", 0) * weights["skills"] +
                        experience_match.get("relevance", 0) * weights["experience"] +
                        (education_match.get("degree_match", 0) + education_match.get("field_match", 0)) * weights["education"] / 2
                    ) * 100
            except Exception:
                # Fallback to calculated score
                score = (
                    skills_match.get("score", 0) * weights["skills"] +
                    experience_match.get("relevance", 0) * weights["experience"] +
                    (education_match.get("degree_match", 0) + education_match.get("field_match", 0)) * weights["education"] / 2
                ) * 100
        except Exception:
            # If OpenAI call fails, use the original calculation
            score = (
                skills_match.get("score", 0) * weights["skills"] +
                experience_match.get("relevance", 0) * weights["experience"] +
                (education_match.get("degree_match", 0) + education_match.get("field_match", 0)) * weights["education"] / 2
            ) * 100
        
        # Generate an overall analysis
        overall = await self.generate_match_report(resume_data, job_data)
        
        return {
            "score": round(score),
            "details": {
                "matched_skills": skills_match.get("matched_skills", []),
                "missing_skills": skills_match.get("missing_skills", []),
                "skills_match": skills_match,
                "experience_match": experience_match,
                "education_match": education_match,
                "overall": overall
            }
        }
    
    # The rest of the methods remain unchanged
    async def evaluate_skills_match(self, candidate_skills, required_skills):
        """Evaluate skills compatibility"""
        if not required_skills:
            return {"score": 0.5, "matched_skills": [], "missing_skills": [], "comments": "No skills requirements specified for this job."}
        
        # Convert to lowercase for better matching
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        # Find matched and missing skills
        matched_skills = []
        missing_skills = []
        for skill in required_skills:
            if skill.lower() in candidate_skills_lower:
                matched_skills.append(skill)
            else:
                # Check for similar skills (could use fuzzy matching or embeddings in a more advanced version)
                similar_found = False
                for candidate_skill in candidate_skills:
                    if skill.lower() in candidate_skill.lower() or candidate_skill.lower() in skill.lower():
                        matched_skills.append(skill)
                        similar_found = True
                        break
                if not similar_found:
                    missing_skills.append(skill)
        
        # Calculate score based on matched percentage
        if not required_skills:
            score = 0.5  # Neutral score if no skills are required
        else:
            score = len(matched_skills) / len(required_skills)
        
        # Use OpenAI to analyze skills match and provide comments
        prompt = f"""
        Analyze the match between a candidate's skills and job requirements:
        Candidate skills: {', '.join(candidate_skills)}
        Required skills: {', '.join(required_skills)}
        Matched skills: {', '.join(matched_skills)}
        Missing skills: {', '.join(missing_skills)}
        
        Analyze the skills match and provide insights about:
        1. How well the candidate's skills align with the job requirements
        2. What are the most important missing skills (if any)
        3. Whether the candidate has additional valuable skills for this role
        
        Provide your analysis in 3-4 sentences.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI assistant specializing in job matching analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=OPENAI_TEMPERATURE
            )
            
            comments = response.choices[0].message.content.strip()
        except Exception as e:
            comments = f"Skills analysis: The candidate matches {len(matched_skills)} out of {len(required_skills)} required skills. {len(missing_skills)} required skills are missing."
        
        return {
            "score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "comments": comments
        }
    
    # Keeping existing methods for experience and education match 
    async def evaluate_experience_match(self, candidate_experience, job_experience_reqs):
        """Evaluate experience compatibility"""
        if not candidate_experience or not job_experience_reqs:
            return {"relevance": 0.5, "duration_match": 0.5, "comments": "Insufficient information to evaluate experience match."}
        
        # Format candidate experience for analysis
        experience_text = ""
        for exp in candidate_experience:
            experience_text += f"- {exp.get('title', 'Unknown')} at {exp.get('company', 'Unknown')}, {exp.get('duration', 'Unknown duration')}\n"
        
        # Use OpenAI to analyze experience match
        prompt = f"""
        Analyze how well a candidate's experience matches job requirements:
        
        Candidate experience:
        {experience_text}
        
        Job experience requirements:
        {job_experience_reqs}
        
        Provide a detailed analysis with:
        1. A relevance score (0.0 to 1.0) representing how relevant the candidate's experience is to the job requirements
        2. A duration match score (0.0 to 1.0) representing if the candidate has sufficient experience duration
        3. A brief analysis of the experience match in 2-3 sentences
        
        Format your response as a JSON object with the following structure:
        {{
            "relevance": 0.75,
            "duration_match": 0.8,
            "comments": "Your analysis here..."
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI assistant specializing in job matching analysis. Respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=OPENAI_TEMPERATURE
            )
            
            result = json.loads(response.choices[0].message.content.strip())
        except Exception:
            # Fallback if JSON parsing fails
            result = {
                "relevance": 0.5,
                "duration_match": 0.5,
                "comments": "Unable to analyze experience match due to insufficient or unstructured data."
            }
        
        return result
    
    async def evaluate_education_match(self, candidate_education, job_education_reqs):
        """Evaluate education compatibility"""
        if not candidate_education or not job_education_reqs:
            return {"degree_match": 0.5, "field_match": 0.5, "comments": "Insufficient information to evaluate education match."}
        
        # Format candidate education for analysis
        education_text = ""
        for edu in candidate_education:
            education_text += f"- {edu.get('degree', 'Unknown degree')} in {edu.get('field', 'Unknown field')} from {edu.get('institution', 'Unknown institution')}, {edu.get('year', 'Unknown year')}\n"
        
        # Use OpenAI to analyze education match
        prompt = f"""
        Analyze how well a candidate's education matches job requirements:
        
        Candidate education:
        {education_text}
        
        Job education requirements:
        {job_education_reqs}
        
        Provide a detailed analysis with:
        1. A degree match score (0.0 to 1.0) representing how well the candidate's degree level meets the requirements
        2. A field match score (0.0 to 1.0) representing how relevant the candidate's field of study is to the job
        3. A brief analysis of the education match in 2-3 sentences
        
        Format your response as a JSON object with the following structure:
        {{
            "degree_match": 0.75,
            "field_match": 0.8,
            "comments": "Your analysis here..."
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI assistant specializing in job matching analysis. Respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=OPENAI_TEMPERATURE
            )
            
            result = json.loads(response.choices[0].message.content.strip())
        except Exception:
            # Fallback if JSON parsing fails
            result = {
                "degree_match": 0.5,
                "field_match": 0.5,
                "comments": "Unable to analyze education match due to insufficient or unstructured data."
            }
        
        return result
    
    async def generate_match_report(self, resume_data, job_data):
        """Create comprehensive match analysis"""
        # Format the data for analysis
        resume_summary = f"""
        Skills: {', '.join(resume_data.get('skills', [])[:10])}
        Experience: {len(resume_data.get('experience', []))} positions
        Education: {', '.join([f"{edu.get('degree', '')} in {edu.get('field', '')}" for edu in resume_data.get('education', [])])}
        """
        
        job_summary = f"""
        Title: {job_data.get('title', 'Unknown')}
        Company: {job_data.get('company', 'Unknown')}
        Required Skills: {', '.join(job_data.get('required_skills', []))}
        Experience Required: {job_data.get('experience_required', 'Not specified')}
        Education Required: {job_data.get('education_required', 'Not specified')}
        """
        
        # Use OpenAI to generate overall match report
        prompt = f"""
        Analyze the overall match between a candidate's profile and a job posting:
        
        Resume summary:
        {resume_summary}
        
        Job summary:
        {job_summary}
        
        Provide an analysis with:
        1. Three key strengths of the candidate for this position
        2. Three areas where the candidate could improve to better match the job
        3. A brief overall summary of the match (2-3 sentences)
        
        Format your response as a JSON object with the following structure:
        {{
            "strengths": ["strength 1", "strength 2", "strength 3"],
            "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
            "summary": "Your summary here..."
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI assistant specializing in job matching analysis. Respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=OPENAI_TEMPERATURE
            )
            
            result = json.loads(response.choices[0].message.content.strip())
        except Exception:
            # Fallback if JSON parsing fails
            result = {
                "strengths": ["Candidate has relevant skills", "Candidate has education in the field", "Candidate has work experience"],
                "weaknesses": ["Could improve specific technical skills", "Could gain more industry experience", "Could obtain additional certifications"],
                "summary": "The candidate shows basic qualifications for the role but may need additional development in specific areas."
            }
        
        return result
