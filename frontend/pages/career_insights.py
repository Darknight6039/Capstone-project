import streamlit as st
import asyncio
from backend.recommender import CandidateRecommender
from backend.openai_client import get_openai_client
import json

def show_career_insights():
    st.title("Career Insights")
    st.write("Get personalized advice to improve your job prospects")

    # Initialize recommender
    recommender = CandidateRecommender()

    # Add personal insights based on CV even without job matches
    if st.session_state.resume_data:
        st.subheader("Personal Career Profile")
        
        skills = st.session_state.resume_data.get("skills", [])
        experience = st.session_state.resume_data.get("experience", [])
        education = st.session_state.resume_data.get("education", [])
        
        # Display resume overview
        st.write("### Your Profile Overview")
        st.write(f"**Skills:** {', '.join(skills)}")
        
        # Generate personalized career path suggestions
        client = get_openai_client()
        advice_prompt = f"""
        Based on this resume data:
        - Skills: {', '.join(skills)}
        - Experience: {str(experience)}
        - Education: {str(education)}
        
        Provide detailed career advice including:
        1. Career path suggestions (3-4 potential paths)
        2. Top 5 skills to develop for career advancement
        3. Industry trends relevant to this profile
        4. Recommended certifications or additional training
        
        Format the response in markdown for better readability.
        """
        
        with st.expander("Career Path Analysis", expanded=True):
            with st.spinner("Analyzing your career profile..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a career advisor specialized in providing personalized insights."},
                        {"role": "user", "content": advice_prompt}
                    ]
                )
                
                # Display the advice
                st.markdown(response.choices[0].message.content)

    # Select a job to get advice for
    if st.session_state.job_matches:
        st.subheader("Job-Specific Advice")
        job_titles = [f"{j['job_data']['title']} at {j['job_data']['company']} ({j['match_score']}% match)" 
                      for j in st.session_state.job_matches]
        selected_job_index = st.selectbox(
            "Select a job to get specific advice for:",
            range(len(job_titles)),
            format_func=lambda i: job_titles[i]
        )
        
        selected_job = st.session_state.job_matches[selected_job_index]

        # Generate advice
        if st.button("Generate Advice", type="primary"):
            with st.spinner("Generating personalized advice..."):
                # Get improvement suggestions
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    suggestions = loop.run_until_complete(
                        recommender.generate_improvement_suggestions(
                            st.session_state.resume_data,
                            selected_job["job_data"],
                            selected_job["match_details"]
                        )
                    )
                finally:
                    loop.close()

                # Display suggestions
                st.subheader("How to Improve Your Match")
                
                # Skills suggestions
                st.markdown("### Skills to Develop")
                for skill in suggestions.get("skills_to_develop", []):
                    st.markdown(f"- **{skill['skill']}**: {skill['reason']}")
                
                # Resume improvements
                st.markdown("### Resume Enhancements")
                for tip in suggestions.get("resume_improvements", []):
                    st.markdown(f"- {tip}")
                
                # Stand out strategies
                st.markdown("### How to Stand Out From Other Candidates")
                for strategy in suggestions.get("differentiation_strategies", []):
                    st.markdown(f"- {strategy}")
                
                # Enhanced interview preparation
                st.markdown("### Interview Preparation")
                
                # Generate more comprehensive interview prep with OpenAI
                job = selected_job['job_data']
                skills = st.session_state.resume_data.get("skills", [])
                
                client = get_openai_client()
                interview_prompt = f"""
                Create comprehensive interview preparation for a {job['title']} position at {job['company']}.
                
                Include:
                1. 10 likely technical questions and ideal answers
                2. 5 behavioral questions with STAR method answers
                3. 3 questions to ask the interviewer
                4. Salary negotiation tips for this specific role
                5. Key points to emphasize about my skills: {', '.join(skills)}
                
                Format the response in markdown with proper headers and bullet points.
                """
                
                with st.spinner("Generating interview preparation..."):
                    interview_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are an interview coach with expertise in job preparation."},
                            {"role": "user", "content": interview_prompt}
                        ]
                    )
                    
                    # Display enhanced interview prep before original questions
                    st.markdown(interview_response.choices[0].message.content)
                    
                    # Display original questions as expanders
                    st.markdown("### Additional Questions")
                    for question in suggestions.get("potential_questions", []):
                        with st.expander(question["question"]):
                            st.write(question["approach"])
    else:
        if not st.session_state.resume_data:
            st.info("Please upload your resume first to get personalized career insights.")
        else:
            st.info("Please search for job matches to get job-specific advice.")
            