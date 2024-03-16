import os
from datetime import timedelta
from fastapi import APIRouter, status
from ..dependencies import get_db, create_access_token
from ..app_data.schemas import UserCreate, UserCredentials, Token
# from fastapi.security import OAuth2PasswordRequestForm
from ..app_data import crud
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from ..utils.password_security import authenticate_user
from dotenv import load_dotenv
from pathlib import Path

router = APIRouter()


dotenv_path = Path('.api_env')
load_dotenv(dotenv_path=dotenv_path)

@router.post("/users/create_user/")
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> Token:
    db_user = crud.get_user_by_email_or_username(db, user)

    if db_user:
        raise HTTPException(status_code=400, detail="Email or username is already used")
    new_user = crud.create_user(db, user)
    if not new_user:
        raise HTTPException(status_code=400, detail="User creating failed")
    access_token_expires = timedelta(minutes=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 1440)))
    access_token = create_access_token(
            data={"sub": new_user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

# @router.get("/users/{user_id}")
# async def get_user_handler(user_id: int, db: Session = Depends(get_db)):
#     user = crud.get_user(db, user_id)
#     return user

# @router.get("/users", response_model=list[User])
# def get_users(db: Session = Depends(get_db)):
#     users = crud.get_users(db)
#     return users

@router.post("/login/")
async def login_for_access_token(
        credentials: UserCredentials, 
        # form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Session = Depends(get_db)) -> Token:
    user = authenticate_user(db, credentials.username.lower(), credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
