# Stores the image path + the story that this image is from

from pydantic import BaseModel, ConfigDict, Field

class ImageBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None # One to many relationship with Story
    image_path: str # You should put the absolute path to the image file here. Also, save the images in the "images" folder in the project root
    story_id: int
