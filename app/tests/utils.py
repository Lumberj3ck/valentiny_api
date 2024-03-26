from fastapi.testclient import TestClient
from ..main import app
from ..utils.data_mutate import reset_sections_state_with_id
from .database_initialise import engine, Base

client = TestClient(app)


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


def create_user_and_save_sections(test_data):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    create_user_response = create_user("unique_username", "unique_username@gmail.com")
    jwt_token = create_user_response.json().get("access_token", "")
    response = client.put(
        "/save_sections/",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={"sections": test_data},
    )
    return (response, jwt_token)


def create_user_and_update_sections(test_data, random_id=False):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    create_user_response = create_user("unique_username", "unique_username@gmail.com")
    jwt_token = create_user_response.json().get("access_token", "")
    response = client.put(
        "/save_sections/",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={"sections": test_data},
    )
    user_sections = client.get(
        "/user/sections/", headers={"Authorization": f"Bearer {jwt_token}"}
    )

    modified_sections = reset_sections_state_with_id(user_sections.json())
    if random_id:
        modified_sections[0]["id"] = 999
    response = client.put(
        "/save_sections/",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={"sections": modified_sections},
    )
    return response
