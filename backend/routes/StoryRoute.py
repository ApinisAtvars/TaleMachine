from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

story_router = APIRouter(prefix="/story", tags=["story"])

class StoryCreate(BaseModel):
    content: str

class StoryUpdate(BaseModel):
    content: str

class Story(BaseModel):
    id: int
    content: str
    timestamp: str

@story_router.get("", response_model=List[Story])
async def get_stories():
    """Get all stories"""
    # TODO: Implement database query
    stories = [
        {"id": 1, "content": "Hello", "timestamp": "2024-01-01T10:00:00"},
        {"id": 2, "content": "World", "timestamp": "2024-01-01T10:01:00"}
    ]
    return stories

@story_router.get("/{story_id}", response_model=Story)
async def get_story(story_id: int):
    """Get a specific story by ID"""
    # TODO: Implement database query
    story = {"id": story_id, "content": "Example story", "timestamp": "2024-01-01T10:00:00"}
    return story

@story_router.post("", response_model=Story, status_code=201)
async def create_story(story: StoryCreate):
    """Create a new story"""
    # TODO: Implement database insert
    new_story = {
        "id": 3,
        "content": story.content,
        "timestamp": "2024-01-01T10:02:00"
    }
    return new_story

@story_router.put("/{story_id}", response_model=Story)
async def update_story(story_id: int, story: StoryUpdate):
    """Update an existing story"""
    # TODO: Implement database update
    updated_story = {
        "id": story_id,
        "content": story.content,
        "timestamp": "2024-01-01T10:03:00"
    }
    return updated_story

@story_router.delete("/{story_id}")
async def delete_story(story_id: int):
    """Delete a story"""
    # TODO: Implement database delete
    return {"message": "Story deleted successfully"}