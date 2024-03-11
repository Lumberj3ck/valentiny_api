from fastapi import APIRouter
from ..dependencies import get_db
from ..app_data.schemas import UserCreate, User
from ..app_data import crud
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/users/create_user")
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> User:
    db_user = crud.get_user_by_email(db, email=user.email)
    # or get_user_by_username  if any of them!
    if db_user:
        raise HTTPException(status_code=400, detail="Email is already used")
    new_user = crud.create_user(db, user)
    return new_user
