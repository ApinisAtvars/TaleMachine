from pydantic import BaseModel, ConfigDict, Field
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from models.postgres.Story import Story

class ChapterBase(BaseModel):
    id: int | None = None
    title: str # Title of the chapter, NOT the story
    content: str
    story_id: int
    sort_order: float
    summary: str | None = None
    timestamp: int

class Chapter(ChapterBase):
    model_config = ConfigDict(from_attributes=True)
    story: Story



class ChapterCreate(BaseModel):
    '''
    When we create a new chapter, it doesn't NEED to be between two existing chapters.\n
    If insert_after_chapter_id is None, we just append it to the end.\n
    Otherwise, we insert it after the given chapter ID. 
    '''
    title: str
    content: str
    story_id: int
    timestamp: int
    insert_after_chapter_id: int | None = None

  