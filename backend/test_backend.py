# test_backend_intensive.py
import os
import sys
import json
from pathlib import Path
import traceback

# Test report setup
test_results = {
    "passed": [],
    "failed": []
}

def run_test(test_name, test_func):
    """Run a test and record its result"""
    print(f"\n{'='*50}\nTesting: {test_name}\n{'='*50}")
    try:
        test_func()
        test_results["passed"].append(test_name)
        print(f"✅ PASSED: {test_name}")
    except Exception as e:
        test_results["failed"].append(test_name)
        print(f"❌ FAILED: {test_name}")
        print(f"Error: {str(e)}")
        print(traceback.format_exc())

def test_resume_parser():
    """Test the resume parser functionality"""
    from backend.resume_parser import ResumeParser
    
    parser = ResumeParser()
    print("Resume parser initialized successfully")
    
    # Create a test PDF resume if none exists
    test_resume_path = Path("test_data/sample_resume.pdf")
    if not test_resume_path.exists():
        print("No sample resume found. Testing with mock data.")
        # Test with mock data
        mock_text = """
        John Doe
        Software Engineer
        
        SKILLS
        Python, Java, Machine Learning, Data Analysis
        
        EXPERIENCE
        Senior Developer at Tech Co (2020-Present)
        - Developed machine learning models
        - Led team of 5 engineers
        
        EDUCATION
        MS Computer Science, Stanford University (2018)
        """
        
        # Create mock resume data
        mock_resume = {
            "raw_text": mock_text,
            "skills": ["Python", "Java", "Machine Learning", "Data Analysis"],
            "experience": [{"title": "Senior Developer", "company": "Tech Co", "duration": "2020-Present"}],
            "education": [{"degree": "MS", "field": "Computer Science", "institution": "Stanford University", "year": "2018"}],
            "contact_info": {"email": "john.doe@example.com"}
        }
        
        # Test extraction methods
        assert parser.extract_skills(mock_text) == ["Python", "Java", "Machine Learning", "Data Analysis"], "Skills extraction failed"
        
        print("Resume parsing with mock data successful")
    else:
        # Test with actual PDF
        resume_data = parser.parse_document(file_path=str(test_resume_path))
        
        # Validate resume data
        assert resume_data.get("skills"), "No skills extracted"
        assert resume_data.get("experience"), "No experience extracted"
        assert resume_data.get("education"), "No education extracted"
        
        print(f"Skills found: {resume_data['skills']}")
        print(f"Experience entries: {len(resume_data['experience'])}")
        print(f"Education entries: {len(resume_data['education'])}")
        
    print("Resume parser passed all tests")

def test_job_fetcher():
    """Test the Arbeitnow job fetcher"""
    from backend.arbeitnow import ArbeitnowJobFetcher
    
    fetcher = ArbeitnowJobFetcher()
    print("Job fetcher initialized successfully")
    
    # Test job search with various parameters
    tech_jobs = fetcher.search_jobs("Python", count=3)
    assert len(tech_jobs) > 0, "No Python jobs found"
    print(f"Found {len(tech_jobs)} Python jobs")
    
    location_jobs = fetcher.search_jobs("Developer", location="Berlin", count=3)
    print(f"Found {len(location_jobs)} Developer jobs in Berlin")
    
    remote_jobs = fetcher.search_jobs("Data Scientist", experience_level="remote", count=3)
    print(f"Found {len(remote_jobs)} remote Data Scientist jobs")
    
    # Validate job data structure
    job = tech_jobs[0]
    required_fields = ["id", "title", "company", "location", "description", "required_skills"]
    for field in required_fields:
        assert field in job, f"Job missing required field: {field}"
    
    print("Job fetcher passed all tests")

def test_job_matcher():
    """Test the job matching algorithm"""
    from backend.matcher import JobMatcher
    from backend.resume_parser import ResumeParser
    from backend.arbeitnow import ArbeitnowJobFetcher
    
    # Create test data
    resume_data = {
        "skills": ["Python", "JavaScript", "Machine Learning", "SQL", "Data Analysis"],
        "experience": [
            {"title": "Data Scientist", "company": "AI Corp", "duration": "2020-Present"}
        ],
        "education": [
            {"degree": "MS", "field": "Data Science", "institution": "University X", "year": "2019"}
        ]
    }
    
    # Get real jobs from API
    fetcher = ArbeitnowJobFetcher()
    jobs = fetcher.search_jobs("Data", count=5)
    
    # Initialize matcher
    matcher = JobMatcher()
    print("Job matcher initialized successfully")
    
    # Test matching
    matches = matcher.match_jobs_to_resume(resume_data, jobs)
    assert len(matches) > 0, "No matches found"
    
    # Validate matching results
    for job_id, match_data in matches.items():
        assert "match_score" in match_data, "Match score missing"
        assert "match_details" in match_data, "Match details missing"
        assert 0 <= match_data["match_score"] <= 100, "Match score out of range"
        
        print(f"Job: {match_data['job_title']}, Score: {match_data['match_score']}%")
        
        # Check match details structure
        assert "skills_match" in match_data["match_details"], "Skills match details missing"
        assert "experience_match" in match_data["match_details"], "Experience match details missing"
        assert "education_match" in match_data["match_details"], "Education match details missing"
    
    print("Job matcher passed all tests")

def test_full_integration():
    """Test the full integration flow"""
    from backend.resume_parser import ResumeParser
    from backend.arbeitnow import ArbeitnowJobFetcher
    from backend.matcher import JobMatcher
    
    print("Testing full integration flow")
    
    # Step 1: Parse resume
    parser = ResumeParser()
    resume_data = {
        "skills": ["Python", "JavaScript", "React", "Data Analysis"],
        "experience": [{"title": "Frontend Developer", "company": "Web Solutions", "duration": "2019-2022"}],
        "education": [{"degree": "BS", "field": "Computer Science", "institution": "Tech University", "year": "2018"}]
    }
    
    # Step 2: Fetch jobs
    fetcher = ArbeitnowJobFetcher()
    jobs = fetcher.search_jobs("Developer", count=10)
    assert len(jobs) > 0, "No jobs found for integration test"
    
    # Step 3: Match jobs to resume
    matcher = JobMatcher()
    matches = matcher.match_jobs_to_resume(resume_data, jobs)
    assert len(matches) > 0, "No matches found in integration test"
    
    # Step 4: Rank and sort matches
    sorted_matches = sorted(
        [(job_id, data["match_score"]) for job_id, data in matches.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    # Print top matches
    print("\nTop 3 job matches:")
    for i, (job_id, score) in enumerate(sorted_matches[:3], 1):
        job = next(job for job in jobs if job["id"] == job_id)
        print(f"{i}. {job['title']} at {job['company']} - {score}% match")
    
    print("Full integration test completed successfully")

def create_test_directory():
    """Create test data directory if it doesn't exist"""
    os.makedirs("test_data", exist_ok=True)

if __name__ == "__main__":
    create_test_directory()
    
    # Run individual component tests
    run_test("Resume Parser", test_resume_parser)
    run_test("Job Fetcher", test_job_fetcher)
    run_test("Job Matcher", test_job_matcher)
    
    # Run integration test
    run_test("Full Integration", test_full_integration)
    
    # Print test summary
    print("\n" + "="*50)
    print(f"SUMMARY: {len(test_results['passed'])}/{len(test_results['passed']) + len(test_results['failed'])} tests passed")
    
    if test_results["failed"]:
        print("\nFailed tests:")
        for test in test_results["failed"]:
            print(f"- {test}")
    else:
        print("\nAll tests passed! Your backend is working correctly.")
