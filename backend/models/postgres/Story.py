from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class Story(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None
    title: str # The Title of the story
    neo_database_name: str # The name of the Neo4j database where this story's nodes are stored, story can be renamed, that's why it's here
    # Single user application, so no user_id field needed
    story_length: Literal['short', 'medium', 'long'] = 'short' 
    chapter_length: Literal['short', 'medium', 'long'] = 'short'
    genre: Literal["sci-fi", "action", "drama", "comedy", "mystery", "thriller", "romance", 
                   "young_adult", "fantasy", "children", "memoir", 
                   "historical", "poetry"] = 'comedy'
    additional_notes: str | None = None
    main_characters: str | None = None
    plot_ideas: str | None = None
    

