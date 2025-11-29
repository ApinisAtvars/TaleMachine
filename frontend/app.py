import streamlit as st
import sys
import os
import uuid
import time
import asyncio

# Extend Python path for backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.agent import TaleMachineAgent
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'navigator_service')))
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'helper_services')))

# Session variables initialization
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""
if "session_id" not in st.session_state:
    st.session_state["session_id"] = None
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "sessions" not in st.session_state:
    st.session_state["sessions"] = {}
if "current_session_name" not in st.session_state:
    st.session_state["current_session_name"] = None

# def update_user_id():
#     """
#     Updates the user_id in session state and resets the session.
#     """
#     st.session_state.user_id = st.session_state["user_id_input"]
#     st.session_state.session_id = str(uuid.uuid4())
#     st.session_state.messages = [{
#         "role": "assistant",
#         "content": "What story would you like to create today?"
#     }]
#     st.session_state.sessions = {}
#     st.session_state.current_session_name = None

# with st.sidebar:

#     user_id = st.text_input(
#         "User ID",
#         value=st.session_state.get("user_id"),
#         key="user_id_input",
#         help="Enter your user ID for personalized experience",
#         on_change=update_user_id
#     )
#     if "sessions" not in st.session_state:
#         st.session_state.sessions = {}

if st.session_state.user_id:

    st.title("👻 TaleMachine")
    st.caption("🚀 Your creative writing helper")
    if not st.session_state["messages"]:
        st.session_state["messages"] = [{
            "role": "assistant",
            "content": "What story would you like to create today?"
        }]

    for idx, msg in enumerate(st.session_state.messages):
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        assistant_placeholder = st.empty()
        with assistant_placeholder.container():
            try:
                async def get_response():
                    full_message = ""
                    async for message in TaleMachineAgent.run(
                        user_id=st.session_state.user_id,
                        session_id=st.session_state.session_id,
                        question=prompt
                    ):
                        full_message += message
                        assistant_placeholder.chat_message("assistant").write(full_message)
                    return full_message if full_message else "No response generated"
                
                msg = asyncio.run(get_response())
            except Exception as e:
                msg = f"An error occurred: {str(e)}"
                st.error("An error occurred while processing your request. Please try again later.")
                print(f"Agent run error: {e}", file=sys.stderr)

        st.session_state.messages.append({"role": "assistant", "content": msg})

else:
    st.title("👻 TaleMachine")
    st.caption("🚀 Your creative writing helper")
    st.info("Please enter your User ID in the sidebar to start chatting.")