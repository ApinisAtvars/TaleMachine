# Stores the image path + the story that this image is from

from pydantic import BaseModel, ConfigDict, Field

class ImageBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None # One to many relationship with Story
    # Idea: when this is in a container, maybe have the image path be just the filename, and the image save directory be a host bind mounted volume?
    image_path: str # For now, you should put the absolute path to the image file here. Also, save the images in the "images" folder in the project root
    story_id: int
    chapter_id: int | None = None # Image can be associated with a chapter, but doesn't have to be
