import streamlit as st
import sys
import os
import uuid
import time
import asyncio

# Extend Python path for backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.agent import TaleMachineAgent

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

def get_async_loop() -> asyncio.AbstractEventLoop:
    """Return a persistent event loop so MCP sessions stay alive across turns."""
    if "async_loop" not in st.session_state:
        st.session_state.async_loop = asyncio.new_event_loop()
    return st.session_state.async_loop


def run_asyncio_task(coro):
    loop = get_async_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def update_user_id():
    """
    Updates the user_id in session state and resets the session.
    """
    st.session_state.user_id = st.session_state["user_id_input"]
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = [{
        "role": "assistant",
        "content": "What story would you like to create today?"
    }]
    st.session_state.sessions = {}
    st.session_state.current_session_name = None

with st.sidebar:

    user_id = st.text_input(
        "User ID",
        value=st.session_state.get("user_id"),
        key="user_id_input",
        help="Enter your user ID for personalized experience",
        on_change=update_user_id
    )
    if "sessions" not in st.session_state:
        st.session_state.sessions = {}

if st.session_state.user_id:

    st.title("👻 TaleMachine")
    st.caption("🚀 Your creative writing helper")
    if not st.session_state["messages"]:
        st.session_state["messages"] = [{
            "role": "assistant",
            "content": "What story would you like to create today?"
        }]

    for idx, msg in enumerate(st.session_state.messages):
        # Check if message contains base64 image
        if "data:image/png;base64," in msg["content"]:
            parts = msg["content"].split("data:image/png;base64,")
            with st.chat_message(msg["role"]):
                if parts[0].strip():
                    st.write(parts[0].strip())
                st.image(f"data:image/png;base64,{parts[1]}", width="stretch")
        else:
            st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Create a copy for the agent with images omitted
        messages_for_agent = []
        messages = st.session_state.messages[-10:] if len(st.session_state.messages) > 10 else st.session_state.messages
        for message in messages:
            if "data:image/png;base64," in message["content"]:
                message_updated = {
                    "role": message["role"],
                    "content": "Image content omitted for context management."
                }
                messages_for_agent.append(message_updated)
            else:
                messages_for_agent.append(message)

        st.chat_message("user").write(prompt)
        assistant_placeholder = st.empty()
        with assistant_placeholder.container():
            try:
                async def get_response():
                    full_message = ""
                    async for message in TaleMachineAgent.run(
                        messages=messages_for_agent
                    ):
                        full_message += message
                        # Check if message contains base64 image data
                        if "data:image/png;base64," in full_message:
                            # Split text and image
                            parts = full_message.split("data:image/png;base64,")
                            with assistant_placeholder.chat_message("assistant"):
                                if parts[0].strip():
                                    st.write(parts[0].strip())
                                # Display image
                                st.image(f"data:image/png;base64,{parts[1]}", width="stretch")
                        else:
                            assistant_placeholder.chat_message("assistant").write(full_message)
                    return full_message if full_message else "No response generated"
                
                msg = run_asyncio_task(get_response())
            except Exception as e:
                msg = f"An error occurred: {str(e)}"
                st.error("An error occurred while processing your request. Please try again later.")
                print(f"Agent run error: {e}", file=sys.stderr)

        st.session_state.messages.append({"role": "assistant", "content": msg})

else:
    st.title("👻 TaleMachine")
    st.caption("🚀 Your creative writing helper")
    st.info("Please enter your User ID in the sidebar to start chatting.")