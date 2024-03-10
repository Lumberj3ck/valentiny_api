from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    email = Column(String, unique=True)
    password = Column(String)
    sections = relationship("Section", back_populates="user")


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String)
    index = Column(Integer)
    render = Column(Boolean)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("User", back_populates="sections")
    background_color = Column(String)
    text_color = Column(String)
    text_inputs = relationship("TextInput", back_populates="section")
    image_inputs = relationship("ImageInput", back_populates="section")


class TextInput(Base):
    __tablename__ = "text_input"

    id = Column(Integer, primary_key=True, nullable=False)
    index = Column(Integer)
    content = Column(String(length=1000))
    section_id = Column(
        Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False
    )
    section = relationship("Section", back_populates="text_inputs")


class ImageInput(Base):
    __tablename__ = "image_input"

    id = Column(Integer, primary_key=True, nullable=False)
    index = Column(Integer)
    link = Column(String(length=255))
    section_id = Column(
        Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False
    )
    section = relationship("Section", back_populates="image_inputs")
