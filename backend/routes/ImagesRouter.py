from fastapi import APIRouter, HTTPException, Request

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

images_router = APIRouter(prefix="/images", tags=["images"])

@images_router.get("/all/{story_id}")
async def get_all_images_by_story_id(story_id: int, request: Request):
    """Get all images for a given story ID"""
    try:
        images = await request.app.state.db.get_images_by_story_id(story_id)
        return [image.model_dump() for image in images]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))