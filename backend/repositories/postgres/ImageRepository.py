from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from models.postgres.Image import ImageBase
from tables.postgres.ImageTable import ImageTable

class ImageRepository:
    @staticmethod
    async def insert(db: Session, new_image: ImageBase) -> ImageBase:
        try:
            db_object = ImageTable(**new_image.model_dump())
            db.add(db_object)
            db.commit()
            db.refresh(db_object)
            return ImageBase.model_validate(db_object)
        except Exception as e:  
            db.rollback()
            raise Exception(f"[ERROR] Error inserting image: {e}")
    
    @staticmethod
    async def get_by_story_id(db: Session, story_id: int) -> list[ImageBase]:
        db_objects = db.query(ImageTable).filter(ImageTable.story_id == story_id).all()
        return [ImageBase.model_validate(obj) for obj in db_objects]
    
    @staticmethod
    async def delete_by_id(db: Session, image_id: int) -> bool:
        try:
            db_object = db.query(ImageTable).filter(ImageTable.id == image_id).first()
            if not db_object:
                return False
            db.delete(db_object)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"[ERROR] Error deleting image: {e}")
    