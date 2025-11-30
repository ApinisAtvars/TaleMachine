# Maps the NNode label and node name from the Neo4j graph to the Message SQLAlchemy model
from pydantic import BaseModel, ConfigDict, Field

from neo4j_test.postgres_models.Chapter import Chapter

class ChapterNodeMappingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    node_label: str # e.g. "Person", "Location"
    node_name: str # e.g. "Alice", "Wonderland"
    chapter_id: int

class ChapterNodeMapping(ChapterNodeMappingBase):
    model_config = ConfigDict(from_attributes=True)
    chapter: Chapter

