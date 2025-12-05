import os
import sys
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from postgres_database import Base

class ImageTable(Base): # Stores the image path + the story that this image is from
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True) # One to many relationship with Story
    image_path = Column(String)  # Path to the image file
    story_id = Column(Integer, ForeignKey('stories.id', ondelete="CASCADE"), nullable=False)  # Foreign key to stories table
    chapter_id = Column(Integer, ForeignKey('chapters.id', ondelete="CASCADE"), nullable=True)  # Nullable foreign key to chapters table
    story = relationship("StoryTable")
    chapter = relationship("ChapterTable")