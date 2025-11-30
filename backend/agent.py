import asyncio
import base64
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
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.tools import tool
from google.oauth2 import service_account
from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv("env/.viola.env")

class TaleMachineAgent:
    _llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=os.getenv("GEMINI_API_KEY"))
    _prompt = "You are an advanced storytelling AI named TaleMachine that helps users create engaging and interactive stories."
    _mcp_server_url = os.getenv("MCP_SERVER_URL")

    @staticmethod
    def _initialize_agent(tools: list, prompt: str):
        agent = create_agent(
            model=TaleMachineAgent._llm, 
            tools=tools, 
            system_prompt=prompt, 
            interrupt_before=[])
        return agent
    
    # Separate tool for image generation that returns a direct answer to the user instead of the model (to avoid token limits)
    @tool(return_direct=True)
    async def generate_image(description: str) -> str:
        """
        Generate an image based on the provided description.
        """
        credentials = None
        service_account_path = os.getenv("VERTEX_SERVICE_ACCOUNT_LOCATION")
        if service_account_path and os.path.exists(service_account_path):
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )

        client = genai.Client(
            project=os.getenv("VERTEX_PROJECT_ID"), 
            vertexai=True, 
            location=os.getenv("VERTEX_PROJECT_LOCATION"),
            credentials=credentials 
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[f"{description}, high resolution, detailed, realistic"],
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                    image_size="1K"
                )
            ),
        )
        
        for part in response.parts:
            if part.inline_data is not None:
                # Get the raw image bytes directly from inline_data
                img_bytes = part.inline_data.data
                img_str = base64.b64encode(img_bytes).decode()
                if part.text is not None:
                    return f"{part.text}\n\ndata:image/png;base64,{img_str}"
                return f"data:image/png;base64,{img_str}"
            
        return "No image generated"
    
    @staticmethod
    async def run(messages: list):
        try:
            async with streamablehttp_client(TaleMachineAgent._mcp_server_url) as connection:
                if isinstance(connection, tuple) and len(connection) >= 2:
                    read_stream, write_stream = connection[0], connection[1]
                else:  # Fallback for any object-style return
                    read_stream = connection.read
                    write_stream = connection.write

                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await load_mcp_tools(session)
                    tools.append(TaleMachineAgent.generate_image)

                    TaleMachineAgentAgent = TaleMachineAgent._initialize_agent(
                        tools=tools,
                        prompt=TaleMachineAgent._prompt
                    )

                    stream = TaleMachineAgentAgent.astream(
                        input={"messages": messages},
                        stream_mode="messages",
                        callbacks=[StreamlitCallbackHandler(st.container())]
                    )
                    async for chunk in stream:
                        try:
                            if isinstance(chunk, tuple):
                                message, _metadata = chunk
                                if message.content:
                                    yield message.content
                            else:
                                if chunk.content:
                                    yield chunk.content
                        except Exception as chunk_error:
                            print(f"Error processing chunk: {chunk_error}", file=sys.stderr)
                            import traceback
                            traceback.print_exc()
                            continue

        except ExceptionGroup as eg:
            print(f"ExceptionGroup in TaleMachineAgent run:", file=sys.stderr)
            for i, exc in enumerate(eg.exceptions):
                print(f"  Exception {i}: {type(exc).__name__}: {exc}", file=sys.stderr)
                import traceback
                traceback.print_exception(type(exc), exc, exc.__traceback__)
            raise
        except Exception as e:
            print(f"Error in TaleMachineAgent run: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            raise e

if __name__ == "__main__":
    TaleMachineAgent._initialize_agent([], TaleMachineAgent._prompt)