from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from models.postgres.ChapterNodeMapping import ChapterNodeMapping, ChapterNodeMappingBase
from tables.postgres.ChapterNodeMappingTable import ChapterNodeMappingTable


class ChapterNodeMappingRepository:
    @staticmethod
    async def insert(db: Session, new_mapping: ChapterNodeMappingBase) -> ChapterNodeMapping:
        try:
            db_object = ChapterNodeMappingTable(**new_mapping.model_dump())
            db.add(db_object)
            db.commit()
            db.refresh(db_object)
            return ChapterNodeMapping.model_validate(db_object)
        except Exception as e:  
            db.rollback()
            raise Exception(f"[ERROR] Error inserting chapter-node mapping: {e}")
    
    @staticmethod
    async def get_by_chapter_id(db: Session, chapter_id: int) -> list[ChapterNodeMapping]:
        db_objects = db.query(ChapterNodeMappingTable).filter(ChapterNodeMappingTable.chapter_id == chapter_id).all()
        return [ChapterNodeMapping.model_validate(obj) for obj in db_objects]
    
    @staticmethod
    async def get_by_node_label_and_name(db: Session, node_label: str, node_name: str) -> list[ChapterNodeMapping] | None:
        db_object = db.query(ChapterNodeMappingTable).filter(
            ChapterNodeMappingTable.node_label == node_label,
            ChapterNodeMappingTable.node_name == node_name
        )
        if db_object:
            return [ChapterNodeMapping.model_validate(obj) for obj in db_object]
        return None
    