from fastapi import Depends, FastAPI, HTTPException
from app_data import models, database, crud
from sqlalchemy.orm import Session
from app_data.schemas import UserCreate, User, Section, SectionCreate, TextInput, SectionUpdate
from utils import transform_sections
from app_data.custom_exceptions import NoDBInstance
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
 

# models.Base.metadata.drop_all(bind=database.engine)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
def get_user_from_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com", id=1
    )

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = get_user_from_token(token)
    return user

@app.get("/items/")
def read_items(user: User = Depends(get_current_user)):
    # for this request we have to add jwt token as a header for request
    return user

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/users/{user_id}")
async def get_user_handler(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    return user


# @app.get("/text_inputs", response_model=list[TextInput])
# async def get_text_inputs(db: Session = Depends(get_db)):
#     text_inputs = crud.get_text_inputs(db)
#     return text_inputs


@app.get("/sections", response_model=dict[str, Section])
async def get_sections(db: Session = Depends(get_db)):
    sections = crud.get_sections(db)
    sections_dict = transform_sections(sections)
    return sections_dict

@app.get("/sections/{user_id}", response_model=dict[str, Section])
async def get_sections_by_user(user_id, db: Session = Depends(get_db)):
    sections = crud.get_sections_by_user(user_id, db)
    sections_dict = transform_sections(sections)
    return sections_dict

@app.put("/update_sections")
def update_sections(sections: list[SectionUpdate], db: Session = Depends(get_db)):
    for section in sections:
        try:
            crud.update_section(db, section)
        except NoDBInstance:
            raise HTTPException(status_code=400, detail="No section with given id")

    return {"message": "Updated successfully"}

@app.post("/create_sections")
def create_sections(
    user: User, sections: list[SectionCreate], db: Session = Depends(get_db)):

    for section in sections:
        crud.create_section(db, section, user)
    return {"message": "Created successfully"}


@app.post("/users/create_user")
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> User:
    db_user = crud.get_user_by_email(db, email=user.email)
    # or get_user_by_username  if any of them!
    if db_user:
        raise HTTPException(status_code=400, detail="Email is already used")
    new_user = crud.create_user(db, user)
    return new_user


# @app.get("/users", response_model=list[User])
# def get_users(db: Session = Depends(get_db)):
#     users = crud.get_users(db)
#     return users
