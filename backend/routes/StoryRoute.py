from fastapi import APIRouter, HTTPException, Request

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.postgres.Story import Story
from models.StartForm import StartForm

story_router = APIRouter(prefix="/story", tags=["story"])

# @story_router.post("/insert")
# async def insert_story(title:str, neo_database_name:str, request: Request):
#     """Insert a new story"""
#     try:
#         new_story = Story(
#             title=title,
#             neo_database_name=neo_database_name)
        
#         created_story = await request.app.state.db.insert_story(new_story)
#         return created_story.model_dump()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@story_router.post("/start_form")
async def insert(form: StartForm, request: Request):
    """Upload start form instructions to initialize the agent's behavior."""
    try:
        new_story = Story(
            title=form.title,
            neo_database_name=form.title,
            story_length=form.story_length,
            chapter_length=form.chapter_length,
            genre=form.genre,
            additional_notes=form.additional_notes,
            main_characters=form.main_characters,
            plot_ideas=form.plot_ideas
        )
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
async def update_story(story_id: int, request: Request, new_title: str| None = None, 
                       new_story_length: str| None = None, new_chapter_length: str| None = None, 
                       new_genre: str| None = None, new_additional_notes: str| None = None, 
                       new_main_characters: str| None = None, 
                       new_plot_ideas: str| None = None):
    """Update a story's title"""
    try:
        updated_story = await request.app.state.db.update_story(story_id, new_title, 
                                                                new_story_length, new_chapter_length, 
                                                                new_genre, new_additional_notes, 
                                                                new_main_characters, new_plot_ideas)
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
    
@story_router.post("/rename/{story_id}")
async def rename_story(story_id: int, new_title: str, request: Request):
    """Rename a story by its ID"""
    try:
        renamed_story = await request.app.state.db.update_story_title(story_id, new_title)
        if renamed_story:
            return renamed_story.model_dump()
        else:
            raise HTTPException(status_code=404, detail="Story not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

