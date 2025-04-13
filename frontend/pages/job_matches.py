import streamlit as st
import asyncio
from backend.arbeitnow import ArbeitnowJobFetcher
from backend.hybrid_matcher import HybridJobMatcher
from frontend.components.job_card import JobCard

def show_job_matches():
    st.title("Job Matches")
    
    # Job search parameters
    col1, col2 = st.columns(2)
    with col1:
        keywords = st.text_input("Job Title/Keywords", "Data Scientist")
    with col2:
        experience_level = st.select_slider(
            "Experience Level",
            options=["Entry", "Associate", "Mid-Senior", "Director", "Executive"]
        )
    
    # Language filter
    language = st.selectbox("Language", ["English", "German", "French", "Any"])

    # Search button
    search_clicked = st.button("Search Jobs", type="primary")
    
    # Display results
    if search_clicked or "job_matches" in st.session_state:
        if search_clicked:
            with st.spinner("Searching for matching jobs..."):
                # Fetch jobs
                job_fetcher = ArbeitnowJobFetcher()
                jobs = job_fetcher.search_jobs(
                    keywords=keywords,
                    experience_level=experience_level,
                    language=language
                )
                
                if not jobs:
                    st.error("No jobs found matching your criteria. Try different keywords.")
                    return

                # Use hybrid matcher
                matcher = HybridJobMatcher()
                matched_jobs = []
                
                # Process matches in parallel
                async def process_matches():
                    tasks = []
                    for job in jobs:
                        task = asyncio.create_task(
                            matcher.calculate_match_score(
                                st.session_state.resume_data,
                                job
                            )
                        )
                        tasks.append((job, task))
                    
                    for job, task in tasks:
                        match_result = await task
                        matched_jobs.append({
                            "job_data": job,
                            "match_score": match_result["score"],
                            "match_details": match_result["details"]
                        })
                
                # Run matching
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(process_matches())
                finally:
                    loop.close()
                
                # Sort by match score
                matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
                st.session_state.job_matches = matched_jobs
        
        # Display job matches
        st.subheader(f"Found {len(st.session_state.job_matches)} matching jobs")
        
        # Filter controls
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
