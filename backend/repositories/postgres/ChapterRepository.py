from sqlalchemy.orm import Session
from sqlalchemy import func
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from tables.postgres.ChapterTable import ChapterTable
from models.postgres.Chapter import Chapter, ChapterBase
from tables.postgres.StoryTable import StoryTable



class ChapterRepository:
    @staticmethod
    async def insert(db: Session, new_chapter: ChapterBase) -> Chapter:
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
    async def get_all_by_story_id(db: Session, story_id: int) -> list[Chapter]:
        # SELECT * FROM chapters WHERE story_id = :story_id ORDER BY sort_order ASC
        db_objects = db.query(ChapterTable).filter(ChapterTable.story_id == story_id).order_by(ChapterTable.sort_order.asc()).all()
        return [Chapter.model_validate(obj) for obj in db_objects]
    
    @staticmethod
    async def get_chapter_by_title(db: Session, story_id: int, title: str) -> Chapter | None:
        db_object = db.query(ChapterTable)\
                        .filter(ChapterTable.story_id == story_id)\
                        .filter(ChapterTable.title == title)\
                        .first()
        if db_object:
            return Chapter.model_validate(db_object)
        return None
    
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
    
    @staticmethod
    async def get_max_sort_order(db: Session, story_id: int) -> float:
        """Finds the highest sort_order currently in the story."""
        result = db.query(func.max(ChapterTable.sort_order))\
                   .filter(ChapterTable.story_id == story_id)\
                   .scalar()
        return result if result is not None else 0.0
    
    @staticmethod
    async def get_min_sort_order(db: Session, story_id: int) -> float | None:
        """Finds the lowest sort_order currently in the story."""
        result = db.query(func.min(ChapterTable.sort_order))\
                   .filter(ChapterTable.story_id == story_id)\
                   .scalar()
        return result

    @staticmethod
    async def get_next_chapter_by_sort_order(db: Session, story_id: int, current_sort_order: float) -> Chapter | None:
        """Finds the chapter that comes immediately AFTER a specific sort_order."""
        db_object = db.query(ChapterTable)\
                      .filter(ChapterTable.story_id == story_id)\
                      .filter(ChapterTable.sort_order > current_sort_order)\
                      .order_by(ChapterTable.sort_order.asc())\
                      .first()
        if db_object:
            return Chapter.model_validate(db_object)
        return None