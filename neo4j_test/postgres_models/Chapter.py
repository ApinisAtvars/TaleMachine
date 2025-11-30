from pydantic import BaseModel, ConfigDict, Field

from postgres_models.Story import Story

class ChapterBase(BaseModel):
    id: int | None = None
    content: str
    story_id: int
    timestamp: int

class Chapter(ChapterBase):
    model_config = ConfigDict(from_attributes=True)
    story: Story