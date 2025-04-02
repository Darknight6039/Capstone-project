import streamlit as st

def show_about():
    st.title("About CV-LinkedIn Job Matcher")
    st.write("""
    This application helps you find the perfect job match based on your resume.
    
    It uses artificial intelligence to analyze your skills and experience, and 
    matches them with job opportunities from LinkedIn.
    
    **Created by Isaia Ebongue**
    """)
    
    # Contact info
    st.subheader("Contact")
    st.write("For more information, please contact isaiaebongue@icloud.com")
