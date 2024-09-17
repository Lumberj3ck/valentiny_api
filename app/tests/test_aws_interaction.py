from fastapi.testclient import TestClient
from ..main import app
from unittest.mock import MagicMock
import io
from ..dependencies import get_s3_client
from botocore.exceptions import ClientError


mock_client = MagicMock()

mock_client_error = MagicMock()

def mock_s3_client():
    mock_client.put_object.return_value = "https://fake-s3-url.com/test_image.jpg"
    return mock_client

def mock_s3_client_put_object_error():
    mock_client_error.put_object.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Mocked error"}}, "PutObject"
    )
    return mock_client_error


app.dependency_overrides[get_s3_client] = mock_s3_client
client = TestClient(app)

def test_upload_image():
    image_content = b"fake image content"
    image = io.BytesIO(image_content)

    unique_filename = f"test_image_name"
    response = client.post(
        "/upload_image/",
        files={"file": (unique_filename, image, "image/jpeg")}
    )

    assert response.status_code == 200
    assert "url" in response.json()
    assert mock_client.put_object.call_count == 1

def test_upload_image_too_large():
    image_content = b"fake image content" * 1000000
    image = io.BytesIO(image_content)

    unique_filename = f"test_image_name"
    response = client.post(
        "/upload_image/",
        files={"file": (unique_filename, image, "image/jpeg")}
    )

    assert response.status_code == 413


def test_upload_image_error():
    app.dependency_overrides[get_s3_client] = mock_s3_client_put_object_error

    image_content = b"fake image content"
    image = io.BytesIO(image_content)

    unique_filename = f"test_image_name"
    response = client.post(
        "/upload_image/",
        files={"file": (unique_filename, image, "image/jpeg")}
    )

    assert response.status_code == 500
    assert mock_client.put_object.call_count == 1