import streamlit as st
import asyncio
from backend.arbeitnow import ArbeitnowJobFetcher
from backend.matcher import JobMatcher
from frontend.components.job_card import JobCard

def show_job_matches():
    st.title("Job Matches")
    
    # Job search parameters - Removed location as requested
    keywords = st.text_input("Job Title/Keywords", "Data Scientist")
    
    experience_level = st.select_slider(
        "Experience Level",
        options=["Entry", "Associate", "Mid-Senior", "Director", "Executive"]
    )
    
    # Language filter to ensure proper results
    language = st.selectbox("Language", ["English", "German", "French", "Any"])

    # Search button
    search_clicked = st.button("Search Jobs", type="primary")
    
    # Condition to display results
    if search_clicked or len(st.session_state.job_matches) > 0:
        # Retrieve new jobs only if a search is requested
        if search_clicked:
            with st.spinner("Searching for matching jobs..."):
                # Fetch jobs from LinkedIn
                job_fetcher = ArbeitnowJobFetcher()
                jobs = job_fetcher.search_jobs(
                    keywords=keywords,
                    # location removed
                    experience_level=experience_level,
                    language=language
                )

                # Match jobs with resume
                matcher = JobMatcher()
                matched_jobs = []
                
                # Use asyncio to run matching in parallel
                async def process_matches():
                    tasks = []
                    for job in jobs:
                        task = asyncio.create_task(matcher.calculate_match_score(
                            st.session_state.resume_data,
                            job
                        ))
                        tasks.append((job, task))
                    
                    for job, task in tasks:
                        match_result = await task
                        matched_jobs.append({
                            "job_data": job,
                            "match_score": match_result["score"],
                            "match_details": match_result["details"]
                        })
                
                # Run the async task
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(process_matches())
                finally:
                    loop.close()
                
                # Sort by match score (descending)
                matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
                st.session_state.job_matches = matched_jobs
        
        # Display job matches
        st.subheader(f"Found {len(st.session_state.job_matches)} matching jobs")
        
        # Filters
        min_match = st.slider("Minimum Match Score", 0, 100, 50)
        filtered_jobs = [j for j in st.session_state.job_matches if j["match_score"] >= min_match]
        
        # Show job cards
        if filtered_jobs:
            for job_match in filtered_jobs:
                job_card = JobCard(
                    job_data=job_match["job_data"],
                    match_score=job_match["match_score"],
                    match_details=job_match["match_details"]
                )
                job_card.display()
        else:
            st.info("No jobs match your current filters. Try lowering the minimum match score.")
