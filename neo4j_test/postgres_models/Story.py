from pydantic import BaseModel, ConfigDict, Field

class Story(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str # The Title of the story
    # Single user application, so no user_id field needed