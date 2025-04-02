import streamlit as st
from backend.conversation import ChatbotConversation

class ChatWidget:
    def __init__(self):
        """Initialize chat conversation handler"""
        self.conversation = ChatbotConversation()

    def display(self):
        st.divider()
        
        # Chat title
        st.subheader("Chat with Career Assistant")
        
        # Display history in an expander
        with st.expander("Chat History", expanded=False):
            # Display chat history
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Chat input outside the expander
        prompt = st.chat_input("Ask me about job matches or career advice...")
        
        if prompt:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate and display response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # FIXED: Added missing closing parenthesis
                    response = self.conversation.process_message(
                        prompt,
                        resume_data=st.session_state.get("resume_data"),
                        job_matches=st.session_state.get("job_matches", [])
                    )
                    st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
