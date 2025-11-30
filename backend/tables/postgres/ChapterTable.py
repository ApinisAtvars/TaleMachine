import os
import sys
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.postgres_database import Base


class ChapterTable(Base): # Chapters table
    __tablename__ = 'chapters'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(Text)
    timestamp = Column(Integer)  # Unix timestamp
    story_id = Column(Integer, ForeignKey('stories.id', ondelete="CASCADE"))  # Foreign key to stories table
    story = relationship("StoryTable")