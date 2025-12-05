import os
import sys
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Double
from sqlalchemy.orm import relationship

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from postgres_database import Base


class ChapterTable(Base): # Chapters table
    __tablename__ = 'chapters'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)  # Title of the chapter, NOT the story
    content = Column(Text, nullable=False)
    timestamp = Column(Integer, nullable=False)  # Unix timestamp
    sort_order = Column(Double, nullable=False)
    story_id = Column(Integer, ForeignKey('stories.id', ondelete="CASCADE"), nullable=False)  # Foreign key to stories table
    story = relationship("StoryTable")