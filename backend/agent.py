import asyncio
import os
import sys
from typing import AsyncGenerator
import streamlit as st
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv
load_dotenv("env/.viola.env")

class TaleMachineAgent:
    _llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=os.getenv("GEMINI_API_KEY"))
    _prompt = "You are an advanced storytelling AI named TaleMachine that helps users create engaging and interactive stories."

    def _initialize_agent(tools: list, prompt: str):
        agent = create_agent(
            model=TaleMachineAgent._llm, 
            tools=tools, 
            system_prompt=prompt, 
            interrupt_before=[]) # interrupt before saving the story
        return agent
    
    @staticmethod
    async def run(user_id: str, session_id: str, question: str):
        agent = TaleMachineAgent._initialize_agent(tools=[], prompt=TaleMachineAgent._prompt)
        async for chunk in agent.astream(
            input={"messages": [HumanMessage(content=question)]},
            stream_mode="messages",
            callbacks=[StreamlitCallbackHandler(st.container())]
        ):
            if isinstance(chunk, tuple):
                message, metadata = chunk
                yield message.content
            else:
                yield chunk.content