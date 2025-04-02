import streamlit as st
import os
import tempfile
from backend.resume_parser import ResumeParser
import PyPDF2
import docx2txt
import json

def show_resume_upload():
    st.title("Upload Your Resume")
    st.write("Upload your resume to find matching job opportunities on LinkedIn")

    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf", "docx"])

    if uploaded_file:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_filepath = tmp_file.name

        try:
            # Process the resume
            with st.spinner("Analyzing your resume..."):
                # Extract text from the file
                resume_text = ""
                if uploaded_file.name.lower().endswith('.pdf'):
                    with open(tmp_filepath, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        for page in reader.pages:
                            page_text = page.extract_text()
                            resume_text += page_text + "\n"
                            # Debug: Preview extracted text
                            print(f"Extracted text from page: {page_text[:100]}...")
                elif uploaded_file.name.lower().endswith(('.docx', '.doc')):
                    resume_text = docx2txt.process(tmp_filepath)

                # Log the extracted text
                print(f"Total extracted text length: {len(resume_text)} chars")
                print(f"Text sample: {resume_text[:300]}...")
                
                # Now pass both resume_text and file_path to parse_document
                parser = ResumeParser()
                resume_data = parser.parse_document(resume_text=resume_text, file_path=tmp_filepath)
                st.session_state.resume_data = resume_data
                
                # Debug: Inspect the parsed data
                print(f"Parsed data keys: {resume_data.keys() if isinstance(resume_data, dict) else 'Not a dict'}")

                # Display success message
                st.success("Resume analysis complete!")

                # Debug display to see raw data - can be removed in production
                with st.expander("Debug: View Parsed Data"):
                    st.json(resume_data)

                # Show extracted information
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Identified Skills")
                    if "skills" in resume_data and isinstance(resume_data["skills"], list) and resume_data["skills"]:
                        for skill in resume_data["skills"][:10]:  # Show top 10 skills
                            st.write(f"- {skill}")
                        if len(resume_data["skills"]) > 10:
                            st.write(f"... and {len(resume_data['skills']) - 10} more")
                    elif "raw_content" in resume_data:
                        st.write("Skills extraction failed. Raw data available in debug section.")
                    else:
                        st.write("No skills identified. Try another resume format.")

                with col2:
                    st.subheader("Experience")
                    if "experience" in resume_data and isinstance(resume_data["experience"], list) and resume_data["experience"]:
                        for job in resume_data["experience"]:
                            st.write(f"**{job.get('title', 'Unknown Title')}** at {job.get('company', 'Unknown Company')}")
                            st.write(f"_{job.get('duration', 'Unknown Duration')}_")
                    elif "raw_content" in resume_data:
                        st.write("Experience extraction failed. Raw data available in debug section.")
                    else:
                        st.write("No experience identified. Try another resume format.")

                # Next steps
                st.subheader("Next Steps")
                if st.button("Find Matching Jobs on LinkedIn", type="primary"):
                    st.session_state.page = "job_matches"

        except Exception as e:
            st.error(f"Error processing resume: {str(e)}")
            import traceback
            print(traceback.format_exc())  # Print full stack trace
        finally:
            # Clean up temporary file
            os.unlink(tmp_filepath)
