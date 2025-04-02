# Make key classes available at the package level
from backend.resume_parser import ResumeParser
from backend.arbeitnow import ArbeitnowJobFetcher
from backend.matcher import JobMatcher
from backend.recommender import CandidateRecommender
from backend.conversation import ChatbotConversation
from backend.openai_resume_extractor import OpenAIResumeExtractor