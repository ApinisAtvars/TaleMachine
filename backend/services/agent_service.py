import asyncio
import base64
import os
import sys
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
import json
# import streamlit as st
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain.agents import create_agent
from langchain.messages import AIMessage, ToolMessage
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
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai

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
        - Story Length: {story_length} (short = 1-3 chapters, medium = 4-15 chapters, long = 15+ chapters)
        - Chapter Length: {chapter_length} (short = <500 words, medium = 500-1500 words, long = 1500-4000 words)
        - Genre: {genre}
        - Additional Notes (if any): {additional_notes}
        - Main Characters (if any): {main_characters}
        - Plot Ideas (if any): {plot_ideas}

        You should plan and write the story in chapters, ensuring each chapter aligns with the specified story length and chapter lengths.
        Plan the narrative arc, character development, and plot progression accordingly. If the user wants a longer story, ensure the chapters build towards that goal.
        You will be provided with summaries of previously saved chapters to maintain continuity. If you need more details about past chapters, use your tools to fetch them.
        If no chapters have been saved yet, begin by drafting the first chapter based on the story context provided.

        *** STRICT OPERATIONAL PROTOCOLS ***

        1. DRAFTING PHASE
        - When asked to write content, you must ALWAYS generate the text in the chat window first.
        - You are prohibited from calling the `save_chapter` tool during the initial drafting phase.

        2. REVIEW PHASE
        - Explicitly ask for user approval before saving.
        - Do not assume silence or vague responses imply consent to save.

        3. SAVING PHASE
        - Execute the `save_chapter` tool ONLY when the user gives an explicit command (e.g., "Save it", "Looks good", "Commit").
        - When saving, strip all conversational filler, markdown headers (like '## Chapter 1'), and titles from the `content` field. The `content` field must contain the story body text only.
        - Ensure that the **order of chapters is maintained as per user instructions** using `previous_chapter_id` and `insert_at_start` parameters.

        *** ANTI-HALLUCINATION & TRUTH GUIDELINES ***
        - DATA INTEGRITY: Never invent or hallucinate success messages. If the tool is not called, the chapter is not saved.

        *** GENERAL BEHAVIOR ***
        - Use your tools to fetch story details or generate images when contextually appropriate.
        - Do not mention internal IDs (UUIDs) in your text response unless specifically asked.
        - Maintain the requested narrative tone and style strictly.

        Chapter overview and planning should be done in your mind only and not shared with the user unless explicitly requested.
        Saved chapters and their summary (if available): {chapter_summaries}
        """
    )
    _mcp_server_url = os.getenv("MCP_SERVER_URL")
    _checkpointer = MemorySaver()
    _service_account_path = os.getenv("VERTEX_SERVICE_ACCOUNT_LOCATION")
    if _service_account_path and os.path.exists(_service_account_path):
        # print("[DEBUG] Path to service account exists")
        credentials = service_account.Credentials.from_service_account_file(
            _service_account_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        # print("[DEBUG] Loaded credentials from service account file")
    vertexai.init(project=os.getenv("VERTEX_PROJECT_ID"), location=os.getenv("VERTEX_PROJECT_LOCATION"), credentials=credentials)
    
    _image_generation_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

    # Tool interceptor to ask for user approval before saving a story
    async def ask_approval_interceptor(
        request: MCPToolCallRequest,
        handler,
    ) -> CallToolResult:
        if request.name == "save_chapter" or request.name == "delete_chapter_by_id":
            
            value = interrupt(json.dumps({
                "tool_name": request.name, 
                "args": request.args,
                "message": "The AI is attempting to save to the database. Approve?" 
            }))

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
            # ask the user to link the image to a chapter or just save it to the story
            value = interrupt(json.dumps({"tool_name": "generate_image", "messsage": "Please provide the chapter ID to link the image to. If you don't want to link it to a chapter, please select \"Save to story\""}))    
               
            try:
                images = TaleMachineAgentService._image_generation_model.generate_images(
                    prompt=description,
                    number_of_images=1,
                    aspect_ratio="16:9",
                    safety_filter_level="block_some",
                    person_generation="allow_adult"
                )
            except Exception as e:
                return f"Error generating image: {str(e)}"
            
            try:
                img = images[0]
                os.makedirs("generated_images", exist_ok=True)
                filename = f"generated_images/image_{hash(description) % 10**8}.png"
                img.save(filename)

                # save image to the database (if the user doesn't want to save it to a chapter, the value passed should be -1)
                if value == -1:
                    new_image = ImageBase(image_path=filename, story_id=story_id, chapter_id=None)
                else:
                    new_image = ImageBase(image_path=filename, story_id=story_id, chapter_id=value) 
                new_image = await db_instance.insert_image(new_image)
                return f"Image generated! You can view it in the gallery now."
            except Exception as e:
                return f"Error saving image: {str(e)}"
        
        return generate_image
    
    @staticmethod
    async def run(messages: list, story_name: str, thread_id: str, story_id: int, db_instance,
                  story_length: str | None = None, chapter_length: str | None = None, 
                  genre: str | None = None, additional_notes: str | None = None, 
                  main_characters: str | None = None, plot_ideas: str | None = None):
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

                    chapter_summaries = await db_instance.get_all_summaries_by_story_id(story_id)
                    
                    agent = TaleMachineAgentService._initialize_agent(
                        tools=tools,
                        prompt=TaleMachineAgentService._prompt.format(story_name=story_name, 
                                                                      story_id=story_id,
                                                                      story_length=story_length,
                                                                      chapter_length=chapter_length,
                                                                      genre=genre,
                                                                      additional_notes=additional_notes,
                                                                      main_characters=main_characters,
                                                                      plot_ideas=plot_ideas,
                                                                      chapter_summaries=chapter_summaries)
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
    async def resume_after_interrupt(thread_id: str, approved: bool, story_name: str, story_id: int, 
                                     db_instance,story_length: str | None = None, chapter_length: str | None = None, 
                                     genre: str | None = None, additional_notes: str | None = None, 
                                     main_characters: str | None = None, plot_ideas: str | None = None,
                                     chapter_id: int | None = None) :
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

                    chapter_summaries = await db_instance.get_all_summaries_by_story_id(story_id)

                    agent = TaleMachineAgentService._initialize_agent(
                        tools=tools,
                        prompt=TaleMachineAgentService._prompt.format(story_name=story_name, 
                                                                      story_id=story_id,
                                                                      story_length=story_length,
                                                                      chapter_length=chapter_length,
                                                                      genre=genre,
                                                                      additional_notes=additional_notes,
                                                                      main_characters=main_characters,
                                                                      plot_ideas=plot_ideas,
                                                                      chapter_summaries=chapter_summaries)
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
                            # print(f"\nResume chunk: {chunk}", file=sys.stderr)
                            if isinstance(chunk, tuple):
                                stream_mode, values = chunk
                                if stream_mode == "messages":
                                    if isinstance(values, tuple):
                                        message, metadata = values
                                        if isinstance(message, AIMessage) and message.content:
                                            yield message.content
                                        elif isinstance(message, ToolMessage):
                                            if message.name == "generate_image" and message.content:
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
        from models.postgres.Story import Story
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