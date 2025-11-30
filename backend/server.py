from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

load_dotenv("env/.viola.env")

mcp = FastMCP(
    name = "tale-machine-server",
)

transport = os.getenv("TRANSPORT", "streamable-http")
print(f"Starting MCP server with transport: {transport}")

database_connection = "successful_db_connection"  # Placeholder for actual DB connection

# save story tool
@mcp.tool()
async def save_story(user_id: str, session_id: str, story_content: str) -> str:
    """
    Save the story content for a given user and session.
    """
    # Here you would implement the logic to save the story to your database
    # For demonstration, we'll just print and return a success message
    print(f"Test database connection: {database_connection}")
    print(f"Saving story for user {user_id}, session {session_id}: {story_content}")
    return f"Story saved successfully in database {database_connection}."

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