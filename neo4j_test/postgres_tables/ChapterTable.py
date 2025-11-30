from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from postgres_database import Base


class ChapterTable(Base): # Chapters table
    __tablename__ = 'chapters'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(Text)
    role = Column(String)  # 'user' or 'ai'
    timestamp = Column(Integer)  # Unix timestamp
    story_id = Column(Integer, ForeignKey('stories.id', ondelete="CASCADE"))  # Foreign key to stories table
    story = relationship("StoryTable")