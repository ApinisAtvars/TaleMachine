from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from tables.postgres.StoryTable import StoryTable
from models.postgres.Story import Story

class StoryRepository:
    @staticmethod
    async def insert(db: Session, new_story: Story) -> Story:
        try:
            db_object = StoryTable(**new_story.model_dump())
            db.add(db_object)
            db.commit()
            db.refresh(db_object)
            return Story.model_validate(db_object)
        except Exception as e:  
            db.rollback()
            raise Exception(f"[ERROR] Error inserting story: {e}")
    
    @staticmethod
    async def get_by_id(db: Session, story_id: int) -> Story | None:
        db_object = db.query(StoryTable).filter(StoryTable.id == story_id).first()
        if db_object:
            return Story.model_validate(db_object)
        return None
    
    @staticmethod
    async def get_all(db: Session) -> list[Story]:
        db_objects = db.query(StoryTable).all()
        return [Story.model_validate(obj) for obj in db_objects]
    
    @staticmethod
    async def delete_by_id(db: Session, story_id: int) -> bool:
        try:
            db_object = db.query(StoryTable).filter(StoryTable.id == story_id).first()
            if db_object:
                db.delete(db_object)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            raise Exception(f"[ERROR] Error deleting story: {e}")
        
    @staticmethod
    async def update_story(db: Session, story_id: int, new_title: str| None = None,
                           new_story_length: str| None = None, new_chapter_length: str| None = None, 
                           new_genre: str| None = None, new_additional_notes: str| None = None, 
                           new_main_characters: str| None = None, 
                           new_plot_ideas: str| None = None) -> Story | None:
        try:
            db_object = db.query(StoryTable).filter(StoryTable.id == story_id).first()
            if db_object:
                if new_title is not None:
                    db_object.title = new_title # type: ignore
                if new_story_length is not None:
                    db_object.story_length = new_story_length # type: ignore
                if new_chapter_length is not None:
                    db_object.chapter_length = new_chapter_length # type: ignore
                if new_genre is not None:
                    db_object.genre = new_genre # type: ignore
                if new_additional_notes is not None:
                    db_object.additional_notes = new_additional_notes # type: ignore
                if new_main_characters is not None:
                    db_object.main_characters = new_main_characters # type: ignore
                if new_plot_ideas is not None:
                    db_object.plot_ideas = new_plot_ideas # type: ignore
                
                db.commit()
                db.refresh(db_object)
                return Story.model_validate(db_object)
        except Exception as e:
            db.rollback()
            raise Exception(f"[ERROR] Error updating story title: {e}")
    