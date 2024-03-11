from pydantic import BaseModel
from enum import Enum
from datetime import datetime


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
