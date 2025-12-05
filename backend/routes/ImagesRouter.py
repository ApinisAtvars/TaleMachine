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
    
@images_router.delete("/delete/{image_id}")
async def delete_image_by_id(image_id: int, request: Request):
    """Delete image by its ID"""
    try:
        success = await request.app.state.db.delete_image_by_id(image_id)
        if not success:
            raise HTTPException(status_code=404, detail="Image not found")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))