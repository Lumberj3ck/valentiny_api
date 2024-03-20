from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from pydantic import validator


class UserCredentials(BaseModel):
    username: str | None = None
    password: str | None = None

    @validator("username")
    def convert_username_to_lower(cls, v):
        return v.lower().strip()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserBase(BaseModel):
    username: str
    email: str

    @validator("username")
    def convert_username_to_lower(cls, v):
        return v.lower().strip()

    @validator("email")
    def convert_email_to_lower(cls, v):
        return v.lower().strip()


class UserCreate(UserBase):
    password: str


class UserAuthenticate(UserBase):
    id: int


class User(UserBase):
    id: int
    created_at: datetime | None

    class Config:
        orm_mode = True


class TextInput(BaseModel):
    index: int
    content: str
    id: int | None = None
    # section_id: int


class ImageInput(BaseModel):
    index: int
    link: str | None
    id: int | None = None


# class TextInput(TextInputCreate):
#     id: int | None = None
#
#
# class ImageInput(ImageInputCreate):
#     id: int | None = None


class SectionNames(Enum):
    start_section = "start_section"
    like_you_section = "like_you_section"
    reasons_like_you_section = "reasons_like_you_section"


class SectionBase(BaseModel):
    index: int
    name: str
    render: bool | None
    background_color: str | None
    text_color: str | None


def validate_input_indexes(v):
    if v is not None:
        print(v)
        indexes = {input_data["index"] for input_data in v}
        if len(indexes) != len(v):
            raise ValueError("Input indexes must be unique within a section")
    return v


# class SectionCreate(SectionBase):
#     image_inputs: list[ImageInputCreate] | None = None
#     text_inputs: list[TextInputCreate] | None = None
#
#     _validate_text_input_indexes = validator('text_inputs', pre=True)(validate_input_indexes)
#     _validate_image_input_indexes = validator('image_inputs', pre=True)(validate_input_indexes)
#
class SectionSave(SectionBase):
    id: int | None = None
    image_inputs: list[ImageInput] | None = None
    text_inputs: list[TextInput] | None = None

    _validate_text_input_indexes = validator("text_inputs", pre=True)(
        validate_input_indexes
    )
    _validate_image_input_indexes = validator("image_inputs", pre=True)(
        validate_input_indexes
    )

    class Config:
        orm_mode = True


class Section(SectionBase):
    id: int
    # user_id: int
    image_inputs: dict[int, ImageInput] | None = None
    text_inputs: dict[int, TextInput] | None = None

    class Config:
        orm_mode = True
