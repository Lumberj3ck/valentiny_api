from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql.functions import mode
from . import models, schemas
from ..custom_exceptions import NoDBInstance


def get_users(db: Session):
    return db.query(models.User).all()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(
        username=user.username, email=user.email, password=fake_hashed_password
    )
    # db.add(db_user)
    # db.commit()
    # db.refresh(db_user)
    save_and_refresh(db, db_user)
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
    db_text_input = db.query(models.TextInput).filter(models.TextInput.id == text_input.id).first()
    if db_text_input is None:
        raise NoDBInstance

    db_text_input.content = text_input.content
    db_text_input.index = text_input.index
    db.commit()

def get_sections_by_user(user_id, db: Session):
    db_sections = db.query(models.Section).options(joinedload(models.Section.image_inputs), joinedload(models.Section.text_inputs)).filter(models.Section.user_id == user_id).all()
    print(db_sections)
    return db_sections

def update_image_input(db: Session, image_input):
    db_image_input = db.query(models.ImageInput).filter(models.ImageInput.id == image_input.id).first()
    if db_image_input is None:
        raise NoDBInstance

    db_image_input.link = image_input.link
    db_image_input.index = image_input.index
    db.commit()

def update_section(db: Session, section: schemas.SectionUpdate):
    db_section = db.query(models.Section).filter(models.Section.id == section.id).first()

    if db_section is None:
        raise NoDBInstance

    for field, value in section.dict().items():
        print(field, value)
        if field in ('text_inputs', 'image_inputs'):
            continue
        setattr(db_section, field, value)

    if section.text_inputs:
        for text_input in section.text_inputs:
            update_text_input(db, text_input)

    if section.image_inputs:
        for image_input in section.image_inputs:
            update_image_input(db, image_input)
    db.commit()


def create_section(db: Session, section: schemas.SectionCreate, user: schemas.User):
    db_section_check = db.query(models.Section).filter_by(user_id=user.id, name=section.name).first()
    print(db_section_check)

    if db_section_check:
        raise NoDBInstance

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
                section_id=db_section.id
            )
            save_and_refresh(db, db_text_input)

    if section.image_inputs:
        for image_input in section.image_inputs:
            db_image_input = models.ImageInput(
                index=image_input.index, link=image_input.link, section_id=db_section.id
            )
            save_and_refresh(db, db_image_input)
