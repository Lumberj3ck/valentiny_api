from fastapi.testclient import TestClient
from ..main import app
from ..app_data.database import Base
from ..dependencies import get_db
from .database_initialise import TestingSessionLocal, engine

import pytest
from ..utils.data_mutate import reset_sections_state
from .sections_test_data import *
from .utils import create_user_and_save_sections, create_user_and_update_sections


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


client = TestClient(app)
app.dependency_overrides[get_db] = override_get_db


@pytest.mark.parametrize("test_data", [test_data, incomplete_sections_data])
def test_get_registered_user_saved_sections(test_data):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    jwt_token = create_user_and_save_sections(test_data)[1]
    user_sections = client.get(
        "/user/sections/", headers={"Authorization": f"Bearer {jwt_token}"}
    )

    new_user_data = reset_sections_state(user_sections.json())
    assert user_sections.json()["start_section"]["id"]
    assert new_user_data == test_data


@pytest.mark.parametrize("test_data", [test_data, incomplete_sections_data, []])
def test_create_sections_successfully(test_data):
    sections_save_response = create_user_and_save_sections(test_data)[0]
    assert sections_save_response.json() == {"message": "Saved successfully"}


@pytest.mark.parametrize(
    "test_data", [sections_data_no_unique_index, sections_data_no_unique_image_index]
)
def test_create_sections_index_not_unique(test_data):
    sections_save_response = create_user_and_save_sections(test_data)[0]
    error = "Value error, Input indexes must be unique within a section"
    assert sections_save_response.json()["detail"][0]["msg"] == error


def test_create_section_with_existed_name():
    sections_save_response = create_user_and_save_sections(
        sections_data_with_same_name
    )[0]
    assert sections_save_response.json() == {
        "detail": "Section with such name is already exists!"
    }


@pytest.mark.parametrize("test_data", [test_data, incomplete_sections_data, []])
def test_update_sections(test_data):
    sections_save_response = create_user_and_update_sections(test_data)
    assert sections_save_response.json() == {"message": "Saved successfully"}


@pytest.mark.parametrize("test_data", [test_data, incomplete_sections_data])
def test_update_sections_and_wrong_id(test_data):
    sections_save_response = create_user_and_update_sections(test_data, True)
    assert sections_save_response.json() == {
        "detail": "No section or text input or image input with given id"
    }


# @pytest.mark.parametrize("test_data", [test_data, incomplete_sections_data])
# def test_update_section_wrong_user(test_data):
#     Base.metadata.drop_all(bind=engine)
#     Base.metadata.create_all(bind=engine)
#     create_user_response = create_user("unique_username", "unique_username@gmail.com")
#     jwt_token = create_user_response.json().get("access_token", "")
#     response = client.put(
#         "/save_sections/",
#         headers={"Authorization": f"Bearer {jwt_token}"},
#         json={"sections": test_data },
#     )
#     user_sections = client.get(
#         "/user/sections/", headers={"Authorization": f"Bearer {jwt_token}"}
#     )
#
#     modified_sections = reset_sections_state_with_id(user_sections.json())
#     if random_id:
#         modified_sections[0]['id'] = 999
#     response = client.put(
#         "/save_sections/",
#         headers={"Authorization": f"Bearer {jwt_token}"},
#         json={"sections": modified_sections},
#     )
