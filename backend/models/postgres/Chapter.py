from pydantic import BaseModel, ConfigDict, Field
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from backend.models.postgres.Story import Story

class ChapterBase(BaseModel):
    id: int | None = None
    content: str
    story_id: int
    timestamp: int

class Chapter(ChapterBase):
    model_config = ConfigDict(from_attributes=True)
    story: Story