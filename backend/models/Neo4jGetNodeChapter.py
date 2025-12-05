from pydantic import BaseModel

class Neo4jGetChapterNodeMapping(BaseModel):
    """Represents a mapping of a chapter node from Neo4j."""
    node_label: str  # e.g. "Person", "Location"
    node_name: str  # e.g. "Alice", "Wonderland"