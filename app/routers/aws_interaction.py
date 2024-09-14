from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Annotated
from ..dependencies import get_current_user
from ..app_data.schemas import User
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

router = APIRouter()

load_dotenv()

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

BUCKET_NAME = os.getenv('AWS_BUCKET')

@router.post("/upload-image/")
async def upload_image(
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...)
):
    await file.seek(0)
    content = await file.read()

    max_content_size = 25 * 1024 * 1024  
    if len(content) > max_content_size:
        raise HTTPException(status_code=400, detail="File size should be less than 50 MB")

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{user.id}_{file.filename}"

    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=unique_filename,
            Body=content,
            ContentType=file.content_type
        )


        url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{unique_filename}"

        return JSONResponse(content={"url": url}, status_code=200)

    except ClientError as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to upload image")
