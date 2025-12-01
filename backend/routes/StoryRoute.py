from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List
from datetime import datetime

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.postgres.Story import Story

story_router = APIRouter(prefix="/story", tags=["story"])

@story_router.post("/insert")
async def insert_story(title:str, neo_database_name:str, request: Request):
    """Insert a new story"""
    try:
        new_story = Story(
            title=title,
            neo_database_name=neo_database_name)
        
        created_story = await request.app.state.db.insert_story(new_story)
        return created_story.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@story_router.get("/find/{story_id}")
async def get_story(story_id: int, request: Request):
    """Get a story by its ID"""
    try:
        story = await request.app.state.db.get_story_by_id(story_id)
        if story:
            return story.model_dump()
        else:
            raise HTTPException(status_code=404, detail="Story not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@story_router.get("/all")
async def get_all_stories(request: Request):
    """Get all stories"""
    try:
        stories = await request.app.state.db.get_all_stories()
        return [story.model_dump() for story in stories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@story_router.post("/update")
async def update_story_title(story_id: int, new_title: str, request: Request):
    """Update a story's title"""
    try:
        updated_story = await request.app.state.db.update_story_title(story_id, new_title)
        if updated_story:
            return updated_story.model_dump()
        else:
            raise HTTPException(status_code=404, detail="Story not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@story_router.delete("/{story_id}")
async def delete_story(story_id: int, request: Request):
    """Delete a story by its ID"""
    try:
        success = await request.app.state.db.delete_story_by_id(story_id)
        if success:
            return {"detail": "Story deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Story not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

