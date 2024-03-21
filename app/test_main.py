from fastapi.testclient import TestClient
from sqlalchemy.engine import create
from .main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from .app_data.database import Base
from .dependencies import get_db

import pytest
import os
from .app_data.crud import get_user_by_username, get_user_by_email
from jose import jwt
from dotenv import load_dotenv
from pathlib import Path

dotenv_path = Path("app/.env.api")
load_dotenv(dotenv_path=dotenv_path)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    yield db
    db.close()


client = TestClient(app)
app.dependency_overrides[get_db] = override_get_db

def get_jwt_token_user(jwt_token, db_session):
    payload = jwt.decode(
        jwt_token, SECRET_KEY, algorithms=[ALGORITHM]
    )
    username = payload.get("sub")
    user = get_user_by_username(db_session, username)
    return user

def create_user(username, email):
    response = client.post(
        "/users/create_user",
        json={
            "username": username,
            "email": email,
            "password": "chimichangas4life",
        },
    )
    return response


def test_first_endpoint():
    response = client.get("/")
    assert response.json() == {"detail": "Not Found"}
    assert response.status_code == 404


def test_create_user():
    response = create_user("lumberjack", "lumberjack@gmail.com")
    data = response.json()
    assert data["access_token"]
    assert data["token_type"]
    assert isinstance(data["access_token"], str)
    assert isinstance(data["token_type"], str)


@pytest.mark.parametrize(
    "username, email",
    [
        ("lumberjack1", "lumberjack1@gmail.com"),
        ("lumberjack2 ", " lumberjack2@gmail.com"),
        (" lumberjack3 ", " lumberjack3@gmail.com "),
    ],
)
def test_user_create_in_db(username, email, db_session):
    create_user(username, f"{email.strip()}")
    user_by_username = get_user_by_username(db_session, username.strip())
    user_by_email = get_user_by_email(db_session, email.strip())
    assert user_by_username
    assert user_by_email


@pytest.mark.parametrize(
    "emails, usernames",
    [
        (("same_name", "same_name"), ("same_email", "same_email")),
        (("same_name", "same_name"), ("some_email", "totaly_different_email")),
        (("some_username", "totaly_different_username"), ("same_email", "same_email")),
    ],
)
def test_create_user_dublicates_username(emails, usernames):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    create_user(usernames[0], emails[0])
    response = create_user(usernames[1], emails[1])
    data = response.json()
    assert data == {"detail": "Email or username is already used"}


def test_created_user_token(db_session):
    username = "lumberjack"
    email = "deadpool@example.com"
    response = create_user(username, email)
    jwt_token = response.json().get("access_token", "")
    user = get_jwt_token_user(jwt_token, db_session)
    assert user


@pytest.mark.parametrize(
    "username, email",
    [
        ("lumberjack1", "lumberjack1@gmail.com"),
        ("lumberjack2 ", " lumberjack2@gmail.com"),
        (" lumberjack3 ", " lumberjack3@gmail.com "),
    ],
)
def test_login_token_valid(username, email, db_session):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    create_user(username, email)
    response = client.post(
        "/login",
        json={
            "username": username,
            "password": "chimichangas4life",
        },
    )
    jwt_token = response.json().get("access_token", "")
    user = get_jwt_token_user(jwt_token, db_session)
    assert user

def test_login_error():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    response = client.post(
        "/login",
        json={
            "username": "lumberjack",
            "password": "chimichangas4life",
        },
    )
    assert response.json() == {'detail': 'Incorrect username or password'}


def test_get_user_sections_no_authorise():
    response = client.get('/user/sections/')
    assert response.json() == {'detail': 'Not authenticated'}

def test_get_registered_user_sections():
    response = create_user('lumberjack', 'lumberjack@gmail.com')
    jwt_token = response.json().get("access_token", "")
    response = client.get('/user/sections/', headers={"Authorization": f"Bearer {jwt_token}"})
    assert response.json() == {}

def test_get_login_user_sections():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    create_user('unique_username', 'unique_username@gmail.com')
    response = client.post(
        "/login",
        json={
            "username": "unique_username",
            "password": "chimichangas4life",
        },
    )
    jwt_token = response.json().get("access_token", "")
    response = client.get('/user/sections/', headers={"Authorization": f"Bearer {jwt_token}"})
    assert response.json() == {}
