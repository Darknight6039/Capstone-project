import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os
import json

class CompatibilityPredictor:
    def __init__(self, model_path=None):
        """Initialize the job-field compatibility predictor"""
        self.model = self._load_model(model_path)
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.job_categories = self._load_job_categories()
        
    def _load_model(self, model_path=None):
        """Load pre-trained model or create a new one"""
        if model_path and os.path.exists(model_path):
            try:
                return joblib.load(model_path)
            except Exception as e:
                print(f"Error loading model: {e}")
        
        # Create a new model if no pre-trained model is available
        return RandomForestClassifier(n_estimators=100, random_state=42)
    
    def _load_job_categories(self):
        """Load job categories data"""
        # In a real application, this would load from a file
        # Here we define a simple dictionary of job categories and related skills
        return {
            "Data Science": {
                "skills": ["Python", "Machine Learning", "Data Analysis", "Statistics", "SQL", "TensorFlow", "PyTorch"],
                "education": ["Computer Science", "Statistics", "Mathematics"],
                "experience_keywords": ["data", "analysis", "machine learning", "algorithms", "prediction"]
            },
            "Software Engineering": {
                "skills": ["Java", "JavaScript", "Python", "C++", "Git", "Docker", "Cloud", "Microservices"],
                "education": ["Computer Science", "Software Engineering", "Information Technology"],
                "experience_keywords": ["software", "development", "programming", "coding", "architecture"]
            },
            "UX/UI Design": {
                "skills": ["Adobe XD", "Figma", "Sketch", "User Research", "Wireframing", "Prototyping"],
                "education": ["Design", "Human-Computer Interaction", "Psychology"],
                "experience_keywords": ["design", "user experience", "interface", "usability", "prototype"]
            },
            "Marketing": {
                "skills": ["Social Media", "Content Strategy", "SEO", "Analytics", "Campaign Management"],
                "education": ["Marketing", "Communications", "Business"],
                "experience_keywords": ["marketing", "campaign", "brand", "market research", "strategy"]
            },
            "Project Management": {
                "skills": ["Agile", "Scrum", "JIRA", "Risk Management", "Stakeholder Management"],
                "education": ["Business", "Management", "Engineering"],
                "experience_keywords": ["project", "management", "planning", "coordination", "delivery"]
            }
        }
    
    def predict_compatibility(self, user_profile, job_listings=None):
        """Predict compatibility between user profile and job categories or specific listings"""
        # Extract features from user profile
        user_skills = [skill["skill"] for skill in user_profile.get("skills", [])]
        user_education = [edu["field"] for edu in user_profile.get("education", [])]
        user_experience = " ".join([exp.get("title", "") + " " + exp.get("company", "") 
                                  for exp in user_profile.get("experience", [])])
        
        results = []
        
        # If specific job listings are provided, match against those
        if job_listings:
            for job in job_listings:
                score = self._calculate_job_match_score(user_skills, user_education, user_experience, job)
                results.append({
                    "job_id": job.get("id", ""),
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "compatibility_score": score,
                    "skill_match": self._get_skill_match_details(user_skills, job.get("required_skills", []))
                })
        
        # Otherwise, match against job categories
        else:
            for category, category_data in self.job_categories.items():
                score = self._calculate_category_match_score(user_skills, user_education, user_experience, category, category_data)
                results.append({
                    "category": category,
                    "compatibility_score": score,
                    "matching_skills": [skill for skill in user_skills if skill in category_data["skills"]],
                    "missing_skills": [skill for skill in category_data["skills"] if skill not in user_skills],
                    "recommended_skills": self._get_recommended_skills(user_skills, category_data["skills"])
                })
        
        # Sort results by compatibility score
        results.sort(key=lambda x: x.get("compatibility_score", 0), reverse=True)
        
        return results
    
    def _calculate_job_match_score(self, user_skills, user_education, user_experience, job):
        """Calculate compatibility score between user and specific job"""
        # Skills match component
        job_skills = job.get("required_skills", [])
        if not job_skills:
            skills_score = 0.5  # Neutral if no skills specified
        else:
            matching_skills = [skill for skill in user_skills if skill in job_skills]
            skills_score = len(matching_skills) / len(job_skills) if len(job_skills) > 0 else 0
        
        # Education match component
        education_score = 0.5  # Default value
        job_education = job.get("education_required", "")
        if job_education:
            # Simple string matching for education
            education_score = any(edu.lower() in job_education.lower() for edu in user_education) if user_education else 0
        
        # Experience match component
        experience_score = 0.5  # Default value
        job_description = job.get("description", "") + " " + job.get("experience_required", "")
        if job_description and user_experience:
            # Calculate text similarity for experience matching
            job_vec = self.vectorizer.fit_transform([job_description])
            user_vec = self.vectorizer.transform([user_experience])
            experience_score = cosine_similarity(user_vec, job_vec)[0][0]
        
        # Weighted combination of scores
        weights = {"skills": 0.6, "education": 0.2, "experience": 0.2}
        total_score = (
            skills_score * weights["skills"] + 
            education_score * weights["education"] + 
            experience_score * weights["experience"]
        )
        
        return min(1.0, total_score)
    
    def _calculate_category_match_score(self, user_skills, user_education, user_experience, category, category_data):
        """Calculate compatibility score between user and job category"""
        # Skills match component
        category_skills = category_data["skills"]
        matching_skills = [skill for skill in user_skills if skill in category_skills]
        skills_score = len(matching_skills) / len(category_skills) if len(category_skills) > 0 else 0
        
        # Education match component
        category_education = category_data["education"]
        education_score = any(edu.lower() in cat_edu.lower() for edu in user_education for cat_edu in category_education) if user_education else 0
        
        # Experience match component
        experience_score = 0
        if user_experience:
            # Check for keywords in user experience
            category_keywords = category_data["experience_keywords"]
            experience_score = sum(1 for keyword in category_keywords if keyword.lower() in user_experience.lower()) / len(category_keywords)
        
        # Weighted combination of scores
        weights = {"skills": 0.6, "education": 0.2, "experience": 0.2}
        total_score = (
            skills_score * weights["skills"] + 
            education_score * weights["education"] + 
            experience_score * weights["experience"]
        )
        
        return min(1.0, total_score)
    
    def _get_skill_match_details(self, user_skills, job_skills):
        """Get detailed information about skill matches and gaps"""
        matched_skills = [skill for skill in user_skills if skill in job_skills]
        missing_skills = [skill for skill in job_skills if skill not in user_skills]
        
        return {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "match_percentage": len(matched_skills) / len(job_skills) if job_skills else 0
        }
    
    def _get_recommended_skills(self, user_skills, category_skills, top_n=3):
        """Get recommended skills for the user to learn based on category"""
        missing_skills = [skill for skill in category_skills if skill not in user_skills]
        
        # In a real implementation, we would use a more sophisticated algorithm
        # to rank skill recommendations based on demand, difficulty, etc.
        return missing_skills[:top_n]
    
    def train(self, training_data):
        """Train the model on labeled data"""
        # In a real implementation, this would train the model on actual data
        # Here we implement a simple placeholder
        
        X = []  # Features
        y = []  # Labels
        
        for item in training_data:
            # Extract features
            features = self._extract_features(item["profile"])
            
            # Get label (job category)
            label = item["job_category"]
            
            X.append(features)
            y.append(label)
        
        # Train the model
        self.model.fit(X, y)
        
        return self.model
    
    def _extract_features(self, profile):
        """Extract numerical features from user profile for model training"""
        # In a real implementation, this would extract meaningful features
        # Here we implement a simple placeholder
        
        # Count skills by category
        technical_skills = 0
        soft_skills = 0
        domain_skills = 0
        
        for skill in profile.get("skills", []):
            skill_name = skill["skill"].lower()
            if any(tech in skill_name for tech in ["python", "java", "programming", "data"]):
                technical_skills += 1
            elif any(soft in skill_name for soft in ["communication", "leadership", "teamwork"]):
                soft_skills += 1
            else:
                domain_skills += 1
        
        # Education level
        education_level = 0
        for edu in profile.get("education", []):
            degree = edu.get("degree", "").lower()
            if "bachelor" in degree or "bs" in degree or "ba" in degree:
                education_level = max(education_level, 1)
            elif "master" in degree or "ms" in degree or "ma" in degree:
                education_level = max(education_level, 2)
            elif "phd" in degree or "doctorate" in degree:
                education_level = max(education_level, 3)
        
        # Experience years
        experience_years = 0
        for exp in profile.get("experience", []):
            # In a real implementation, we would actually parse the duration
            # Here we just use a placeholder
            experience_years += 1
        
        return [technical_skills, soft_skills, domain_skills, education_level, experience_years]
    
    def save_model(self, model_path):
        """Save the trained model to a file"""
        joblib.dump(self.model, model_path)
        print(f"Model saved to {model_path}")
