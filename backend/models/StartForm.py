from typing import List, Literal, Set
from pathlib import Path
from pydantic import BaseModel, field_validator, ValidationInfo
import re

# loaded from https://github.com/LDNOOBWV2/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words_V2/blob/main/data/en.txt
def load_banned_words(filepath: str = "banned_words.txt") -> Set[str]:
    try:
        path = Path(filepath)
        if not path.exists():
            return set()
        
        with open(path, "r", encoding="utf-8") as f:
            return {line.strip().lower() for line in f if line.strip()}
            
    except Exception as e:
        print(f"Warning: Could not load banned words: {e}")
        return set()
    
BANNED_TERMS = load_banned_words()

class StartForm(BaseModel):
    title: str
    story_length: Literal["short", "medium", "long"]
    chapter_length: Literal["short", "medium", "long"]
    genre: Literal["sci-fi", "action", "drama", "comedy", "mystery", "thriller", "romance", "young_adult", "fantasy", "children", "memoir", "historical", "poetry"]
    
    # open fields
    additional_notes: str | None = None
    main_characters: str | None = None
    plot_ideas: str | None = None

    @field_validator('additional_notes', 'main_characters', 'plot_ideas')
    @classmethod
    def no_explicit_content(cls, v: str | None, info: ValidationInfo):
        if v is None:
            return v
        
        def check_text(text: str, field_name: str):
            text_lower = text.lower()
            for term in BANNED_TERMS:
                # \b matches word boundaries (spaces, punctuation, start/end of line)
                if re.search(rf"\b{re.escape(term)}\b", text_lower):
                    raise ValueError(f"The field '{field_name}' contains inappropriate content: '{term}'")

        if isinstance(v, str):
            check_text(v, info.field_name)
        elif isinstance(v, list):
            for item in v:
                check_text(item, info.field_name)
        
        return v