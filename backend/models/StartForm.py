from typing import List, Literal, Set
from pathlib import Path
from pydantic import BaseModel, field_validator, ValidationInfo
import re


class StartForm(BaseModel):
    title: str
    story_length: Literal["short", "medium", "long"]
    chapter_length: Literal["short", "medium", "long"]
    genre: Literal["sci-fi", "action", "drama", "comedy", "mystery", "thriller", "romance", "young_adult", "fantasy", "children", "memoir", "historical", "poetry"]
    
    # open fields
    additional_notes: str | None = None
    main_characters: str | None = None
    plot_ideas: str | None = None