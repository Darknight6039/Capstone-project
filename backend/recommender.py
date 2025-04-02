import openai
import os
import json
import asyncio
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE

class CandidateRecommender:
    def __init__(self):
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

    async def generate_improvement_suggestions(self, resume_data, job_data, match_results):
        """Generate personalized suggestions to improve candidacy"""
        # Format the data for analysis
        skills_match = match_results.get("skills_match", {})
        missing_skills = skills_match.get("missing_skills", [])
        
        # Format resume summary
        resume_summary = f"""
        Skills: {', '.join(resume_data.get('skills', [])[:15])}
        Experience:
        {self._format_experience(resume_data.get('experience', []))}
        Education:
        {self._format_education(resume_data.get('education', []))}
        """
        
        # Format job summary
        job_summary = f"""
        Title: {job_data.get('title', 'Unknown')}
        Company: {job_data.get('company', 'Unknown')}
        Required Skills: {', '.join(job_data.get('required_skills', []))}
        Job Description: {job_data.get('description', 'Not provided')}
        Experience Required: {job_data.get('experience_required', 'Not specified')}
        Education Required: {job_data.get('education_required', 'Not specified')}
        """
        
        # Format match results summary
        match_summary = f"""
        Overall Match Score: {match_results.get('score', 0)}%
        Skills Match:
        - Matched Skills: {', '.join(skills_match.get('matched_skills', []))}
        - Missing Skills: {', '.join(missing_skills)}
        Experience Analysis: {match_results.get('experience_match', {}).get('comments', 'Not analyzed')}
        Education Analysis: {match_results.get('education_match', {}).get('comments', 'Not analyzed')}
        """
        
        # Use OpenAI to generate improvement suggestions
        prompt = f"""
        As a career advisor, provide personalized recommendations to help a candidate improve their chances for a specific job position.
        
        Resume Summary:
        {resume_summary}
        
        Job Summary:
        {job_summary}
        
        Match Analysis:
        {match_summary}
        
        Provide detailed recommendations in the following areas:
        1. Skills to develop (focus on the most important missing skills)
        2. Resume improvements (specific sections/points to add or emphasize)
        3. Strategies to stand out from other candidates (unique approaches for this specific role)
        4. Potential interview questions and how to prepare for them
        
        Format your response as a JSON object with the following structure:
        {{
            "skills_to_develop": [
                {{"skill": "Skill name", "reason": "Why this skill is important and how to develop it"}}
            ],
            "resume_improvements": [
                "Specific suggestion 1",
                "Specific suggestion 2"
            ],
            "differentiation_strategies": [
                "Strategy 1",
                "Strategy 2"
            ],
            "potential_questions": [
                {{"question": "Example question?", "approach": "How to approach answering this question"}}
            ]
        }}
        
        Provide 3-5 items for each category.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI career advisor specializing in personalized job matching recommendations. Respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2  # Slightly higher temperature for more diverse suggestions
            )
            
            result = json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            # Fallback if JSON parsing fails
            result = {
                "skills_to_develop": [
                    {"skill": missing_skills[0] if missing_skills else "Relevant technical skill",
                     "reason": "This skill appears in the job requirements and would strengthen your application."}
                ],
                "resume_improvements": [
                    "Highlight projects relevant to this specific industry",
                    "Quantify achievements with metrics and results"
                ],
                "differentiation_strategies": [
                    "Research the company thoroughly and mention specific initiatives in your application",
                    "Prepare a portfolio of relevant work samples"
                ],
                "potential_questions": [
                    {"question": "Tell me about your experience with similar roles",
                     "approach": "Focus on relevant projects and achievements that align with this job's requirements"}
                ]
            }
            
        return result

    async def identify_skill_gaps(self, candidate_skills, required_skills):
        """Identify missing skills and learning opportunities"""
        # Convert to lowercase for better matching
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        # Find missing skills
        missing_skills = []
        for skill in required_skills:
            if skill.lower() not in candidate_skills_lower:
                missing_skills.append(skill)
                
        if not missing_skills:
            return {
                "missing_skills": [],
                "learning_resources": [],
                "priority": "You already have all the required skills for this position."
            }
            
        # Use OpenAI to recommend learning resources and prioritize skills
        prompt = f"""
        A job candidate is missing these skills required for a position:
        {', '.join(missing_skills)}
        
        The candidate already has these skills:
        {', '.join(candidate_skills)}
        
        For each missing skill, recommend:
        1. How important this skill is for the role (high/medium/low priority)
        2. Specific resources to learn this skill (courses, books, websites, etc.)
        3. Estimated time needed to develop a basic proficiency
        
        Format your response as a JSON object with the following structure:
        {{
            "missing_skills": [
                {{
                    "skill": "Skill name",
                    "priority": "high/medium/low",
                    "resources": [
                        "Specific resource 1",
                        "Specific resource 2"
                    ],
                    "time_estimate": "Estimated time to learn (e.g., '2-3 weeks')"
                }}
            ],
            "learning_plan": "A brief suggestion of which skills to learn first and why"
        }}
        
        Include all missing skills in your response.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI career advisor specializing in skill development recommendations. Respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            # Fallback if JSON parsing fails
            result = {
                "missing_skills": [
                    {
                        "skill": skill,
                        "priority": "medium",
                        "resources": [
                            "Online courses on platforms like Coursera or Udemy",
                            "YouTube tutorials and documentation"
                        ],
                        "time_estimate": "4-8 weeks depending on prior experience"
                    } for skill in missing_skills[:3]  # Include up to 3 skills in fallback
                ],
                "learning_plan": "Focus on the most frequently mentioned skills in the job description first."
            }
            
        return result

    async def suggest_resume_improvements(self, resume_data, job_data):
        """Suggest specific resume improvements"""
        # Format the data for analysis
        resume_summary = f"""
        Skills: {', '.join(resume_data.get('skills', [])[:15])}
        Experience:
        {self._format_experience(resume_data.get('experience', []))}
        Education:
        {self._format_education(resume_data.get('education', []))}
        """
        
        # Format job summary
        job_summary = f"""
        Title: {job_data.get('title', 'Unknown')}
        Company: {job_data.get('company', 'Unknown')}
        Required Skills: {', '.join(job_data.get('required_skills', []))}
        Job Description: {job_data.get('description', 'Not provided')[:500]}...
        """
        
        # Use OpenAI to suggest resume improvements
        prompt = f"""
        As a resume expert, suggest specific improvements to make this resume more effective for this specific job:
        
        Resume Summary:
        {resume_summary}
        
        Target Job:
        {job_summary}
        
        Provide detailed recommendations on:
        1. Content improvements (what to add, remove, or modify)
        2. Formatting suggestions
        3. Keywords to include for ATS optimization
        4. How to better highlight relevant experience
        
        Format your response as a JSON object with the following structure:
        {{
            "content_improvements": ["suggestion 1", "suggestion 2", ...],
            "formatting_suggestions": ["suggestion 1", "suggestion 2", ...],
            "keywords": ["keyword 1", "keyword 2", ...],
            "highlight_experience": ["suggestion 1", "suggestion 2", ...]
        }}
        
        Provide 3-5 items for each category.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI resume expert. Respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            # Fallback if JSON parsing fails
            result = {
                "content_improvements": [
                    "Add a tailored professional summary highlighting relevant experience",
                    "Include metrics and achievements in your experience section",
                    "List relevant projects with outcomes"
                ],
                "formatting_suggestions": [
                    "Use bullet points for better readability",
                    "Ensure consistent formatting throughout",
                    "Limit resume to 1-2 pages"
                ],
                "keywords": job_data.get("required_skills", ["relevant", "skills", "experience"]),
                "highlight_experience": [
                    "Emphasize roles most relevant to this position",
                    "Quantify achievements with numbers and percentages",
                    "Focus on results rather than responsibilities"
                ]
            }
            
        return result

    async def generate_interview_tips(self, resume_data, job_data):
        """Provide job-specific interview preparation"""
        # Format job summary
        job_summary = f"""
        Title: {job_data.get('title', 'Unknown')}
        Company: {job_data.get('company', 'Unknown')}
        Required Skills: {', '.join(job_data.get('required_skills', []))}
        Job Description: {job_data.get('description', 'Not provided')[:500]}...
        """
        
        # Format candidate summary
        candidate_summary = f"""
        Key Skills: {', '.join(resume_data.get('skills', [])[:10])}
        Experience in: {', '.join([exp.get('title', 'Unknown role') for exp in resume_data.get('experience', [])])}
        """
        
        # Use OpenAI to generate interview tips
        prompt = f"""
        As an interview coach, prepare a candidate for an upcoming job interview:
        
        Job Details:
        {job_summary}
        
        Candidate Profile:
        {candidate_summary}
        
        Provide:
        1. 10 likely interview questions for this specific role (include technical, behavioral, and situational questions)
        2. For each question, suggest an effective approach to answering it
        3. 3 questions the candidate should ask the interviewer
        4. 5 tips for preparing for this specific interview
        
        Format your response as a JSON object with the following structure:
        {{
            "likely_questions": [
                {{
                    "question": "Question text",
                    "type": "technical/behavioral/situational",
                    "approach": "Suggested approach to answering"
                }}
            ],
            "questions_to_ask": [
                "Question 1",
                "Question 2",
                "Question 3"
            ],
            "preparation_tips": [
                "Tip 1",
                "Tip 2",
                "..."
            ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI interview coach. Respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            # Fallback if JSON parsing fails
            result = {
                "likely_questions": [
                    {
                        "question": "Tell me about your relevant experience for this role",
                        "type": "behavioral",
                        "approach": "Focus on experience directly relevant to the job requirements"
                    },
                    {
                        "question": "How do you handle challenging situations?",
                        "type": "behavioral",
                        "approach": "Use the STAR method (Situation, Task, Action, Result) with a relevant example"
                    }
                ],
                "questions_to_ask": [
                    "What does success look like in this role?",
                    "Can you tell me about the team I'd be working with?",
                    "What are the biggest challenges for someone in this position?"
                ],
                "preparation_tips": [
                    "Research the company thoroughly",
                    "Practice your answers to common questions",
                    "Prepare examples that demonstrate relevant skills",
                    "Review the job description thoroughly",
                    "Prepare questions that show your interest and knowledge"
                ]
            }
            
        return result

    async def recommend_differentiation_strategies(self, resume_data, job_data):
        """Suggest ways to stand apart from other candidates"""
        # Format job summary
        job_summary = f"""
        Title: {job_data.get('title', 'Unknown')}
        Company: {job_data.get('company', 'Unknown')}
        Required Skills: {', '.join(job_data.get('required_skills', []))}
        Job Description: {job_data.get('description', 'Not provided')[:500]}...
        """
        
        # Format candidate summary
        candidate_summary = f"""
        Key Skills: {', '.join(resume_data.get('skills', [])[:10])}
        Experience: {self._format_experience(resume_data.get('experience', []))}
        Education: {self._format_education(resume_data.get('education', []))}
        """
        
        # Use OpenAI to generate differentiation strategies
        prompt = f"""
        As a career strategist, recommend ways for a candidate to stand out from other applicants for this specific role:
        
        Job Details:
        {job_summary}
        
        Candidate Profile:
        {candidate_summary}
        
        Provide strategies in these categories:
        1. Application differentiation - how to make their application stand out
        2. Portfolio/work sample ideas specific to this role
        3. Research and preparation that would impress during interviews
        4. Follow-up strategies after applying/interviewing
        5. Personal branding approaches for this specific role
        
        Format your response as a JSON object with the following structure:
        {{
            "application_strategies": ["strategy 1", "strategy 2", ...],
            "portfolio_ideas": ["idea 1", "idea 2", ...],
            "research_preparation": ["approach 1", "approach 2", ...],
            "follow_up_strategies": ["strategy 1", "strategy 2", ...],
            "personal_branding": ["approach 1", "approach 2", ...]
        }}
        
        Provide 3-4 items for each category.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI career strategist. Respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            # Fallback if JSON parsing fails
            result = {
                "application_strategies": [
                    "Include a personalized cover letter addressing specific company needs",
                    "Highlight unique projects that demonstrate required skills",
                    "Include relevant metrics and achievements that stand out"
                ],
                "portfolio_ideas": [
                    "Create a targeted mini-project showing skills important for the role",
                    "Include case studies of relevant work",
                    "Create a presentation of your approach to a challenge in this field"
                ],
                "research_preparation": [
                    "Research recent company news and initiatives",
                    "Study industry trends and prepare to discuss them",
                    "Learn about the company's competitors and market position"
                ],
                "follow_up_strategies": [
                    "Send a thoughtful thank-you note referencing specific discussion points",
                    "Share a relevant article or resource after the interview",
                    "Connect with team members on LinkedIn with personalized messages"
                ],
                "personal_branding": [
                    "Optimize LinkedIn profile with keywords from the job description",
                    "Share relevant industry content on professional social media",
                    "Engage in industry discussions on professional forums or LinkedIn"
                ]
            }
            
        return result

    def _format_experience(self, experience_list):
        """Helper to format experience list for prompts"""
        if not experience_list:
            return "No experience listed"
            
        formatted = ""
        for exp in experience_list[:3]:  # Limit to 3 most recent to keep prompts manageable
            formatted += f"- {exp.get('title', 'Unknown role')} at {exp.get('company', 'Unknown')}, {exp.get('duration', 'Unknown duration')}\n"
            
        if len(experience_list) > 3:
            formatted += f"- And {len(experience_list) - 3} more positions...\n"
            
        return formatted

    def _format_education(self, education_list):
        """Helper to format education list for prompts"""
        if not education_list:
            return "No education listed"
            
        formatted = ""
        for edu in education_list[:2]:  # Limit to 2 most relevant
            formatted += f"- {edu.get('degree', 'Unknown degree')} in {edu.get('field', 'Unknown field')} from {edu.get('institution', 'Unknown institution')}\n"
            
        if len(education_list) > 2:
            formatted += f"- And {len(education_list) - 2} more educational qualifications...\n"
            
        return formatted
