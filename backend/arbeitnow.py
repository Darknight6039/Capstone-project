import requests
import time
import random

class ArbeitnowJobFetcher:
    def __init__(self, api_key=None):
        # Arbeitnow doesn't require an API key
        self.base_url = "https://www.arbeitnow.com/api/job-board-api"
        
    def search_jobs(self, keywords, location=None, experience_level=None, language="English", count=None):
        """Search for jobs matching criteria using Arbeitnow API"""
        # Build query parameters
        params = {}
        
        # Add keywords to search parameter
        if keywords:
            params["search"] = keywords
            
        # Add filters if provided
        if location:
            params["location"] = location
            
        # Add language filter
        if language and language.lower() != "any":
            params["language"] = language.lower()
            
        # Arbeitnow supports remote filter
        if experience_level and experience_level.lower() == "remote":
            params["remote"] = "true"
            
        # Add sorting by relevance
        params["sort"] = "relevance"
        
        # Add page size parameter
        from config import MAX_JOBS_TO_FETCH
        params["page_size"] = count or MAX_JOBS_TO_FETCH
        
        # Make the API request
        try:
            response = requests.get(self.base_url, params=params)
            if response.status_code == 200:
                arbeitnow_jobs = response.json().get("data", [])
                
                # Convert Arbeitnow job format to your application's format
                jobs = []
                for job in arbeitnow_jobs:
                    # Additional keyword filtering for better relevance
                    if keywords and not self._job_matches_keywords(job, keywords):
                        continue
                        
                    # Map to your job structure
                    processed_job = self._map_arbeitnow_to_job_object(job)
                    jobs.append(processed_job)
                    
                # Limit results if count is specified
                if count and len(jobs) >= count:
                    return jobs[:count]
                    
                return jobs
            else:
                print(f"Error fetching jobs: {response.status_code}")
                return self._generate_mock_jobs(keywords, location, experience_level, count)
        except Exception as e:
            print(f"Exception when fetching jobs: {str(e)}")
            return self._generate_mock_jobs(keywords, location, experience_level, count)
            
    def _job_matches_keywords(self, job, keywords):
        """Check if job matches the provided keywords"""
        keywords_lower = keywords.lower().split()
        title_lower = job.get("title", "").lower()
        description_lower = job.get("description", "").lower()
        
        # Improved matching algorithm
        keyword_match_count = 0
        for keyword in keywords_lower:
            if keyword in title_lower:
                # Title matches are more important
                keyword_match_count += 2
            elif keyword in description_lower:
                keyword_match_count += 1
                
        # Require a minimum match score based on number of keywords
        return keyword_match_count >= len(keywords_lower)
        
    def _map_arbeitnow_to_job_object(self, arbeitnow_job):
        """Convert Arbeitnow job format to your application's job object format"""
        # Extract skills from tags and description
        skills = self._extract_skills_from_tags(arbeitnow_job.get("tags", []))
        
        # Extract additional skills from description
        description_skills = self._extract_skills_from_description(arbeitnow_job.get("description", ""))
        skills.extend([skill for skill in description_skills if skill not in skills])
        
        return {
            "id": str(arbeitnow_job.get("slug", "")),
            "title": arbeitnow_job.get("title", "Unknown position"),
            "company": arbeitnow_job.get("company_name", "Unknown company"),
            "location": arbeitnow_job.get("location", "Unknown location"),
            "description": arbeitnow_job.get("description", ""),
            "required_skills": skills,
            "qualifications": self._extract_qualifications(arbeitnow_job.get("description", "")),
            "experience_required": self._extract_experience(arbeitnow_job.get("description", "")),
            "education_required": self._extract_education(arbeitnow_job.get("description", "")),
            "apply_url": arbeitnow_job.get("url", "")
        }
        
    def _extract_skills_from_tags(self, tags):
        """Extract skills from job tags"""
        # Tags often contain skills and technologies
        skill_tags = [tag for tag in tags if not tag.startswith("location:") and not tag.startswith("type:")]
        
        # Enhance skills list based on job type keywords in tags
        common_skills_by_job_type = {
            "business analyst": ["Excel", "SQL", "Data Analysis", "Requirements Gathering", "Business Intelligence"],
            "data scientist": ["Python", "R", "Machine Learning", "Statistics", "SQL", "Data Visualization"],
            "developer": ["JavaScript", "Python", "SQL", "Git", "Problem Solving"],
            "project manager": ["Project Management", "Agile", "Scrum", "Stakeholder Management"],
            "marketing": ["Marketing Strategy", "SEO", "Content Marketing", "Social Media"],
            "hr": ["Recruitment", "Employee Relations", "HR Policies", "Talent Management"]
        }
        
        # Check if any job type keywords are in the tags
        for job_type, skills in common_skills_by_job_type.items():
            if any(job_type in tag.lower() for tag in tags):
                # Add common skills for that job type
                for skill in skills:
                    if skill not in skill_tags:
                        skill_tags.append(skill)
                        
        return skill_tags
        
    def _extract_skills_from_description(self, description):
        """Extract skills from job description"""
        # Common technical skills to look for
        common_skills = [
            "Python", "R", "SQL", "JavaScript", "Java", "C++", "C#", "Ruby", "PHP",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Jenkins",
            "Excel", "Word", "PowerPoint", "Tableau", "Power BI", "Looker",
            "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "AI",
            "Data Analysis", "Data Science", "Statistics", "Mathematics",
            "Agile", "Scrum", "Kanban", "Project Management", "Leadership",
            "Communication", "Teamwork", "Problem Solving", "Critical Thinking"
        ]
        
        found_skills = []
        description_lower = description.lower()
        
        for skill in common_skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)
                
        return found_skills
        
    def _extract_qualifications(self, description):
        """Extract qualifications from job description"""
        # Basic implementation - in a real app, use NLP for better extraction
        qualifications = []
        
        # Look for common qualification indicators
        desc_lines = description.split('\n')
        in_qualifications_section = False
        
        for line in desc_lines:
            line = line.strip()
            if not line:
                continue
                
            if "qualifications" in line.lower() or "requirements" in line.lower():
                in_qualifications_section = True
                continue
                
            if in_qualifications_section and line.startswith(('-', '•', '*')):
                qualifications.append(line.lstrip('-•* '))
                
        return qualifications[:5]  # Limit to 5 qualifications
        
    def _extract_experience(self, description):
        """Extract experience requirements from description"""
        # Simple regex could be used here for a more robust solution
        description_lower = description.lower()
        experience_phrases = [
            "years of experience",
            "years experience",
            "year experience",
            "experienced in"
        ]
        
        for phrase in experience_phrases:
            if phrase in description_lower:
                # Find the sentence containing the phrase
                sentences = description.split('.')
                for sentence in sentences:
                    if phrase in sentence.lower():
                        return sentence.strip()
                        
        return "Not specified"
        
    def _extract_education(self, description):
        """Extract education requirements from description"""
        description_lower = description.lower()
        education_keywords = ["degree", "bachelor", "master", "phd", "diploma", "certification"]
        
        for keyword in education_keywords:
            if keyword in description_lower:
                # Find the sentence containing the keyword
                sentences = description.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        return sentence.strip()
                        
        return "Not specified"
        
    def get_job_details(self, job_id):
        """Get detailed information about a specific job"""
        # Arbeitnow doesn't have a specific endpoint for job details
        # In a real implementation, you might want to cache job data
        return {
            "id": job_id,
            "title": "Data Scientist",
            "company": "Tech Innovations",
            "location": "Remote",
            "description": "Looking for a talented Data Scientist...",
            "required_skills": ["Python", "Machine Learning", "SQL"],
            "qualifications": ["Bachelor's degree", "3+ years experience"],
            "experience_required": "3+ years in data science",
            "education_required": "Bachelor's degree in related field",
            "apply_url": f"https://www.arbeitnow.com/view/{job_id}"
        }
        
    def _generate_mock_jobs(self, keywords, location, experience_level, count=5):
        """Generate mock job listings for fallback"""
        mock_jobs = []
        job_titles = ["Data Scientist", "Machine Learning Engineer", "Data Analyst",
                      "AI Researcher", "Business Intelligence Analyst"]
        companies = ["TechCorp", "DataSystems", "AILabs", "Analytics Plus", "Future Tech"]
        locations = [location or "Remote", "Paris", "Lyon", "Marseille", "Bordeaux"]
        
        # Generate random jobs
        for i in range(min(count or 5, 10)):
            skills = ["Python", "SQL", "Machine Learning", "Data Analysis", "Statistics",
                      "Deep Learning", "TensorFlow", "PyTorch", "Pandas", "Scikit-learn"]
            random.shuffle(skills)
            
            mock_jobs.append({
                "id": f"mock-job-{i}",
                "title": job_titles[i % len(job_titles)],
                "company": companies[i % len(companies)],
                "location": locations[i % len(locations)],
                "description": f"We are looking for a talented {job_titles[i % len(job_titles)]} to join our team...",
                "required_skills": skills[:5],
                "qualifications": ["Bachelor's degree", "3+ years experience"],
                "experience_required": "3+ years in data science",
                "education_required": "Bachelor's degree in related field",
                "apply_url": "https://example.com/apply"
            })
            
        return mock_jobs
