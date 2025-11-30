from pydantic import BaseModel, ConfigDict, Field

class Story(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None
    title: str # The Title of the story
    neo_database_name: str # The name of the Neo4j database where this story's nodes are stored, story can be renamed, that's why it's here
    # Single user application, so no user_id field needed

