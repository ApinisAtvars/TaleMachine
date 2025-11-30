from sqlalchemy.orm import Session

from postgres_tables.StoryTable import StoryTable
from postgres_models.Story import Story

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
    async def update_title(db: Session, story_id: int, new_title: str) -> Story | None:
        try:
            db_object = db.query(StoryTable).filter(StoryTable.id == story_id).first()
            if db_object:
                db_object.title = new_title # type: ignore
                
                db.commit()
                db.refresh(db_object)
                return Story.model_validate(db_object)
        except Exception as e:
            db.rollback()
            raise Exception(f"[ERROR] Error updating story title: {e}")