from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, select
from . import models, schemas
from ..custom_exceptions import (
    NoDBInstance,
    WrongSectionID,
    UserNonExists,
    DBInstanceExists,
)
from ..utils.password_security import get_password_hash


def delete_section(db: Session, section_id: int):
    section = db.query(models.Section).filter(models.Section.id == section_id).first()
    if section:
        db.delete(section)
        db.commit()
        return True
    else:
        return False


def get_users(db: Session):
    return db.query(models.User).all()


def get_user_by_username(db: Session, username: str | None):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str | None):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


# def get_user_by_email(db: Session, email: str):
#     return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_email_or_username(db: Session, user: schemas.UserCreate):
    return (
        db.query(models.User)
        .filter(
            or_(models.User.email == user.email, models.User.username == user.username)
        )
        .first()
    )


def create_user(db: Session, user: schemas.UserCreate):
    password_hash = get_password_hash(user.password)

    db_user = models.User(
        username=user.username, email=user.email, password=password_hash
    )
    save_and_refresh(db, db_user)
    db.commit()
    return db_user



def update_and_refresh(db: Session, object):
    db.commit()
    db.refresh(object)


def save_and_refresh(db: Session, object):
    db.add(object)
    db.commit()
    db.refresh(object)


def get_text_inputs(db: Session):
    return db.query(models.TextInput).all()


def get_sections(db: Session):
    return (
        db.query(models.Section)
        .options(
            joinedload(models.Section.image_inputs),
            joinedload(models.Section.text_inputs),
        )
        .all()
    )


def update_text_input(db: Session, text_input):
    db_text_input = (
        db.query(models.TextInput).filter(models.TextInput.id == text_input.id).first()
    )
    if db_text_input is None:
        raise NoDBInstance

    db_text_input.content = text_input.content
    db_text_input.index = text_input.index
    db.commit()


def get_sections_by_user(user_id, db: Session):
    db_sections = (
        db.query(models.Section)
        .options(
            joinedload(models.Section.image_inputs),
            joinedload(models.Section.text_inputs),
        )
        .filter(models.Section.user_id == user_id)
        .all()
    )
    return db_sections


def update_image_input(db: Session, image_input):
    db_image_input = (
        db.query(models.ImageInput)
        .filter(models.ImageInput.id == image_input.id)
        .first()
    )
    if db_image_input is None:
        raise NoDBInstance

    db_image_input.link = image_input.link
    db_image_input.index = image_input.index
    db.commit()


def update_section(
    db: Session, section: schemas.SectionSave, user: schemas.UserAuthenticate
):
    db_section = (
        db.query(models.Section).filter(models.Section.id == section.id).first()
    )

    if db_section is None:
        raise NoDBInstance

    if db_section.user_id != user.id:
        raise WrongSectionID

    for field, value in section.model_dump().items():
        # print(field, value)
        if field in ("text_inputs", "image_inputs"):
            continue
        setattr(db_section, field, value)

    if section.text_inputs:
        for text_input in section.text_inputs:
            update_text_input(db, text_input)

    if section.image_inputs:
        for image_input in section.image_inputs:
            update_image_input(db, image_input)
    db.commit()


def create_section(
    db: Session, section: schemas.SectionSave, user: schemas.UserAuthenticate
):
    db_section_check = (
        db.query(models.Section).filter_by(user_id=user.id, name=section.name).first()
    )
    user = get_user(db, user.id)

    if not user:
        raise UserNonExists

    if db_section_check:
        raise DBInstanceExists

    db_section = models.Section(
        index=section.index,
        render=section.render,
        name=section.name,
        user_id=user.id,
        background_color=section.background_color,
        text_color=section.text_color,
    )
    save_and_refresh(db, db_section)
    if section.text_inputs:
        for text_input in section.text_inputs:
            db_text_input = models.TextInput(
                index=text_input.index,
                content=text_input.content,
                section_id=db_section.id,
            )
            save_and_refresh(db, db_text_input)

    if section.image_inputs:
        for image_input in section.image_inputs:
            db_image_input = models.ImageInput(
                index=image_input.index, link=image_input.link, section_id=db_section.id
            )
            save_and_refresh(db, db_image_input)

def get_user_subdomains(db: Session, user_id: int):
    return db.query(models.Subdomain).filter(models.Subdomain.user_id == user_id).all()

def get_subdomain_by_name_and_domain(db: Session, subdomain_name: str, domain_name: str):
    return db.query(models.Subdomain).join(models.Domain).filter(
        models.Subdomain.name == subdomain_name,
        models.Domain.name == domain_name
    ).first()

def get_domain_by_name(db: Session, domain_name: str):
    return db.query(models.Domain).filter(models.Domain.name == domain_name).first()

def create_subdomain(db: Session, user_id: int, subdomain_name: str, domain_name: str):
    domain = get_domain_by_name(db, domain_name)
    if not domain:
        raise NoDBInstance
    
    new_subdomain = models.Subdomain(
        name=subdomain_name,
        user_id=user_id,
        domain_id=domain.id
    )
    save_and_refresh(db, new_subdomain)
    return new_subdomain

def create_domain(db: Session, domain_name: str):
    new_domain = models.Domain(
        name=domain_name
    )
    save_and_refresh(db, new_domain)
    return new_domain

def get_user_domains(db: Session, user_id: int):
    result = (
        db.query(
            models.Subdomain.name.label('subdomain'),
            models.Domain.name.label('domain')
        )
        .join(models.Subdomain.domain)
        .filter(models.Subdomain.user_id == user_id)
        .all()
    )
    return [{"name": subdomain, "domain_name": domain} for subdomain, domain in result]


def init_data(db: Session):
    default_domains = [
        {"name": "my-valentine-postcard.site"},
        {"name": "postcard.site"}
    ]
    for domain in default_domains:
        if not db.query(models.Domain).filter(models.Domain.name == domain["name"]).first():
            new_domain = models.Domain(**domain)
            db.add(new_domain)
    
    db.commit()