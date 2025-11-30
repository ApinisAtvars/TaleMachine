# Stores the image path + the story that this image is from

from pydantic import BaseModel, ConfigDict, Field

class ImageBase(BaseModel):
    id: int | None = None
    image_path: str
    story_id: int