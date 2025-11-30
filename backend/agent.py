import asyncio
import base64
import os
import sys
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
import streamlit as st
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain.agents import create_agent
from langchain.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.tools import tool
from google.oauth2 import service_account
from google import genai
from google.genai import types
from mcp.types import (
    CallToolResult,
    TextContent,
)

from langchain_mcp_adapters.interceptors import (
    MCPToolCallRequest,
)

from dotenv import load_dotenv
load_dotenv("env/.viola.env")

class TaleMachineAgent:
    _llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=os.getenv("GEMINI_API_KEY"))
    _prompt = PromptTemplate.from_template(
        "You are an advanced storytelling AI named TaleMachine that helps users create engaging and interactive stories. Right now, you are working with the following story: {story_name}\n\n" \
        "When responding to user queries, make sure to use the tools available to you to fetch relevant story details from the database or save new story content as needed. " \
        "Always aim to enhance the user's storytelling experience by providing creative and contextually appropriate responses.")
    
    _mcp_server_url = os.getenv("MCP_SERVER_URL")
    _checkpointer = MemorySaver()

    @staticmethod
    def _initialize_agent(tools: list, prompt: str):
        agent = create_agent(
            model=TaleMachineAgent._llm, 
            tools=tools, 
            system_prompt=prompt, 
            checkpointer=TaleMachineAgent._checkpointer,
        )
        return agent
    
    async def ask_approval_interceptor(
        request: MCPToolCallRequest,
        handler,
    ) -> CallToolResult:
        if request.name == "save_story":
            # Raise interrupt to pause execution
            value = interrupt("Story save requested. Do you want to proceed? Story: " + request.args.get("story_content", ""))
            print(f"Interrupt value: {value}", file=sys.stderr)
            if value == "Action cancelled by user":
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="Story save action was cancelled by the user."
                    )],
                    isError=False,
                )

        # Execute the tool
        result = await handler(request)

        if result:
            print(f"Tool {request.name} executed with result: {result.content}", file=sys.stderr)

        return result
    
    # Separate tool for image generation that returns a direct answer to the user
    @tool(return_direct=True)
    async def generate_image(description: str) -> str:
        """
        Generate an image based on the provided description. Only the image is returned to the user.
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
                img_bytes = part.inline_data.data
                img_str = base64.b64encode(img_bytes).decode()
                if part.text is not None:
                    return f"{part.text}\n\ndata:image/png;base64,{img_str}"
                return f"data:image/png;base64,{img_str}"
            
        return "No image generated"
    
    @staticmethod
    async def run(messages: list, story_name: str, thread_id: str):
        """Run the agent with a specific thread ID for checkpoint management."""
        try:
            async with streamablehttp_client(TaleMachineAgent._mcp_server_url) as connection:
                if isinstance(connection, tuple) and len(connection) >= 2:
                    read_stream, write_stream = connection[0], connection[1]
                else:
                    read_stream = connection.read
                    write_stream = connection.write

                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await load_mcp_tools(session, tool_interceptors=[TaleMachineAgent.ask_approval_interceptor])
                    tools.append(TaleMachineAgent.generate_image)

                    agent = TaleMachineAgent._initialize_agent(
                        tools=tools,
                        prompt=TaleMachineAgent._prompt.format(story_name=story_name)
                    )

                    # Create thread config with thread_id
                    config = {
                        "configurable": {
                            "thread_id": thread_id
                        }
                    }

                    stream = agent.astream(
                        input={"messages": messages},
                        config=config,
                        stream_mode=["messages", "values"],
                    )
                    
                    async for chunk in stream:
                        try:
                            if isinstance(chunk, tuple):
                                stream_mode, values = chunk
                                if stream_mode == "messages":
                                    if isinstance(values, tuple):
                                        message, metadata = values
                                        if isinstance(message, AIMessage) and message.content:
                                            yield message.content
                                elif stream_mode == "values":
                                    if "__interrupt__" in values:
                                        print("\nDetected interrupt in agent stream", file=sys.stderr)
                                        # Extract interrupt message
                                        interrupt_info = values.get("__interrupt__", "")
                                        if interrupt_info:
                                            interrupt_msg = interrupt_info[0].value if interrupt_info else "Approval required"
                                            yield f"__interrupt__:{interrupt_msg}"
                        except Exception as chunk_error:
                            print(f"Error processing chunk: {chunk_error}", file=sys.stderr)
                            import traceback
                            traceback.print_exc()
                            continue

        except Exception as e:
            print(f"Error in TaleMachineAgent run: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            raise e

    @staticmethod
    async def resume_after_interrupt(thread_id: str, approved: bool, story_name: str):
        """Resume agent execution after an interrupt with approval/rejection."""
        try:
            async with streamablehttp_client(TaleMachineAgent._mcp_server_url) as connection:
                if isinstance(connection, tuple) and len(connection) >= 2:
                    read_stream, write_stream = connection[0], connection[1]
                else:
                    read_stream = connection.read
                    write_stream = connection.write

                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await load_mcp_tools(session, tool_interceptors=[TaleMachineAgent.ask_approval_interceptor])
                    tools.append(TaleMachineAgent.generate_image)

                    agent = TaleMachineAgent._initialize_agent(
                        tools=tools,
                        prompt=TaleMachineAgent._prompt.format(story_name=story_name)
                    )

                    config = {
                        "configurable": {
                            "thread_id": thread_id
                        }
                    }

                    if approved:
                        # Resume with None to continue execution
                        command = Command(resume=True)
                    else:
                        # Send a Command to cancel the current operation
                        command = Command(resume="Action cancelled by user")
                    
                    stream = agent.astream(
                        input=command,
                        config=config,
                        stream_mode=["messages", "values"]
                    )
                    
                    async for chunk in stream:
                        try:
                            if isinstance(chunk, tuple):
                                stream_mode, values = chunk
                                if stream_mode == "messages":
                                    if isinstance(values, tuple):
                                        message, metadata = values
                                        if message.content:
                                            yield message.content
                        except Exception as chunk_error:
                            print(f"Error processing chunk: {chunk_error}", file=sys.stderr)
                            import traceback
                            traceback.print_exc()
                            continue

        except Exception as e:
            print(f"Error in resume_after_interrupt: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            raise e


def main():
    messages = [
        {"role": "user", "content": "Find chapters in my story about a brave knight for user123 and session abc."}
    ]
    thread_id = "test_thread_123"
    session_name = "Knights and Dragons"
    async def run_agent():
        async for response in TaleMachineAgent.run(messages, session_name, thread_id):
            print(response)
    
    asyncio.run(run_agent())

if __name__ == "__main__":
    main()