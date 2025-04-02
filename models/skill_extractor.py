import spacy
import re
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import json
import os

class SkillExtractor:
    def __init__(self, skills_db_path=None):
        """Initialize the skill extractor with NLP models and skills database"""
        # Load spaCy model
        self.nlp = spacy.load("en_core_web_md")
        
        # Load skills database
        self.skills_db = self._load_skills_database(skills_db_path)
        
        # Initialize vectorizer for skills matching
        self.vectorizer = CountVectorizer(ngram_range=(1, 3), min_df=1, binary=True)
        self.vectorizer.fit([' '.join(self.skills_db)])
        
    def _load_skills_database(self, skills_db_path=None):
        """Load skills database from file or use default skills list"""
        if skills_db_path and os.path.exists(skills_db_path):
            try:
                with open(skills_db_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading skills database: {e}")
        
        # Default skills list if no database is provided
        return [
            "Python", "Java", "JavaScript", "HTML", "CSS", "SQL", "NoSQL",
            "Machine Learning", "Deep Learning", "Data Analysis", "Data Science",
            "Natural Language Processing", "Computer Vision", "TensorFlow", "PyTorch",
            "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "CI/CD",
            "React", "Angular", "Vue.js", "Node.js", "Django", "Flask",
            "Project Management", "Agile", "Scrum", "Business Analysis",
            "Communication", "Leadership", "Problem Solving", "Critical Thinking",
            "Microsoft Office", "Excel", "Word", "PowerPoint", "Tableau", "Power BI"
        ]
    
    def extract_skills(self, resume_text):
        """Extract skills from resume text using NLP and pattern matching"""
        # Preprocess text
        resume_text = self._preprocess_text(resume_text)
        
        # Extract skills using direct pattern matching
        pattern_skills = self._extract_skills_by_pattern(resume_text)
        
        # Extract skills using NLP
        nlp_skills = self._extract_skills_by_nlp(resume_text)
        
        # Combine and deduplicate skills
        all_skills = list(set(pattern_skills + nlp_skills))
        
        # Calculate confidence scores
        skills_with_confidence = self._calculate_confidence_scores(resume_text, all_skills)
        
        return skills_with_confidence
    
    def _preprocess_text(self, text):
        """Clean and preprocess resume text"""
        # Convert to lowercase
        text = text.lower()
        
        # Replace newlines with spaces
        text = re.sub(r'\n+', ' ', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_skills_by_pattern(self, text):
        """Extract skills using direct pattern matching"""
        found_skills = []
        
        for skill in self.skills_db:
            skill_lower = skill.lower()
            # Create word boundary pattern
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, text):
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_skills_by_nlp(self, text):
        """Extract skills using NLP techniques"""
        doc = self.nlp(text)
        
        # Extract noun phrases as potential skills
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]
        
        # Extract named entities that might be skills
        entities = [ent.text for ent in doc.ents if ent.label_ in ["ORG", "PRODUCT"]]
        
        # Combine potential skill phrases
        potential_skills = noun_phrases + entities
        
        # Match potential skills against skills database using similarity
        found_skills = []
        for skill in self.skills_db:
            skill_doc = self.nlp(skill.lower())
            
            # Check if any potential skill is similar to skills in database
            for potential_skill in potential_skills:
                potential_skill_doc = self.nlp(potential_skill.lower())
                
                # Use vector similarity to match skills
                if potential_skill_doc and skill_doc:
                    similarity = potential_skill_doc.similarity(skill_doc)
                    if similarity > 0.85:  # Threshold for similarity
                        found_skills.append(skill)
                        break
        
        return found_skills
    
    def _calculate_confidence_scores(self, text, skills):
        """Calculate confidence score for each extracted skill"""
        skills_with_confidence = []
        
        for skill in skills:
            # Base confidence
            confidence = 0.7
            
            # Increase confidence if skill appears exactly in text
            skill_lower = skill.lower()
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, text):
                confidence += 0.2
            
            # Increase confidence if skill appears multiple times
            occurrences = len(re.findall(pattern, text))
            if occurrences > 1:
                confidence += min(0.1, occurrences * 0.02)  # Cap at 0.1
            
            skills_with_confidence.append({
                "skill": skill,
                "confidence": min(1.0, confidence)  # Cap at 1.0
            })
        
        # Sort by confidence
        skills_with_confidence.sort(key=lambda x: x["confidence"], reverse=True)
        
        return skills_with_confidence
    
    def categorize_skills(self, skills):
        """Categorize skills into technical, soft, and domain-specific"""
        # Predefined categories
        categories = {
            "technical": ["Python", "Java", "SQL", "Machine Learning", "AWS", "Docker"],
            "soft": ["Communication", "Leadership", "Problem Solving", "Teamwork"],
            "domain_specific": ["Finance", "Healthcare", "Marketing", "Engineering"]
        }
        
        categorized = {
            "technical": [],
            "soft": [],
            "domain_specific": [],
            "other": []
        }
        
        for skill_item in skills:
            skill = skill_item["skill"]
            categorized_flag = False
            
            for category, category_skills in categories.items():
                if any(category_skill.lower() in skill.lower() for category_skill in category_skills):
                    categorized[category].append(skill_item)
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                categorized["other"].append(skill_item)
        
        return categorized
