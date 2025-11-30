from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

from models.postgres.Chapter import ChapterBase
from services.postgres_service import PostgresService

load_dotenv("env/.viola.env")

mcp = FastMCP(
    name = "tale-machine-server",
)

transport = os.getenv("TRANSPORT", "streamable-http")
print(f"Starting MCP server with transport: {transport}")

#region Postgres Database Tools
pg_database_service = PostgresService()

@mcp.tool()
async def save_story(story_content: str) -> dict:
    """
    Save chapter content. 
    Only add the chapter text, without any metadata as the argument.
    """
    # new_chapter = ChapterBase(content="Chapter Content", story_id=story_id, timestamp=1234567890)
    # created_chapter = await pg_database_service.insert_chapter(new_chapter)
    # return new_chapter.model_dump()
    pass

# query database tool
@mcp.tool()
async def query_database(user_id: str, query: str) -> str:
    """
    Query the database for information related to the user's stories.
    """
    # Here you would implement the logic to query your database
    # For demonstration, we'll just print and return a mock response
    print(f"Querying database for user {user_id} with query: {query}")
    return f"Mock response for query '{query}' for user {user_id}."
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