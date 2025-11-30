from postgres_database import get_db
from postgres_repositories.StoryRepository import StoryRepository
from postgres_repositories.ChapterRepository import ChapterRepository
from postgres_repositories.ChapterNodeMappingRepository import ChapterNodeMappingRepository


from sqlalchemy.orm import Session


class PostgresService:
    def __init__(self):
        self.db_session = get_db()
    
    #region story repository

    async def insert_story(self, new_story):
        assert isinstance(self.db_session, Session)
        return await StoryRepository.insert(self.db_session, new_story)

    async def get_story_by_id(self, story_id: int):
        assert isinstance(self.db_session, Session)
        return await StoryRepository.get_by_id(self.db_session, story_id)
    
    async def get_all_stories(self):
        assert isinstance(self.db_session, Session)
        return await StoryRepository.get_all(self.db_session)
    
    async def delete_story_by_id(self, story_id: int):
        assert isinstance(self.db_session, Session)
        return await StoryRepository.delete_by_id(self.db_session, story_id)
    
    async def update_story_title(self, story_id: int, new_title: str):
        assert isinstance(self.db_session, Session)
        return await StoryRepository.update_title(self.db_session, story_id, new_title)
    
    #endregion

    #region chapter repository

    async def insert_chapter(self, new_chapter):
        assert isinstance(self.db_session, Session)
        return await ChapterRepository.insert(self.db_session, new_chapter)
    
    async def get_chapter_by_id(self, chapter_id: int):
        assert isinstance(self.db_session, Session)
        return await ChapterRepository.get_by_id(self.db_session, chapter_id)
    
    async def get_all_chapters(self):
        assert isinstance(self.db_session, Session)
        return await ChapterRepository.get_all(self.db_session)
    
    async def delete_chapter_by_id(self, chapter_id: int):
        assert isinstance(self.db_session, Session)
        return await ChapterRepository.delete_by_id(self.db_session, chapter_id)
    
    #endregion

    #region Chapter-Node Mapping repository

    async def insert_chapter_node_mapping(self, new_mapping):
        assert isinstance(self.db_session, Session)
        return await ChapterNodeMappingRepository.insert(self.db_session, new_mapping)
    
    async def get_mappings_by_chapter_id(self, chapter_id: int):
        assert isinstance(self.db_session, Session)
        return await ChapterNodeMappingRepository.get_by_chapter_id(self.db_session, chapter_id)
    
    async def get_mapping_by_node_label_and_name(self, node_label: str, node_name: str):
        assert isinstance(self.db_session, Session)
        return await ChapterNodeMappingRepository.get_by_node_label_and_name(self.db_session, node_label, node_name)
    
    #endregion