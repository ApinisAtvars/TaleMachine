import asyncio
import base64
import os
import sys
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
# import streamlit as st
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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.postgres.Image import ImageBase

from dotenv import load_dotenv
load_dotenv()

class TaleMachineAgentService:
    _llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=os.getenv("GEMINI_API_KEY"))
    _prompt = PromptTemplate.from_template(
        """
        You are TaleMachine, an advanced storytelling AI and collaborative co-author.
        Your role is to assist the user in writing and managing their story with precision and creativity.

        CURRENT CONTEXT
        - Story Title: {story_name}
        - Story ID: {story_id}

        *** STRICT OPERATIONAL PROTOCOLS ***

        1. DRAFTING PHASE
        - When asked to write content, you must ALWAYS generate the text in the chat window first.
        - You are prohibited from calling the `save_chapter` tool during the initial drafting phase.
        - Even if the user says "Write and save," you must reply: "I have drafted the content below. Please review it. Shall I save this to the database?"

        2. REVIEW PHASE
        - Explicitly ask for user approval before saving.
        - Do not assume silence or vague responses imply consent to save.

        3. SAVING PHASE
        - execute the `save_chapter` tool ONLY when the user gives an explicit command (e.g., "Save it", "Looks good", "Commit").
        - When saving, strip all conversational filler, markdown headers (like '## Chapter 1'), and titles from the `content` field. The `content` field must contain the story body text only.

        *** ANTI-HALLUCINATION & TRUTH GUIDELINES ***

        - VERIFICATION OF ACTION: You are forbidden from stating "I have saved the chapter" or "The story is updated" unless you are simultaneously calling the `save_chapter` tool in that exact response turn.
        - ACCURACY: If you are not calling the tool, you must use future-tense phrasing, such as "I am ready to save this" or "Waiting for your confirmation to save."
        - DATA INTEGRITY: Never invent or hallucinate success messages. If the tool is not called, the data is not saved.

        *** GENERAL BEHAVIOR ***
        - Use your tools to fetch story details or generate images when contextually appropriate.
        - Do not mention internal IDs (UUIDs) in your text response unless specifically asked.
        - Maintain the requested narrative tone and style strictly.
        """
    )
    _mcp_server_url = os.getenv("MCP_SERVER_URL")
    _checkpointer = MemorySaver()

    # Tool interceptor to ask for user approval before saving a story
    async def ask_approval_interceptor(
        request: MCPToolCallRequest,
        handler,
    ) -> CallToolResult:
        if request.name == "save_chapter" or request.name == "delete_chapter_by_id":
            
            value = interrupt({
                "tool_name": request.name, 
                "args": request.args,
                "message": "The AI is attempting to save to the database. Approve?" 
            })

            if value == "Action cancelled by user":
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="Action was cancelled by the user."
                    )],
                    isError=False,
                )



        # Execute the tool
        result = await handler(request)
        return result
    
    @staticmethod
    def _initialize_agent(tools: list, prompt: str):
        agent = create_agent(
            model=TaleMachineAgentService._llm, 
            tools=tools, 
            system_prompt=prompt, 
            checkpointer=TaleMachineAgentService._checkpointer,
        )

        return agent
    
    # Separate tool for image generation that returns a direct answer to the user
    # This is a tricky one
    @staticmethod
    def create_generate_image_tool(story_id: int, db_instance):
        @tool(return_direct=True)
        async def generate_image(description: str) -> str:
            """
            Generate an image based on the provided description. A url to the generated image will be returned.
            """
            # 1. Generate and save the image as a file
            credentials = None
            service_account_path = os.getenv("VERTEX_SERVICE_ACCOUNT_LOCATION")
            if service_account_path and os.path.exists(service_account_path):
                print("[DEBUG] Path to service account exists")
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                print("[DEBUG] Loaded credentials from service account file")

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
                                    
                    # Save image to file
                    os.makedirs("generated_images", exist_ok=True)
                    filename = f"generated_images/image_{hash(description) % 10**8}.png"
                    with open(filename, "wb") as f:
                        f.write(img_bytes)
                    #2. Send an interrupt before saving the image in Postgres 
                    # (User can specify if they want to save it to a chapter or just the story)
                    value = interrupt({
                        "tool_name": "generate_image"})        

                    # save image to the database (if the user doesn't want to save it to a chapter, the value passed should be -1)
                    if value == -1:
                        new_image = ImageBase(image_path=filename, story_id=story_id, chapter_id=None)
                    else:
                        new_image = ImageBase(image_path=filename, story_id=story_id, chapter_id=value) 
                    new_image = await db_instance.insert_image(new_image)
                    # img_str = base64.b64encode(img_bytes).decode()
                    # if part.text is not None:
                    #     return f"{part.text}\n\ndata:image/png;base64,{img_str}"
                    # return f"data:image/png;base64,{img_str}"
                    return f"/generated_images/{os.path.basename(filename)}"
                
            return "No image generated"
        return generate_image
    
    @staticmethod
    async def run(messages: list, story_name: str, thread_id: str, story_id: int, db_instance) :
        """Run the agent with a specific thread ID for checkpoint management."""
        try:
            async with streamablehttp_client(TaleMachineAgentService._mcp_server_url) as connection:
                if isinstance(connection, tuple) and len(connection) >= 2:
                    read_stream, write_stream = connection[0], connection[1]
                else:
                    read_stream = connection.read
                    write_stream = connection.write

                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await load_mcp_tools(session, tool_interceptors=[TaleMachineAgentService.ask_approval_interceptor])
                    tools.append(TaleMachineAgentService.create_generate_image_tool(story_id, db_instance))

                    agent = TaleMachineAgentService._initialize_agent(
                        tools=tools,
                        prompt=TaleMachineAgentService._prompt.format(story_name=story_name, story_id=story_id)
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
            print(f"Error in TaleMachineAgentService run: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            raise e

    @staticmethod
    async def resume_after_interrupt(thread_id: str, approved: bool, story_name: str, story_id: int, db_instance, chapter_id: int | None = None) :
        """Resume agent execution after an interrupt with approval/rejection."""
        try:
            async with streamablehttp_client(TaleMachineAgentService._mcp_server_url) as connection:
                if isinstance(connection, tuple) and len(connection) >= 2:
                    read_stream, write_stream = connection[0], connection[1]
                else:
                    read_stream = connection.read
                    write_stream = connection.write

                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await load_mcp_tools(session, tool_interceptors=[TaleMachineAgentService.ask_approval_interceptor])
                    tools.append(TaleMachineAgentService.create_generate_image_tool(story_id, db_instance))

                    agent = TaleMachineAgentService._initialize_agent(
                        tools=tools,
                        prompt=TaleMachineAgentService._prompt.format(story_name=story_name, story_id=story_id)
                    )

                    config = {
                        "configurable": {
                            "thread_id": thread_id
                        }
                    }

                    if approved:
                        if chapter_id is not None:
                            command = Command(resume=chapter_id)
                        # Resume with None to continue execution
                        else:
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
                            print(f"\nResume chunk: {chunk}", file=sys.stderr)
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


def test_interrupt():
    messages = [
        {"role": "user", "content": "Save the following story content: Once upon a time in a land far, far away..."}
    ]
    thread_id = "test_thread_123"
    session_name = "Knights and Dragons"
    async def run_agent():
        async for response in TaleMachineAgentService.run(messages, session_name, thread_id, story_id=14577):
            print(response, end="", flush=True)
        if response.startswith("__interrupt__:"):
            interrupt_msg = response[len("__interrupt__:"):].strip()
            print(f"\nInterrupt received: {interrupt_msg}")
            # Simulate user approval
            user_approval = True  # Change to False to simulate rejection
            async for resume_response in TaleMachineAgentService.resume_after_interrupt(thread_id, user_approval, session_name, story_id=14577):
                print(resume_response, end="", flush=True)
    
    asyncio.run(run_agent())

def test_in_terminal():
    async def setup_story():
        from postgres_service import PostgresService
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from backend.models.postgres.Story import Story
        pg_database_service = PostgresService()

        all_stories = await pg_database_service.get_all_stories()
        if all_stories:
            story = all_stories[0]
            return story.id, "terminal_thread_001", story.title
        else:
            thread_id = "terminal_thread_001"
            story_name = "The Adventures of Terminal"
            story = Story(title=story_name, neo_database_name="terminal_adventures_db")
            story = await pg_database_service.insert_story(story)
            return story.id, thread_id, story_name
    
    story_id, thread_id, story_name = asyncio.run(setup_story())
    async def run_terminal_agent():
        print("Welcome to the TaleMachine Terminal Interface!")
        print("Type 'exit' to quit.")

        messages = []
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() == "exit":
                print("Exiting TaleMachine. Goodbye!")
                break
            messages.append({"role": "user", "content": user_input})
            full_response = ""
            async for response in TaleMachineAgentService.run(messages, story_name, thread_id, story_id):
                full_response += response
                print(response, end="", flush=True)
            if response.startswith("__interrupt__:"):
                interrupt_msg = response[len("__interrupt__:"):].strip()
                print(f"\nInterrupt received: {interrupt_msg}")
                approval = input("Do you want to approve this action? (yes/no): ").strip().lower()
                user_approval = approval == "yes"
                async for resume_response in TaleMachineAgentService.resume_after_interrupt(thread_id, user_approval, story_name, story_id):
                    print(resume_response, end="", flush=True)
                    full_response += resume_response
            messages.append({"role": "assistant", "content": full_response})
    
    asyncio.run(run_terminal_agent())

if __name__ == "__main__":
    test_in_terminal()