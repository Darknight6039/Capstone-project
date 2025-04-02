import streamlit as st
import plotly.graph_objects as go
from bs4 import BeautifulSoup

class JobCard:
    def __init__(self, job_data, match_score, match_details):
        self.job_data = job_data
        self.match_score = match_score
        self.match_details = match_details
        
    def display(self):
        """Display a job card with match information"""
        with st.container():
            # Card header with title and match score
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(self.job_data["title"])
                st.write(f"**{self.job_data['company']}** • {self.job_data['location']}")
            with col2:
                # Display match score with color coding
                score_color = "#5FD068" if self.match_score >= 80 else "#FFC107" if self.match_score >= 60 else "#EF6262"
                st.markdown(f"""
                <div style="
                    background-color: {score_color};
                    padding: 10px;
                    border-radius: 10px;
                    text-align: center;
                    color: white;
                    font-weight: bold;
                ">
                    Match<br>{self.match_score}%
                </div>
                """, unsafe_allow_html=True)
            
            # Job details with proper HTML rendering
            with st.expander("Job Description"):
                description = self.job_data.get("description", "No description available")
                
                # Clean HTML tags if present
                if "<" in description and ">" in description:
                    try:
                        # Use BeautifulSoup to clean and format HTML
                        soup = BeautifulSoup(description, "html.parser")
                        # Either render as HTML or clean it
                        st.markdown(description, unsafe_allow_html=True)
                    except Exception:
                        # Fallback if BeautifulSoup fails
                        st.write(description)
                else:
                    # If already clean, just display
                    st.write(description)
            
            # Skills match visualization
            st.subheader("Skills Match")
            required_skills = self.job_data.get("required_skills", [])
            
            if required_skills:
                # Get matched and missing skills
                matched_skills = self.match_details.get("matched_skills", [])
                missing_skills = [skill for skill in required_skills if skill not in matched_skills]
                
                # Display as two columns
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 👍 Matched Skills")
                    if matched_skills:
                        for skill in matched_skills:
                            st.markdown(f"- :green[{skill}]")
                    else:
                        st.write("No skills matched.")
                        
                with col2:
                    st.markdown("#### 📚 Skills to Develop")
                    if missing_skills:
                        for skill in missing_skills:
                            st.markdown(f"- :orange[{skill}]")
                    else:
                        st.write("You have all the required skills!")
            
            # Action buttons with corrected session state keys
            job_id = self.job_data.get('id', 'job')
            
            # Use different keys for session state than the button keys
            apply_state_key = f"applied_status_{job_id}"
            advice_state_key = f"advice_status_{job_id}"
            
            def on_apply_click():
                st.session_state[apply_state_key] = True
                
            def on_advice_click():
                # Navigate to career insights when clicking advice button
                st.session_state[advice_state_key] = True
                st.session_state.page = "career_insights"
            
            col1, col2 = st.columns(2)
            with col1:
                st.button("💼 Apply Now", 
                          key=f"apply_{job_id}", 
                          on_click=on_apply_click)
            with col2:
                st.button("💬 Get Career Advice", 
                          key=f"advice_{job_id}", 
                          on_click=on_advice_click)
            
            # Show content based on button clicks
            if st.session_state.get(apply_state_key, False):
                st.success("Application submitted successfully!")
            
            st.divider()  # Visual separation between cards
