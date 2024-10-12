import pytest
from fastapi.testclient import TestClient
from ..main import app
from unittest.mock import MagicMock
import io
from ..dependencies import get_s3_client
from botocore.exceptions import ClientError


# mock_client = MagicMock()

# mock_client_error = MagicMock()

from ..app_data import schemas
from ..dependencies import get_current_user

# def mock_s3_client():
#     mock_client.put_object.return_value = "https://fake-s3-url.com/test_image.jpg"
#     return mock_client

# def mock_s3_client_put_object_error():
#     mock_client_error.put_object.side_effect = ClientError(
#         {"Error": {"Code": "500", "Message": "Mocked error"}}, "PutObject"
#     )
#     return mock_client_error

# app.dependency_overrides[get_s3_client] = mock_s3_client
client = TestClient(app)

def test_current_user():
    return schemas.UserAuthenticate(id=1, username="testuser", email="test@example.com", website_upload_amount=2, subdomain_amount=2)

@pytest.fixture
def mock_get_current_user():
    app.dependency_overrides[get_current_user] = test_current_user
    yield
    del app.dependency_overrides[get_current_user]

@pytest.fixture(scope="function")
def mocked_s3_client():
    mock_client = MagicMock()
    mock_client.put_object.return_value = "https://fake-s3-url.com/test_image.jpg"
    app.dependency_overrides[get_s3_client] = lambda: mock_client
    yield mock_client
    mock_client.reset_mock()
    del app.dependency_overrides[get_s3_client]

@pytest.fixture(scope="function")
def mocked_s3_client_put_object_error():
    mock_client_error = MagicMock()
    mock_client_error.put_object.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Mocked error"}}, "PutObject"
    )
    app.dependency_overrides[get_s3_client] = lambda: mock_client_error
    yield mock_client_error
    mock_client_error.reset_mock()
    del app.dependency_overrides[get_s3_client]

@pytest.mark.parametrize("image_path", ["./app/tests/test_data/8.jpg", "./app/tests/test_data/file_example_gif.gif", "./app/tests/test_data/file_example_webp.webp", "./app/tests/test_data/file_example_png.png", "./app/tests/test_data/file_example_tiff.tiff", "./app/tests/test_data/file_example_ico.ico"])
def test_upload_image(image_path, mocked_s3_client):
    with open(image_path, "rb") as image:
        unique_filename = f"test_image_name"
        response = client.post(
            "/upload_image/",
            files={"file": (unique_filename, image, "image/jpeg")}
        )

    assert response.status_code == 200
    assert "url" in response.json()
    assert mocked_s3_client.put_object.call_count == 1

def test_upload_image_too_large():
    image_content = b"fake image content" * 1000000
    image = io.BytesIO(image_content)

    unique_filename = f"test_image_name"
    response = client.post(
        "/upload_image/",
        files={"file": (unique_filename, image, "image/jpeg")}
    )

    assert response.status_code == 413


def test_upload_image_error(mocked_s3_client_put_object_error):
    # app.dependency_overrides[get_s3_client] = mock_s3_client_put_object_error

    with open("./app/tests/test_data/8.jpg", "rb") as image:
        unique_filename = f"test_image_name"
        response = client.post(
            "/upload_image/",
            files={"file": (unique_filename, image, "image/jpeg")}
        )

    assert response.status_code == 500
    assert mocked_s3_client_put_object_error.put_object.call_count == 1


def test_upload_image_invalid_extension():
    with open("./app/tests/test_data/8.jpg", "rb") as image:
        unique_filename = f"test_image_name.txt"
        response = client.post(
            "/upload_image/",
            files={"file": (unique_filename, image, "text/plain")}
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid file extension"

def test_upload_image_duplicate_filename(mocked_s3_client):
    # mock_client.reset_mock()
    # app.dependency_overrides[get_s3_client] = mock_s3_client

    with open("./app/tests/test_data/8.jpg", "rb") as image:
        unique_filename = f"test_image_name"
        response = client.post(
            "/upload_image/",
            files={"file": (unique_filename, image, "image/jpeg")}
        )

    assert response.status_code == 200
    assert "url" in response.json()
    assert mocked_s3_client.put_object.call_count == 1

    # Try uploading the same file again to trigger the duplicate filename logic
    with open("./app/tests/test_data/8.jpg", "rb") as image:
        response = client.post(
            "/upload_image/",
            files={"file": (unique_filename, image, "image/jpeg")}
        )

    assert response.status_code == 200
    assert "url" in response.json()
    assert mocked_s3_client.put_object.call_count == 2

# --- Upload website tests ---

@pytest.fixture
def mock_crud_functions(monkeypatch):
    mock_get_domain = MagicMock()
    mock_get_subdomain = MagicMock()
    mock_create_subdomain = MagicMock()
    mock_update_user_amounts = MagicMock()

    monkeypatch.setattr('app.app_data.crud.get_domain_by_name', mock_get_domain)
    monkeypatch.setattr('app.app_data.crud.get_subdomain_by_name_and_domain', mock_get_subdomain)
    monkeypatch.setattr('app.app_data.crud.create_subdomain', mock_create_subdomain)
    monkeypatch.setattr('app.app_data.crud.update_user_amounts', mock_update_user_amounts)

    return mock_get_domain, mock_get_subdomain, mock_create_subdomain, mock_update_user_amounts

def test_upload_website_success(mock_crud_functions, mock_get_current_user, mocked_s3_client):
    # app.dependency_overrides[get_current_user] = mock_get_current_user
    # mock_client.reset_mock()

    mock_get_domain, mock_get_subdomain, mock_create_subdomain, mock_update_user_amounts = mock_crud_functions
    mock_get_domain.return_value = True
    mock_get_subdomain.return_value = None
    mock_create_subdomain.return_value = schemas.SubdomainCreate(name="test", domain_name="example.com")

    with open("./app/tests/test_data/test_website.zip", "rb") as zip_file:
        response = client.post(
            "/user/upload_website/",
            data={"subdomain_name": "test", "domain_name": "example.com"},
            files={"zip_file": ("test_website.zip", zip_file, "application/zip")}
        )
    mock_get_domain.assert_called_once_with(mock_get_domain.call_args[0][0], "example.com")
    mock_get_subdomain.assert_called_once_with(mock_get_subdomain.call_args[0][0], "test", "example.com")
    mock_create_subdomain.assert_called_once_with(mock_create_subdomain.call_args[0][0], 1, "test", "example.com")
    mock_update_user_amounts.call_count == 2
    assert response.status_code == 200
    assert mocked_s3_client.put_object.call_count == 2

    # del app.dependency_overrides[get_current_user]

from dataclasses import dataclass

@dataclass
class MockSubdomainWithUser:
    id: int
    name: str
    domain_name: str
    user_id: int

def test_upload_website_success_to_existing_subdomain(mock_crud_functions, mock_get_current_user, mocked_s3_client):
    # app.dependency_overrides[get_current_user] = mock_get_current_user

    mock_get_domain, mock_get_subdomain, mock_create_subdomain, mock_update_user_amounts = mock_crud_functions
    mock_get_domain.return_value = True
    mock_get_subdomain.return_value = MockSubdomainWithUser(id=1, name="test", domain_name="example.com", user_id=1)

    with open("./app/tests/test_data/test_website.zip", "rb") as zip_file:
        response = client.post(
            "/user/upload_website/",
            data={"subdomain_name": "test", "domain_name": "example.com"},
            files={"zip_file": ("test_website.zip", zip_file, "application/zip")}
        )

    assert response.status_code == 200
    mocked_s3_client.put_object.assert_called()
    mock_get_domain.assert_called_once_with(mock_get_domain.call_args[0][0], "example.com")
    mock_get_subdomain.assert_called_once_with(mock_get_subdomain.call_args[0][0], "test", "example.com")
    mock_create_subdomain.assert_not_called()
    mock_update_user_amounts.call_count == 1

    # del app.dependency_overrides[get_current_user]

def test_upload_website_invalid_file(mock_crud_functions, mock_get_current_user, mocked_s3_client):
    # app.dependency_overrides[get_current_user] = mock_get_current_user
    mock_get_domain, mock_get_subdomain, mock_create_subdomain, mock_update_user_amounts = mock_crud_functions

    with open("./app/tests/test_data/8.jpg", "rb") as image_file:
        response = client.post(
            "/user/upload_website/",
            data={"subdomain_name": "test", "domain_name": "example.com"},
            files={"zip_file": ("test_image.jpg", image_file, "image/jpeg")}
        )

    assert response.status_code == 400
    assert "Uploaded file must be a ZIP archive" in response.json()["detail"]
    mock_get_domain.assert_not_called()
    mock_get_subdomain.assert_not_called()
    mock_create_subdomain.assert_not_called()
    mock_update_user_amounts.assert_not_called()

    # del app.dependency_overrides[get_current_user]

def test_upload_website_domain_not_exist(mock_crud_functions, mock_get_current_user):
    # app.dependency_overrides[get_current_user] = mock_get_current_user
    mock_get_domain, mock_get_subdomain, mock_create_subdomain, mock_update_user_amounts = mock_crud_functions
    mock_get_domain.return_value = None

    with open("./app/tests/test_data/test_website.zip", "rb") as zip_file:
        response = client.post(
            "/user/upload_website/",
            data={"subdomain_name": "test", "domain_name": "nonexistent.com"},
            files={"zip_file": ("test_website.zip", zip_file, "application/zip")}
        )

    assert response.status_code == 400
    assert "The specified domain does not exist" in response.json()["detail"]
    mock_get_domain.assert_called_once_with(mock_get_domain.call_args[0][0], "nonexistent.com")
    mock_get_subdomain.assert_not_called()
    mock_create_subdomain.assert_not_called()
    mock_update_user_amounts.assert_not_called()

    # del app.dependency_overrides[get_current_user]

def test_upload_website_no_uploads_left(mock_crud_functions):
    mock_get_domain, mock_get_subdomain, mock_create_subdomain, mock_update_user_amounts = mock_crud_functions

    def override_get_current_user():
        return schemas.UserAuthenticate(id=1, username="testuser", email="test@example.com", website_upload_amount=0, subdomain_amount=1)
    
    app.dependency_overrides[get_current_user] = override_get_current_user

    with open("./app/tests/test_data/test_website.zip", "rb") as zip_file:
        response = client.post(
            "/user/upload_website/",
            data={"subdomain_name": "test", "domain_name": "example.com"},
            files={"zip_file": ("test_website.zip", zip_file, "application/zip")}
        )
    assert response.status_code == 403
    assert "You don't have any website uploads left" in response.json()["detail"]
    mock_get_domain.assert_called_once_with(mock_get_domain.call_args[0][0], "example.com")
    mock_get_subdomain.assert_not_called()
    mock_create_subdomain.assert_not_called()
    mock_update_user_amounts.assert_not_called()

    del app.dependency_overrides[get_current_user]

def test_upload_website_no_subdomains_left(mock_crud_functions):
    mock_get_domain, mock_get_subdomain, mock_create_subdomain, mock_update_user_amounts = mock_crud_functions
    mock_get_subdomain.return_value = None
    
    def override_get_current_user():
        return schemas.UserAuthenticate(id=1, username="testuser", email="test@example.com", website_upload_amount=1, subdomain_amount=0)
    
    app.dependency_overrides[get_current_user] = override_get_current_user

    with open("./app/tests/test_data/test_website.zip", "rb") as zip_file:
        response = client.post(
            "/user/upload_website/",
            data={"subdomain_name": "test", "domain_name": "example.com"},
            files={"zip_file": ("test_website.zip", zip_file, "application/zip")}
        )

    print(response.json())
    assert response.status_code == 403
    assert "You don't have any subdomains left" in response.json()["detail"]
    mock_get_domain.assert_called_once_with(mock_get_domain.call_args[0][0], "example.com")
    mock_get_subdomain.assert_called_once()
    mock_create_subdomain.assert_not_called()
    mock_update_user_amounts.assert_not_called()
    # mock_update_user_amounts.assert_called_once_with(mock_update_user_amounts.call_args[0][0], override_get_current_user())

    del app.dependency_overrides[get_current_user]

def test_upload_website_subdomain_not_available(mock_crud_functions, mock_get_current_user):
    # app.dependency_overrides[get_current_user] = mock_get_current_user
    # mock_client.reset_mock()
    mock_get_domain, mock_get_subdomain, mock_create_subdomain, mock_update_user_amounts = mock_crud_functions
    mock_get_domain.return_value = True
    mock_get_subdomain.return_value = MockSubdomainWithUser(id=1, name="test", domain_name="example.com", user_id=2)

    with open("./app/tests/test_data/test_website.zip", "rb") as zip_file:
        response = client.post(
            "/user/upload_website/",
            data={"subdomain_name": "test", "domain_name": "example.com"},
            files={"zip_file": ("test_website.zip", zip_file, "application/zip")}
        )

    assert response.status_code == 400
    assert "This subdomain is not available" in response.json()["detail"]
    mock_get_domain.assert_called_once_with(mock_get_domain.call_args[0][0], "example.com")
    mock_get_subdomain.assert_called_once_with(mock_get_subdomain.call_args[0][0], "test", "example.com")
    mock_create_subdomain.assert_not_called()
    mock_update_user_amounts.assert_not_called()

    # del app.dependency_overrides[get_current_user]