import os
import sys
from sqlalchemy import Column, Integer, String, Text, ForeignKey

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from postgres_database import Base

class StoryTable(Base): # Stories table stores story titles because they can maybe be renamed (sessions)
    __tablename__ = 'stories'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)  # Title of the story (session)
    neo_database_name = Column(String)  # Name of the Neo4j database where this story's nodes are stored
    story_length = Column(String, default='short')  # 'short', 'medium', 'long'
    chapter_length = Column(String, default='short')  # 'short', 'medium', 'long'
    genre = Column(String, default='comedy')  # Genre of the story
    additional_notes = Column(Text, nullable=True)  # Additional notes for the story
    main_characters = Column(Text, nullable=True)  # Comma-separated list of main characters
    plot_ideas = Column(Text, nullable=True)  # Comma-separated list of plot ideas