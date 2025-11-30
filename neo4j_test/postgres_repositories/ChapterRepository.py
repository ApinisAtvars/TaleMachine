from sqlalchemy.orm import Session

from postgres_tables.ChapterTable import ChapterTable
from postgres_models.Chapter import Chapter
from postgres_tables.StoryTable import StoryTable

class ChapterRepository:
    @staticmethod
    async def insert(db: Session, new_chapter: Chapter) -> Chapter:
        try:
            stories = db.query(StoryTable).filter(StoryTable.id == new_chapter.story_id).first()
            if not stories:
                raise Exception(f"[ERROR] Story with id {new_chapter.story_id} does not exist.")
            db_object = ChapterTable(**new_chapter.model_dump())
            db.add(db_object)
            db.commit()
            db.refresh(db_object)
            return Chapter.model_validate(db_object)
        except Exception as e:  
            db.rollback()
            raise Exception(f"[ERROR] Error inserting chapter: {e}")
    
    @staticmethod
    async def get_by_id(db: Session, chapter_id: int) -> Chapter | None:
        db_object = db.query(ChapterTable).filter(ChapterTable.id == chapter_id).first()
        if db_object:
            return Chapter.model_validate(db_object)
        return None
    
    @staticmethod
    async def get_all(db: Session) -> list[Chapter]:
        db_objects = db.query(ChapterTable).all()
        return [Chapter.model_validate(obj) for obj in db_objects]
    
    @staticmethod
    async def delete_by_id(db: Session, chapter_id: int) -> bool:
        try:
            db_object = db.query(ChapterTable).filter(ChapterTable.id == chapter_id).first()
            if db_object:
                db.delete(db_object)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            raise Exception(f"[ERROR] Error deleting chapter: {e}")