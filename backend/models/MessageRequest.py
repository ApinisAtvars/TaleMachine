from pydantic import BaseModel
from typing import List

class MessageRequest(BaseModel):
    """Represents a question request by the user to the agent."""
    messages: List[dict]
    story_name: str
    thread_id: str
    story_id: int
    story_length: str | None = None
    chapter_length: str | None = None
    genre: str | None = None
    additional_notes: str | None = None
    main_characters: str | None = None
    plot_ideas: str | None = None

class ResumeMessageRequest(BaseModel):
    """Represents a resume after interrupt request."""
    thread_id: str
    approval: bool
    story_name: str
    story_id: int
    story_length: str | None = None
    chapter_length: str | None = None
    genre: str | None = None
    additional_notes: str | None = None
    main_characters: str | None = None
    plot_ideas: str | None = None
    chapter_id: int # -1 for None (limitation of interrupt tool)