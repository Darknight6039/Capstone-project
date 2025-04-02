import streamlit as st
from frontend.pages.resume_upload import show_resume_upload
from frontend.pages.job_matches import show_job_matches
from frontend.pages.career_insights import show_career_insights
from frontend.pages.about import show_about
from frontend.components.chat_widget import ChatWidget

def run_streamlit_app():
    # Set page configuration
    st.set_page_config(
        page_title="CV-LinkedIn Job Matcher",
        page_icon="💼",
        layout="wide"
    )

    # Initialize session state variables
    if 'page' not in st.session_state:
        st.session_state.page = "home"
        
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        
    if 'resume_data' not in st.session_state:
        st.session_state.resume_data = None
        
    if 'job_matches' not in st.session_state:
        st.session_state.job_matches = []

    # Sidebar navigation
    with st.sidebar:
        st.title("CV-LinkedIn Job Matcher")
        st.write("Find your perfect job match")
        st.divider()
        
        # Navigation callback functions
        def navigate_to_home():
            st.session_state.page = "home"
            
        def navigate_to_resume_upload():
            st.session_state.page = "resume_upload"
            
        def navigate_to_job_matches():
            st.session_state.page = "job_matches"
            
        def navigate_to_career_insights():
            st.session_state.page = "career_insights"
            
        def navigate_to_about():
            st.session_state.page = "about"
        
        # Navigation buttons with callbacks
        st.button("🏠 Home", key="nav_home", 
                 on_click=navigate_to_home, 
                 use_container_width=True)
        
        st.button("📄 Upload Resume", key="nav_upload_resume", 
                 on_click=navigate_to_resume_upload, 
                 use_container_width=True)
        
        # Only enable job matches button if resume data exists
        job_matches_button = st.button("🔍 Job Matches", key="nav_job_matches", 
                                      on_click=navigate_to_job_matches, 
                                      disabled=st.session_state.resume_data is None,
                                      use_container_width=True)
        
        st.button("📈 Career Insights", key="nav_career_insights", 
                 on_click=navigate_to_career_insights, 
                 use_container_width=True)
        
        st.button("ℹ️ About", key="nav_about", 
                 on_click=navigate_to_about, 
                 use_container_width=True)
        
        # Footer
        st.divider()
        st.write("Created by Isaia Ebongue")

    # Render the appropriate page based on the current page state
    if st.session_state.page == "home":
        # Home page content
        st.title("Welcome to CV-LinkedIn Job Matcher")
        st.write("""
        This application helps you find the perfect job match based on your CV.
        
        **How it works:**
        1. Upload your resume
        2. Our AI analyzes your skills and experience
        3. View matching job opportunities from LinkedIn
        4. Get personalized career advice
        """)
        
        # Call-to-action button
        if st.button("Get Started", type="primary"):
            st.session_state.page = "resume_upload"
            st.rerun()
            
    elif st.session_state.page == "resume_upload":
        # Show resume upload page
        show_resume_upload()
        
    elif st.session_state.page == "job_matches":
        # Show job matches page with validation
        if st.session_state.resume_data is None:
            st.warning("Please upload your resume first")
            st.session_state.page = "resume_upload"
            st.rerun()
        else:
            show_job_matches()
            
    elif st.session_state.page == "career_insights":
        # Show career insights page
        show_career_insights()
        
    elif st.session_state.page == "about":
        # Show about page
        show_about()
    
    # Chat widget (displayed on all pages except home)
    if st.session_state.page != "home":
        chat_widget = ChatWidget()
        chat_widget.display()
