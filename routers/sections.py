from typing import Annotated
from fastapi import APIRouter
from ..dependencies import get_current_user, get_db
from ..app_data import crud
from fastapi import Depends, HTTPException
from ..app_data.schemas import User, Section, SectionCreate, SectionUpdate, UserAuthenticate
from sqlalchemy.orm import Session
from ..utils.data_mutate import transform_sections
from ..custom_exceptions import NoDBInstance, UserNonExists, WrongSectionID
from ..app_data.schemas import TextInput

router = APIRouter()

@router.get("/text_inputs", response_model=list[TextInput])
async def get_text_inputs(db: Session = Depends(get_db)):
    text_inputs = crud.get_text_inputs(db)
    return text_inputs

@router.get("/sections", response_model=dict[str, Section])
async def get_sections(db: Session = Depends(get_db)):
    sections = crud.get_sections(db)
    sections_dict = transform_sections(sections)
    return sections_dict

@router.get("/user/sections/", response_model=dict[str, Section])
async def get_sections_by_user(user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    sections = crud.get_sections_by_user(user.id, db)
    sections_dict = transform_sections(sections)
    return sections_dict

@router.put("/update_sections")
def update_sections(user: Annotated[UserAuthenticate, Depends(get_current_user)], sections: list[SectionUpdate], db: Session = Depends(get_db)):
    print(user)
    for section in sections:
        try:
            crud.update_section(db, section, user)
        except NoDBInstance:
            raise HTTPException(status_code=400, detail="No section or text input or image input with given id")
        except WrongSectionID:
            raise HTTPException(status_code=400, detail="Not enough permissions to modify a given section")
    return {"message": "Updated successfully"}

@router.post("/create_sections")
def create_sections(user: User, sections: list[SectionCreate], db: Session = Depends(get_db)):
    for section in sections:
        try:
            crud.create_section(db, section, user)
        except NoDBInstance:
            raise HTTPException(status_code=400, detail="Section with such name is already exists!")
        except UserNonExists:
            raise HTTPException(status_code=400, detail="User is not exist")
    return {"message": "Created successfully"}

