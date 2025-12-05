from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import datetime

from models.postgres.Chapter import ChapterBase
from services.postgres_service import PostgresService

load_dotenv()

mcp = FastMCP(
    name = "tale-machine-server",
)

transport = os.getenv("TRANSPORT", "streamable-http")
print(f"Starting MCP server with transport: {transport}")

#region Postgres Database Tools
pg_database_service = PostgresService()

@mcp.tool()
async def save_chapter(
    content: str, 
    story_id: int, 
    title: str, 
    previous_chapter_id: int | None = None,
    insert_at_start: bool = False
) -> dict: # TODO: Make it not write the chapter name in the content
    """
    Saves a new chapter to the database.

    IMPORTANT - WHAT TO PASS AS CONTENT:
    - You should save the content of one chapter only - one of your messages, NOT the entire chat history.
    - If it is unclear what the user wants to be saved, just ask them to clarify.

    IMPORTANT - HOW TO ORDER CHAPTERS:
    1. To add a chapter at the END of the story:
       - Set `previous_chapter_id` = None
       - Set `insert_at_start` = False
    
    2. To insert a chapter at the VERY START (Preface/Prologue/Chapter 1 of existing story):
       - Set `previous_chapter_id` = None
       - Set `insert_at_start` = True  <-- CRITICAL for "First Chapter" requests
    
    3. To insert a chapter BETWEEN existing chapters (e.g. between Ch 1 and Ch 2):
       - Set `previous_chapter_id` = [ID of Chapter 1]
       - Set `insert_at_start` = False

    Args:
        content: The text content.
        story_id: The ID of the story.
        title: The chapter title.
        previous_chapter_id: The ID of the chapter immediately preceding this one (for squeezing in middle).
        insert_at_start: Set True ONLY if inserting before all other chapters.
    """
    try:
        # Calls your PostgresService logic
        created_chapter = await pg_database_service.insert_chapter_with_ordering(
            content=content,
            title=title,
            story_id=story_id,
            insert_after_chapter_id=previous_chapter_id,
            insert_at_start=insert_at_start
        )
        return created_chapter.model_dump()
    except Exception as e:
        return {"error": str(e)}

# query database tool
@mcp.tool()
async def get_chapter_by_id(chapter_id: int) -> dict | None:
    """
    Get chapter by its ID.
    """
    chapter = await pg_database_service.get_chapter_by_id(chapter_id)
    if chapter:
        return chapter.model_dump()
    return None

@mcp.tool()
async def get_chapter_by_chapter_title(story_id: int, title: str) -> dict | None:
    """
    Get chapter by its title within a story.
    This is case-sensitive, and must match exactly.
    This tool can be used to get a chapter id for further operations.
    """
    chapter = await pg_database_service.get_chapter_by_title(story_id, title)
    if chapter:
        return chapter.model_dump()
    return None

@mcp.tool()
async def get_all_chapters_by_story_id(story_id: int) -> list[dict]:
    """
    Get all chapters for a given story ID.
    """
    chapters = await pg_database_service.get_all_chapters_by_story_id(story_id)
    return [chapter.model_dump() for chapter in chapters]

@mcp.tool()
async def delete_chapter_by_id(chapter_id: int) -> bool:
    """
    Delete chapter by its ID.
    """
    return await pg_database_service.delete_chapter_by_id(chapter_id)
#endregion

#region Neo4j Database Tools
# Removed after conversation with Dieter. Semantic search should be a separate operation outside of the story-writing agent.
# @mcp.tool()
# async def semantic_search(story_id: int, user_query: str) -> str:
#     """
#     Query the database using natural language. Provide the story ID, and the question. You will receive the answer as a string.
#     """
#     # 1. Change the Neo4j database to the correct one.
#     story = await pg_database_service.get_story_by_id(story_id)
#     if not story:
#         raise Exception(f"[ERROR] Story with id {story_id} does not exist.")
#     await pg_database_service.neo4j_service.connect_to_existing_database(story.neo_database_name)
#     # 2. Query the database with natural language
#     answer = await pg_database_service.neo4j_service.query_with_natural_language(user_query)
#     return answer
#endregion
if __name__ == "__main__":
    print(f"Starting MCP server with transport: {transport}")
    try:
        if transport == "stdio":
            print("Running server with stdio transport")
            mcp.run(transport="stdio")
        elif transport == "streamable-http":
            print("Running server with Streamable HTTP transport")
            mcp.run(transport="streamable-http")
        else:
            raise ValueError(f"Unknown transport: {transport}")
    finally:
        pg_database_service.close()