import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.postgres_database import SessionLocal, start_db
from backend.repositories.postgres.StoryRepository import StoryRepository
from backend.repositories.postgres.ChapterRepository import ChapterRepository
from backend.repositories.postgres.ChapterNodeMappingRepository import ChapterNodeMappingRepository
from backend.repositories.postgres.ImageRepository import ImageRepository
from backend.services.neo4j_service import Neo4jService
from backend.models.postgres.Chapter import ChapterBase, ChapterCreate
from backend.models.postgres.ChapterNodeMapping import ChapterNodeMappingBase

from sqlalchemy.orm import Session
from langchain_neo4j import Neo4jGraph


class PostgresService:
    def __init__(self):
        start_db()
        self.db_session = SessionLocal()
        self.db_graph = Neo4jGraph(
            url="bolt://localhost:7687",
            username="neo4j",
            password="qwertyui",
            enhanced_schema=True
        )
        self.neo4j_service = Neo4jService(self.db_graph)
    
    #region story repository

    async def insert_story(self, new_story):
        assert isinstance(self.db_session, Session)
        #0. Check if there already exists a Neo4j database with the same name
        # The story that this database belongs to can already be renamed to something different
        sanitized_db_name = self.neo4j_service._sanitize_db_name(new_story.neo_database_name)
        if await self.neo4j_service.check_database_exists(sanitized_db_name):
            raise Exception(f"[ERROR] A Neo4j database with the name {new_story.neo_database_name} already exists.")
        #1. Create a new Neo4j database for the story
        neo_database_name = await self.neo4j_service.create_new_database(new_story.title) # Database name is the initial title of the story
        #2. Set the story's neo_database_name to the new database name
        new_story.neo_database_name = neo_database_name # The database name is the sanitized final name
        #3. Insert the story in postgres, and return the created story
        return await StoryRepository.insert(self.db_session, new_story)

    async def get_story_by_id(self, story_id: int):
        """Get a story by its ID + Connect to its Neo4j database (if the story exists)"""
        assert isinstance(self.db_session, Session)
        story = await StoryRepository.get_by_id(self.db_session, story_id)
        if story:
            await self.neo4j_service.connect_to_existing_database(story.neo_database_name)
            print(f"[DEBUG] Connected to Neo4j database: {story.neo_database_name}")
        return story
    
    async def get_all_stories(self):
        assert isinstance(self.db_session, Session)
        return await StoryRepository.get_all(self.db_session)
    
    async def delete_story_by_id(self, story_id: int):
        assert isinstance(self.db_session, Session)
        story = await self.get_story_by_id(story_id)
        #1. Delete the story's Neo4j database
        await self.neo4j_service.delete_database(story.neo_database_name)
        #2. Delete the story from Postgres
        return await StoryRepository.delete_by_id(self.db_session, story_id)
    
    async def update_story_title(self, story_id: int, new_title: str):
        assert isinstance(self.db_session, Session)
        return await StoryRepository.update_title(self.db_session, story_id, new_title)
    
    #endregion

    #region chapter repository

    async def insert_chapter(self, new_chapter: ChapterBase):
        """
        When inserting a chapter, we also extract the nodes and relationships from it,
        and add those to the story's neo4j database.\n
        On top of that, we also create the chapter-node mappings in Postgres.
        """
        assert isinstance(self.db_session, Session)

        # Ensure we are connected to the correct Neo4j database
        await self.get_story_by_id(new_chapter.story_id)

        added_chapter = await ChapterRepository.insert(self.db_session, new_chapter)
        node_tuples = await self.neo4j_service.insert_story(added_chapter.content)
        for node_label, node_name in node_tuples:
            new_mapping = ChapterNodeMappingBase(
                node_label=node_label,
                node_name=node_name,
                chapter_id=added_chapter.id
            )
            await ChapterNodeMappingRepository.insert(self.db_session, new_mapping)
        return added_chapter
    
    async def insert_chapter_with_ordering(
        self, 
        content: str, 
        title: str, 
        story_id: int, 
        insert_after_chapter_id: int | None = None,
        insert_at_start: bool = False
    ):
        assert isinstance(self.db_session, Session)
        
        new_sort_order = 0.0
        GAP = 10000.0

        # --- LOGIC BRANCHING ---
        if insert_at_start:
            # SCENARIO 0: Insert at the very beginning
            min_order = await ChapterRepository.get_min_sort_order(self.db_session, story_id)
            if min_order is None:
                # Story is empty, just start at GAP
                new_sort_order = GAP
            else:
                # Place before the current first chapter
                new_sort_order = min_order / 2.0

        elif insert_after_chapter_id is None:
            # SCENARIO 1: Append to the end
            max_order = await ChapterRepository.get_max_sort_order(self.db_session, story_id)
            new_sort_order = max_order + GAP
            
        else:
            # SCENARIO 2: Squeeze between existing chapters
            prev_chapter = await ChapterRepository.get_by_id(self.db_session, insert_after_chapter_id)
            if not prev_chapter:
                raise Exception(f"Cannot insert: Chapter ID {insert_after_chapter_id} not found.")
            
            prev_order = prev_chapter.sort_order
            next_chapter = await ChapterRepository.get_next_chapter_by_sort_order(self.db_session, story_id, prev_order)
            
            if next_chapter:
                new_sort_order = (prev_order + next_chapter.sort_order) / 2.0
            else:
                new_sort_order = prev_order + GAP

        # Prepare and save...
        timestamp = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
        chapter_data = ChapterBase(
            title=title,
            content=content,
            story_id=story_id,
            timestamp=timestamp,
            sort_order=new_sort_order 
        )

        return await self.insert_chapter(chapter_data)
    
    async def get_chapter_by_id(self, chapter_id: int):
        assert isinstance(self.db_session, Session)
        return await ChapterRepository.get_by_id(self.db_session, chapter_id)
    
    async def get_all_chapters(self):
        assert isinstance(self.db_session, Session)
        return await ChapterRepository.get_all(self.db_session)
    
    async def get_chapter_by_title(self, story_id: int, title: str):
        assert isinstance(self.db_session, Session)
        return await ChapterRepository.get_chapter_by_title(self.db_session, story_id, title)
    
    async def delete_chapter_by_id(self, chapter_id: int):
        assert isinstance(self.db_session, Session)
        
        return await ChapterRepository.delete_by_id(self.db_session, chapter_id)
    
    async def get_all_chapters_by_story_id(self, story_id: int):
        """
        This function is intended to be called for fetching a session's history
        When the history is fetched, the user intends to write more chapters
        Therefore, the neo4j database should be switched to the story's database
        """
        story = await self.get_story_by_id(story_id)
        await self.neo4j_service.connect_to_existing_database(story.neo_database_name)

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

    #region Image repository

    async def insert_image(self, new_image):
        assert isinstance(self.db_session, Session)
        return await ImageRepository.insert(self.db_session, new_image)
    
    async def get_images_by_story_id(self, story_id: int):
        assert isinstance(self.db_session, Session)
        return await ImageRepository.get_by_story_id(self.db_session, story_id)
    
    #endregion

    #region Neo4j service
    async def get_all_nodes_and_relationships(self, database_name: str):
        return await self.neo4j_service.get_all_nodes_and_relationships(database_name)
    
    #endregion

    #region Cleanup
    def close(self):
        """Closes the database sessions."""
        self.db_session.close()
        self.neo4j_service.close_connection()
    #endregion

if __name__ == "__main__":
    start_db()
    service = PostgresService()

    import asyncio
    from backend.models.postgres.Story import Story
    from backend.models.postgres.Chapter import ChapterBase
    from backend.models.postgres.ChapterNodeMapping import ChapterNodeMappingBase
    from backend.models.postgres.Image import ImageBase

    #region Tests
    async def run_tests():
        print("--- Starting Tests ---")

        # 1. Story Tests
        print("\n[Story Tests]")
        # Insert
        new_story = Story(title="Test Story", neo_database_name="test_story_db")
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

        # 4. Image Tests
        print("\n[Image Tests]")
        new_image = ImageBase(image_path=r"C:\Users\Atvar\Desktop\SEM5\GenerativeAI\New folder\TaleMachine\images\OIP.t6I7VZpL7005vZqkYA-cOQHaIW.webp", story_id=story_id)
        new_image = await service.insert_image(
            new_image
        )
        print(f"Inserted Image: {new_image}")

        images = await service.get_images_by_story_id(story_id)
        print(f"Images for Story {story_id}: {images}")

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
    #endregion