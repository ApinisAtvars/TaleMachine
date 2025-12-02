from pydantic import BaseModel
from fastapi import Form, UploadFile, File
from typing import List, Union
import json

class Message(BaseModel):
    role: str
    content: str
    
class MessageRequest(BaseModel):
    """Represents a question request by the user to the agent."""
    messages: List[Message]
    story_name: str
    thread_id: str
    story_id: int

class ResumeMessageRequest(BaseModel):
    """Represents a resume after interrupt request."""
    thread_id: str
    approval: bool
    story_name: str
    story_id: int