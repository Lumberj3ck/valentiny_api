from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from .database import Base
import datetime



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

class Subdomain(Base):
    __tablename__ = "subdomains"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    domain_id = Column(
        Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False
    )
    domain = relationship("Domain", back_populates="subdomains")
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("User", back_populates="subdomains")
    created_at = Column(DateTime, default=datetime.datetime.now)

    __table_args__ = (UniqueConstraint('name', 'domain_id', name='uq_subdomain_name_domain'),)


class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    subdomains = relationship("Subdomain", back_populates="domain")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    subdomains_amount = Column(Integer, nullable=False)
    websites_upload_amount = Column(Integer, nullable=False)

class PlanUsage(Base):
    __tablename__ = "plan_usage"

    id = Column(Integer, primary_key=True, nullable=False)
    subdomains_count = Column(Integer, nullable=False)
    websites_upload_count = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="plan_usage")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    email = Column(String, unique=True)
    password = Column(String)
    sections = relationship("Section", back_populates="user")
    subdomains = relationship("Subdomain", back_populates="user")
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    plan = relationship("Plan")
    plan_usage = relationship("PlanUsage", back_populates="user")
