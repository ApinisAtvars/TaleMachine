from sqlalchemy import Column, Index, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from postgres_database import Base

class ChapterNodeMappingTable(Base):
    __tablename__ = 'chapter_node_mappings'
    chapter_id = Column(Integer, ForeignKey('chapters.id', ondelete="CASCADE"), primary_key=True)  # Foreign key to chapters table
    node_label = Column(String, index=True, primary_key=True)  # ID of the corresponding Neo4j story node
    node_name = Column(String, index=True, primary_key=True)  # Name of the corresponding Neo4j story node
    
    chapter = relationship("ChapterTable")

    __table_args__ = (
        # Because practically all queries on this table will be looking up by both label and name
        Index('idx_node_lookup', 'node_label', 'node_name'),
    )