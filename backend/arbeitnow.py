import requests
import time
import random
import re
from typing import List, Dict, Tuple, Any, Optional

class ArbeitnowJobFetcher:
    def __init__(self, api_key=None):
        # Arbeitnow doesn't require an API key
        self.base_url = "https://www.arbeitnow.com/api/job-board-api"
        self.cache = {}  # Simple in-memory cache
        self.cache_timeout = 3600  # Cache timeout in seconds (1 hour)

    def search_jobs(self, keywords, location=None, experience_level=None, language="English", count=None):
        """Search for jobs matching criteria using Arbeitnow API"""
        print(f"Searching jobs with: keywords={keywords}, location={location}, experience={experience_level}, language={language}")
        
        # Check cache first
        cache_key = f"{keywords}_{location}_{experience_level}_{language}_{count}"
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if time.time() - cache_time < self.cache_timeout:
                return cache_data

        # Build query parameters
        params = {}
        
        # Add keywords to search parameter
        if keywords:
            params["search"] = keywords
        
        # Add filters if provided
        if location:
            params["location"] = location
        
        # Map language to API expected format
        if language and language.lower() != "any":
            # Arbeitnow API uses language codes
            language_map = {"english": "en", "german": "de", "french": "fr", "spanish": "es"}
            lang_code = language_map.get(language.lower(), "en")
            params["language"] = lang_code
        
        # Handle experience level filter (Arbeitnow doesn't have this directly)
        # We'll filter results after fetching
        
        # Add sorting by relevance
        params["sort"] = "relevance"
        
        # Add page size parameter (fetch more to allow for filtering)
        try:
            from config import MAX_JOBS_TO_FETCH
            params["page_size"] = min(count or MAX_JOBS_TO_FETCH, 50)  # API may have limits
        except ImportError:
            params["page_size"] = min(count or 50, 50)  # Default if config not available
        
        print(f"API parameters: {params}")
        
        # Make the API request with retry logic
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.get(self.base_url, params=params, timeout=10)
                print(f"API response status: {response.status_code}")
                
                if response.status_code == 200:
                    arbeitnow_jobs = response.json().get("data", [])
                    print(f"Found {len(arbeitnow_jobs)} jobs from API")
                    
                    # Convert Arbeitnow job format to your application's format
                    jobs = []
                    
                    for job in arbeitnow_jobs:
                        # Map to your job structure
                        processed_job = self._map_arbeitnow_to_job_object(job)
                        
                        # Filter by language here as a double-check
                        job_language = processed_job.get("language", "en")
                        if language and language.lower() != "any":
                            lang_code = language_map.get(language.lower(), "en")
                            if job_language != lang_code:
                                continue
                        
                        # Add to jobs list if it passes language filter
                        jobs.append(processed_job)
                    
                    print(f"Processed {len(jobs)} jobs after language filtering")
                    
                    # Score and filter results
                    scored_jobs = []
                    for job in jobs:
                        # Calculate relevance score with keywords
                        relevance_score = self._calculate_relevance_score(job, keywords)
                        
                        # Only include jobs with meaningful relevance
                        if relevance_score > 0:
                            # Store job with its score
                            scored_jobs.append((job, relevance_score))
                    
                    print(f"Found {len(scored_jobs)} jobs with relevance > 0")
                    
                    # Filter by experience level if provided
                    if experience_level and experience_level.lower() != "all":
                        filtered_jobs = []
                        for job, score in scored_jobs:
                            # Check if job description or title indicates the right experience level
                            if self._matches_experience_level(job, experience_level):
                                filtered_jobs.append((job, score))
                        scored_jobs = filtered_jobs
                        print(f"After experience filtering: {len(scored_jobs)} jobs")
                    
                    # Sort by relevance score (descending)
                    scored_jobs.sort(key=lambda x: x[1], reverse=True)
                    
                    # Extract just the jobs (without scores)
                    sorted_jobs = [job for job, _ in scored_jobs]
                    
                    # Print top 5 matches for debugging
                    for i, (job, score) in enumerate(scored_jobs[:5], 1):
                        print(f"Match #{i}: {job['title']} - Score: {score}")
                    
                    # Limit results if count is specified
                    result = sorted_jobs[:count] if count else sorted_jobs
                    
                    # Update cache
                    self.cache[cache_key] = (time.time(), result)
                    
                    return result
                
                elif response.status_code == 429:  # Too many requests
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        print(f"Rate limit exceeded after {max_retries} attempts")
                        return self._generate_mock_jobs(keywords, location, experience_level, count)
                
                else:
                    print(f"Error fetching jobs: {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        return self._generate_mock_jobs(keywords, location, experience_level, count)
            
            except Exception as e:
                print(f"Exception when fetching jobs: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    return self._generate_mock_jobs(keywords, location, experience_level, count)
        
        return self._generate_mock_jobs(keywords, location, experience_level, count)

    def _calculate_relevance_score(self, job, keywords):
        """Calculate a relevance score for ranking job results"""
        if not keywords:
            return 0
        
        # Initialize score
        score = 0
        
        # Split keywords for more precise matching
        keywords_list = [kw.lower().strip() for kw in keywords.split() if len(kw.strip()) > 2]
        if not keywords_list:
            return 0
            
        # Get job fields for matching
        title = job.get("title", "").lower()
        company = job.get("company", "").lower()
        description = job.get("description", "").lower()
        required_skills = [skill.lower() for skill in job.get("required_skills", [])]
        
        # Check for exact keyword matches in title (highest weight)
        for keyword in keywords_list:
            # Exact title match (strongest signal)
            if keyword in title:
                score += 20
                # Bonus for keyword at the beginning of title
                if title.startswith(keyword):
                    score += 10
            
            # Partial title match (still strong)
            elif any(keyword in word for word in title.split()):
                score += 10
        
        # Check for keyword matches in skills (high weight)
        for keyword in keywords_list:
            skill_matches = sum(1 for skill in required_skills if keyword in skill)
            score += skill_matches * 8
        
        # Check for keyword matches in description (medium weight)
        for keyword in keywords_list:
            # Count occurrences in description (more occurrences = more relevant)
            keyword_count = description.count(keyword)
            if keyword_count > 0:
                # Cap the contribution from multiple occurrences
                score += min(keyword_count * 2, 10)
        
        # Company name match (slight bonus)
        for keyword in keywords_list:
            if keyword in company:
                score += 3
        
        # Normalize score to a more reasonable range (0-100)
        # This conversion ensures more meaningful percentage displays
        if score > 0:
            # Apply diminishing returns for very high raw scores
            normalized_score = min(100, int(20 + (score * 80 / 100)))
            return normalized_score
        
        return 0

    def _matches_experience_level(self, job, experience_level):
        """Check if job matches the specified experience level"""
        experience_level = experience_level.lower()
        
        # Get relevant job fields
        title = job.get("title", "").lower()
        description = job.get("description", "").lower()
        experience_required = job.get("experience_required", "").lower()
        
        # Define keywords for different experience levels
        level_keywords = {
            "entry": ["entry", "junior", "trainee", "graduate", "entry-level", "entry level", 
                     "beginner", "0-2 years", "0-1 year", "einsteiger", "junior", "praktikum", "werkstudent"],
            "mid": ["mid", "intermediate", "associate", "2-5 years", "3-5 years", "mitarbeiter", "sachbearbeiter"],
            "senior": ["senior", "expert", "lead", "5+ years", "5-7 years", "6+ years", "experienced", 
                      "manager", "director", "head of", "leiter", "führung"],
            "executive": ["executive", "c-level", "chief", "cto", "ceo", "cfo", "vp", "vice president", 
                         "head of", "director", "geschäftsführer", "vorstand"]
        }
        
        # For remote jobs, handle differently
        if experience_level == "remote":
            return ("remote" in title or "remote" in description or 
                   "home office" in description or "work from home" in description or
                   "remote" in job.get("location", "").lower())
        
        # Check for level-specific keywords
        relevant_keywords = level_keywords.get(experience_level, [])
        if not relevant_keywords:
            return True  # Unknown level, don't filter
        
        # Check title for level keywords
        for keyword in relevant_keywords:
            if keyword in title:
                return True
        
        # Check experience required
        for keyword in relevant_keywords:
            if keyword in experience_required:
                return True
        
        # Check description for level keywords
        # Be more lenient here - just need one match from description
        for keyword in relevant_keywords:
            if keyword in description:
                return True
        
        # Default behavior depends on level
        if experience_level == "entry":
            # For entry level, also return True if no specific experience is mentioned
            no_experience_required = (
                "no experience" in description or
                "keine erfahrung" in description or
                ("experience" not in description and "erfahrung" not in description)
            )
            return no_experience_required
            
        # If we don't find explicit level markers, return False
        return False

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
            "apply_url": arbeitnow_job.get("url", ""),
            "language": arbeitnow_job.get("language", "en")
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
            "marketing": ["Marketing Strategy", "SEO", "Content Marketing", "Social Media", "Digital Marketing"],
            "hr": ["Recruitment", "Employee Relations", "HR Policies", "Talent Management"],
            "software": ["Programming", "Software Development", "Debugging", "Code Review"],
            "frontend": ["HTML", "CSS", "JavaScript", "UI/UX", "React", "Angular"],
            "backend": ["API Development", "Databases", "Server Management", "Node.js", "Django"]
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
        # Common technical skills to look for (including German terms)
        common_skills = [
            "Python", "R", "SQL", "JavaScript", "Java", "C++", "C#", "Ruby", "PHP",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Jenkins",
            "Excel", "Word", "PowerPoint", "Tableau", "Power BI", "Looker",
            "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "AI",
            "Data Analysis", "Data Science", "Statistics", "Mathematics",
            "Agile", "Scrum", "Kanban", "Project Management", "Leadership",
            "Communication", "Teamwork", "Problem Solving", "Critical Thinking",
            # Marketing specific skills
            "SEO", "SEM", "Content Marketing", "Social Media", "Email Marketing",
            "Google Analytics", "Facebook Ads", "Google Ads", "Marketing Strategy",
            "Brand Management", "Market Research", "Digital Marketing", "Campaign Management",
            # German-specific skills
            "Deutsch", "Englisch", "Kommunikationsfähigkeit", "Teamfähigkeit",
            "SAP", "Beratung", "Vertrieb", "Projektleitung", "Marketing", "Werbung"
        ]
        
        description_lower = description.lower()
        found_skills = []
        
        # Extract skills using improved pattern matching
        for skill in common_skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)
        
        # Look for technical terms with word boundaries
        technical_patterns = [
            r'\b(react(?:\.js)?)\b', r'\b(node(?:\.js)?)\b', r'\b(angular(?:js)?)\b',
            r'\b(vue(?:\.js)?)\b', r'\b(django)\b', r'\b(flask)\b', r'\b(spring)\b',
            r'\b(express(?:\.js)?)\b', r'\b(typescript)\b', r'\b(graphql)\b',
            r'\b(seo)\b', r'\b(sem)\b', r'\b(marketing)\b', r'\b(adwords)\b'
        ]
        
        for pattern in technical_patterns:
            matches = re.findall(pattern, description_lower)
            for match in matches:
                if match and match.capitalize() not in found_skills:
                    found_skills.append(match.capitalize())
        
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
            
            if any(term in line.lower() for term in ["qualifications", "requirements", "anforderungen", "voraussetzungen"]):
                in_qualifications_section = True
                continue
            
            if in_qualifications_section and any(term in line.lower() for term in ["benefits", "we offer", "wir bieten"]):
                in_qualifications_section = False
                continue
            
            if in_qualifications_section and line.startswith(('-', '•', '*')):
                qualifications.append(line.lstrip('-•* '))
        
        return qualifications[:5] # Limit to 5 qualifications

    def _extract_experience(self, description):
        """Extract experience requirements from description"""
        description_lower = description.lower()
        
        # Look for years of experience patterns in English and German
        experience_patterns = [
            r'(\d+\+?\s*(?:years|year)(?:\s*of)?\s*experience)',
            r'(\d+\+?\s*jahre\s*(?:berufserfahrung|erfahrung))'
        ]
        
        for pattern in experience_patterns:
            match = re.search(pattern, description_lower)
            if match:
                # Find the sentence containing the experience
                sentences = description.split('.')
                for sentence in sentences:
                    if match.group(1) in sentence.lower():
                        return sentence.strip()
        
        # Check for experience phrases
        experience_phrases = [
            "years of experience", "years experience", "year experience",
            "experienced in", "jahre erfahrung", "berufserfahrung"
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
        
        # Education keywords in English and German
        education_keywords = [
            "degree", "bachelor", "master", "phd", "diploma", "certification",
            "studium", "abschluss", "bachelor", "master", "diplom", "ausbildung"
        ]
        
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
        # Check cache first
        for cache_key, (_, cache_data) in self.cache.items():
            for job in cache_data:
                if job.get("id") == job_id:
                    return job
        
        # Arbeitnow doesn't have a specific endpoint for job details
        # Return a mock job as fallback
        return {
            "id": job_id,
            "title": "Data Scientist",
            "company": "Tech Innovations",
            "location": "Berlin",
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
        
        # Generate jobs specifically related to the keywords
        if keywords and keywords.lower() == "marketing":
            job_titles = [
                "Marketing Specialist", "Digital Marketing Manager", "Social Media Coordinator",
                "Content Marketing Specialist", "SEO Specialist", "Marketing Analyst",
                "Brand Marketing Manager", "Email Marketing Specialist"
            ]
            
            skills_by_title = {
                "Marketing Specialist": ["Marketing Strategy", "Social Media", "Content Creation", "SEO", "Analytics"],
                "Digital Marketing Manager": ["Digital Marketing", "SEO/SEM", "Campaign Management", "Analytics", "Social Media"],
                "Social Media Coordinator": ["Social Media", "Content Creation", "Hootsuite", "Community Management", "Analytics"],
                "Content Marketing Specialist": ["Content Strategy", "Blog Writing", "SEO", "Content Management", "Copywriting"],
                "SEO Specialist": ["SEO", "Keyword Research", "Analytics", "Link Building", "Technical SEO"],
                "Marketing Analyst": ["Data Analysis", "Google Analytics", "Marketing Metrics", "Reporting", "Excel"],
                "Brand Marketing Manager": ["Brand Strategy", "Campaign Management", "Market Research", "Creative Direction", "Positioning"],
                "Email Marketing Specialist": ["Email Campaigns", "A/B Testing", "Marketing Automation", "CRM", "Analytics"]
            }
        else:
            # Generic job titles for other searches
            job_titles = ["Data Scientist", "Software Developer", "Project Manager",
                         "Business Analyst", "UX Designer", "Product Manager", "Sales Representative"]
            
            skills_by_title = {
                "Data Scientist": ["Python", "Machine Learning", "SQL", "Data Analysis", "Statistics"],
                "Software Developer": ["JavaScript", "Python", "Git", "HTML", "CSS", "React"],
                "Project Manager": ["Project Management", "Agile", "Scrum", "Leadership", "Communication"],
                "Business Analyst": ["Data Analysis", "Requirements Gathering", "SQL", "Excel", "Process Improvement"],
                "UX Designer": ["UI/UX Design", "Wireframing", "User Research", "Figma", "Prototyping"],
                "Product Manager": ["Product Development", "Market Research", "Roadmapping", "Stakeholder Management", "Agile"],
                "Sales Representative": ["Sales", "Negotiation", "Customer Relationship", "CRM", "Communication"]
            }
        
        companies = ["TechCorp", "DataSystems", "AILabs", "CodeFactory", "Deutsche Tech", "MarketingPro", "BrandBoost"]
        
        # Use provided location or default to German cities
        locations = [location] if location else ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne"]
        
        # Generate appropriate number of jobs
        for i in range(min(count or 10, len(job_titles))):
            job_title = job_titles[i]
            skills = skills_by_title.get(job_title, ["Communication", "Teamwork", "Problem Solving"])
            
            # Set language based on search criteria
            job_language = "en" if "english" in (language or "").lower() else "de"
            
            # Experience level text
            exp_text = ""
            if experience_level and experience_level.lower() == "entry":
                exp_text = "No previous experience required. Perfect for recent graduates."
            elif experience_level and experience_level.lower() == "mid":
                exp_text = "2-5 years of relevant experience required."
            elif experience_level and experience_level.lower() == "senior":
                exp_text = "5+ years of experience in similar roles required."
            elif experience_level and experience_level.lower() == "executive":
                exp_text = "10+ years of experience with leadership background required."
            
            mock_jobs.append({
                "id": f"mock-job-{i}",
                "title": job_title,
                "company": companies[i % len(companies)],
                "location": locations[i % len(locations)],
                "description": f"We are looking for a talented {job_title} to join our team. {exp_text}",
                "required_skills": skills,
                "qualifications": ["Relevant degree or certification", "Strong communication skills"],
                "experience_required": exp_text if exp_text else "Relevant experience in the field",
                "education_required": "Bachelor's degree in relevant field or equivalent experience",
                "apply_url": "https://example.com/apply",
                "language": job_language
            })
        
        return mock_jobs
