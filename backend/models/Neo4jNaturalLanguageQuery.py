from pydantic import BaseModel


class MessageRequest(BaseModel):
    """Represents a natural language query request to the Neo4j database."""
    query: str