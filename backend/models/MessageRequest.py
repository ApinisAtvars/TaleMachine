from pydantic import BaseModel
from typing import List

class MessageRequest(BaseModel):
    """Represents a question request by the user to the agent."""
    messages: List[dict]
    story_name: str
    thread_id: str
    story_id: int

class ResumeMessageRequest(BaseModel):
    """Represents a resume after interrupt request."""
    thread_id: str
    approval: bool
    story_name: str
    story_id: int
    chapter_id: int # -1 for None (limitation of interrupt tool)