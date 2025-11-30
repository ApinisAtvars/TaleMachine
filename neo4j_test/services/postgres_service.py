import sys
import os

# Add the parent directory to sys.path to allow imports from the root of the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from postgres_database import SessionLocal, start_db
from postgres_repositories.StoryRepository import StoryRepository
from postgres_repositories.ChapterRepository import ChapterRepository
from postgres_repositories.ChapterNodeMappingRepository import ChapterNodeMappingRepository


from sqlalchemy.orm import Session


class PostgresService:
    def __init__(self):
        self.db_session = SessionLocal()
    
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
    
    async def get_all_chapters_by_story_id(self, story_id: int):
        assert isinstance(self.db_session, Session)
        return await ChapterRepository.get_all_by_story_id(self.db_session, story_id)
    
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

if __name__ == "__main__":
    start_db()
    service = PostgresService()

    import asyncio
    from postgres_models.Story import Story
    from postgres_models.Chapter import ChapterBase
    from postgres_models.ChapterNodeMapping import ChapterNodeMappingBase

    async def run_tests():
        print("--- Starting Tests ---")

        # 1. Story Tests
        print("\n[Story Tests]")
        # Insert
        new_story = Story(title="Test Story")
        created_story = await service.insert_story(new_story)
        print(f"Inserted Story: {created_story}")
        assert created_story.id is not None
        story_id = created_story.id

        # Get by ID
        fetched_story = await service.get_story_by_id(story_id)
        print(f"Get Story by ID ({story_id}): {fetched_story}")

        # Get All
        all_stories = await service.get_all_stories()
        print(f"All Stories: {len(all_stories)} found")

        # Update Title
        updated_story = await service.update_story_title(story_id, "Updated Test Story Title")
        print(f"Updated Story: {updated_story}")

        # 2. Chapter Tests
        print("\n[Chapter Tests]")
        # Insert
        new_chapter = ChapterBase(content="Chapter Content", story_id=story_id, timestamp=1234567890)
        created_chapter = await service.insert_chapter(new_chapter)
        print(f"Inserted Chapter: {created_chapter}")
        assert created_chapter.id is not None
        chapter_id = created_chapter.id

        # Get by ID
        fetched_chapter = await service.get_chapter_by_id(chapter_id)
        print(f"Get Chapter by ID ({chapter_id}): {fetched_chapter}")

        # Get All
        all_chapters = await service.get_all_chapters()
        print(f"All Chapters: {len(all_chapters)} found")

        # Get by Story ID
        story_chapters = await service.get_all_chapters_by_story_id(story_id)
        print(f"Chapters for Story {story_id}: {len(story_chapters)} found")

        # 3. Mapping Tests
        print("\n[Mapping Tests]")
        # Insert
        new_mapping = ChapterNodeMappingBase(node_label="Person", node_name="Alice", chapter_id=chapter_id)
        created_mapping = await service.insert_chapter_node_mapping(new_mapping)
        print(f"Inserted Mapping: {created_mapping}")

        # Get by Chapter ID
        chapter_mappings = await service.get_mappings_by_chapter_id(chapter_id)
        print(f"Mappings for Chapter {chapter_id}: {chapter_mappings}")

        # Get by Label and Name
        specific_mapping = await service.get_mapping_by_node_label_and_name("Person", "Alice")
        print(f"Mapping (Person, Alice): {specific_mapping}")

        # 4. Cleanup (Delete Tests)
        print("\n[Cleanup / Delete Tests]")
        # Delete Chapter
        deleted_chapter = await service.delete_chapter_by_id(chapter_id)
        print(f"Deleted Chapter {chapter_id}: {deleted_chapter}")
        
        # Verify Chapter Deletion
        check_chapter = await service.get_chapter_by_id(chapter_id)
        print(f"Check Chapter {chapter_id} (should be None): {check_chapter}")

        # Delete Story
        deleted_story = await service.delete_story_by_id(story_id)
        print(f"Deleted Story {story_id}: {deleted_story}")

        # Verify Story Deletion
        check_story = await service.get_story_by_id(story_id)
        print(f"Check Story {story_id} (should be None): {check_story}")

        print("\n--- Tests Completed ---")

    asyncio.run(run_tests())
