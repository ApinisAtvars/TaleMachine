from sqlalchemy import Column, Integer, String, Text, ForeignKey

from postgres_database import Base

class StoryTable(Base): # Stories table stores story titles because they can maybe be renamed (sessions)
    __tablename__ = 'stories'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)  # Title of the story (session)
    