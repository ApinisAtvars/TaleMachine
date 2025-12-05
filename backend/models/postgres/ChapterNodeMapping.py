# Maps the NNode label and node name from the Neo4j graph to the Message SQLAlchemy model
import os
import sys
from pydantic import BaseModel, ConfigDict, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from models.postgres.Chapter import Chapter

class ChapterNodeMappingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    node_label: str # e.g. "Person", "Location"
    node_name: str # e.g. "Alice", "Wonderland"
    chapter_id: int

class ChapterNodeMapping(ChapterNodeMappingBase):
    model_config = ConfigDict(from_attributes=True)
    chapter: Chapter

