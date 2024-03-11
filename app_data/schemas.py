from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from pydantic import validator


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    created_at: datetime | None

    class Config:
        orm_mode = True


class TextInputCreate(BaseModel):
    index: int
    content: str
    # section_id: int


class ImageInputCreate(BaseModel):
    index: int
    link: str


class TextInput(TextInputCreate):
    id: int


class ImageInput(ImageInputCreate):
    id: int


class SectionNames(Enum):
    start_section = "start_section"
    like_you_section = "like_you_section"
    reasons_like_you_section = "reasons_like_you_section"

# class SectionName(BaseModel):
#     name: str


class SectionBase(BaseModel):
    index: int
    name: str
    render: bool | None
    background_color: str | None
    text_color: str | None


class SectionCreate(SectionBase):
    image_inputs: list[ImageInputCreate] | None = None
    text_inputs: list[TextInputCreate] | None = None

    @validator('text_inputs')
    def validate_text_input_indexes(cls, v, values):
        if v is not None:
            indexes = {input_data.index for input_data in v}
            if len(indexes) != len(v):
                raise ValueError("Text input indexes must be unique within a section")
        return v

    @validator('image_inputs')
    def validate_image_input_indexes(cls, v, values):
        if v is not None:
            indexes = {input_data.index for input_data in v}
            if len(indexes) != len(v):
                raise ValueError("Image input indexes must be unique within a section")
        return v

class SectionUpdate(SectionBase):
    id: int
    image_inputs: list[ImageInput] | None = None
    text_inputs: list[TextInput] | None = None

    class Config:
        orm_mode = True

class Section(SectionBase):
    id: int
    user_id: int
    image_inputs: dict[int, ImageInput] | None = None
    text_inputs: dict[int, TextInput] | None = None

    class Config:
        orm_mode = True
