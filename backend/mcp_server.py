from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import datetime

from models.postgres.Chapter import ChapterBase
from services.postgres_service import PostgresService
from models.postgres.ChapterNodeMapping import ChapterNodeMapping

load_dotenv("env/.viola.env")

mcp = FastMCP(
    name = "tale-machine-server",
)

transport = os.getenv("TRANSPORT", "streamable-http")
print(f"Starting MCP server with transport: {transport}")

#region Postgres Database Tools
pg_database_service = PostgresService()

@mcp.tool()
async def save_story(story_content: str, story_id: int) -> dict:
    """
    Save chapter content. 
    Only add the chapter text, without any metadata as the argument.
    Only save the story when user asks to save.
    """
    timestamp = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
    new_chapter = ChapterBase(content=story_content, story_id=story_id, timestamp=timestamp)
    created_chapter = await pg_database_service.insert_chapter(new_chapter)
    return created_chapter.model_dump()

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

if __name__ == "__main__":
    print(f"Starting MCP server with transport: {transport}")
    if transport == "stdio":
        print("Running server with stdio transport")
        mcp.run(transport="stdio")
    elif transport == "streamable-http":
        print("Running server with Streamable HTTP transport")
        mcp.run(transport="streamable-http")
    else:
        raise ValueError(f"Unknown transport: {transport}")