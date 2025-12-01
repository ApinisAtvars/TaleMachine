from fastapi import APIRouter, HTTPException, Request

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

chapter_router = APIRouter(prefix="/chapter", tags=["chapter"])

@chapter_router.get("/all/{story_id}")
async def get_all_chapters_by_story_id(story_id: int, request: Request):
    """Get all chapters for a given story ID"""
    try:
        chapters = await request.app.state.db.get_all_chapters_by_story_id(story_id)
        return [chapter.model_dump() for chapter in chapters]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))