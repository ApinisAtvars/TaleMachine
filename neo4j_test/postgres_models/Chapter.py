from pydantic import BaseModel, ConfigDict, Field

from neo4j_test.postgres_models.Story import Story

class ChapterBase(BaseModel):
    id: int
    content: str
    story_id: int
    timestamp: int

class Chapter(ChapterBase):
    model_config = ConfigDict(from_attributes=True)
    story: Story