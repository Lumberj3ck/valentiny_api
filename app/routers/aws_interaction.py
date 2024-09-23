from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Annotated
from ..dependencies import get_s3_client
# from ..app_data.schemas import User
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

import io
import zipfile
import mimetypes
from ..dependencies import get_current_user
from ..app_data.schemas import User
from fastapi import Form

    
from PIL import Image
import io
import re

router = APIRouter()

load_dotenv()

# s3_client = boto3.client(
#     's3',
#     aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
#     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
#     region_name=os.getenv('AWS_REGION')
# )

IMAGE_BUCKET_NAME = os.getenv('AWS_BUCKET')
WEBSITE_BUCKET_NAME = os.getenv('AWS_WEBSITE_BUCKET')


@router.post("/upload_image/")
async def upload_image(
    s3_client: boto3.client = Depends(get_s3_client),
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    await file.seek(0)
    content = await file.read()

    max_content_size = 5 * 1024 * 1024  
    if len(content) > max_content_size:
        raise HTTPException(status_code=413, detail="Entity too Large")

    sanitized_filename = re.sub(r'[^a-zA-Z0-9._\-<>]', '', file.filename.replace('/', ''))
    
    if not sanitized_filename:
        raise HTTPException(status_code=400, detail="Invalid filename after sanitization")
    file.filename = sanitized_filename

    unique_filename = file.filename

    try:
        s3_client.head_object(Bucket=IMAGE_BUCKET_NAME, Key=unique_filename)
        import time
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{file.filename}"
    except ClientError as e:
        if e.response['Error']['Code'] != '404':
            raise HTTPException(status_code=500, detail="Error checking file existence")

    appropriate_content_type = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp", "image/tiff", "image/ico", "image/ppm"]
    buf_img = io.BytesIO(content)
    webp_img_buf = io.BytesIO()

    if file.content_type in appropriate_content_type:
        if file.content_type != "image/webp":
            with Image.open(buf_img) as img:
                img.save(webp_img_buf, format="webp")
        else:
            webp_img_buf.write(content)
    else:
        raise HTTPException(status_code=400, detail="Invalid file extension")

    content = webp_img_buf.getvalue()
    file_content_type = "image/webp"


    try:
        s3_client.put_object(
            Bucket=IMAGE_BUCKET_NAME,
            Key=unique_filename,
            Body=content,
            ContentType=file_content_type
        )


        url = f"https://{IMAGE_BUCKET_NAME}.s3.amazonaws.com/{unique_filename}"

        return JSONResponse(content={"url": url}, status_code=200)

    except ClientError as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to upload image")



# We need to check by our database if the current user created a website where 
# he wants to upload the files to.
# if not create a db entry for him.
# @router.post("/upload_website_zip/")
# async def upload_website_zip(
#     s3_client: boto3.client = Depends(get_s3_client),
#     current_user: User = Depends(get_current_user),
#     folder_name: str = Form(...),
#     zip_file: UploadFile = File(...)
# ):
#     if not current_user:
#         raise HTTPException(status_code=401, detail="User not authenticated")

#     if not zip_file.filename.endswith('.zip'):
#         raise HTTPException(status_code=400, detail="Uploaded file must be a ZIP archive")

#     try:
#         s3_client.head_object(Bucket=WEBSITE_BUCKET_NAME, Key=f"{folder_name}/")
#         raise HTTPException(status_code=400, detail="Folder already exists")
#     except ClientError as e:
#         if e.response['Error']['Code'] != '404':
#             raise HTTPException(status_code=500, detail="Error checking folder existence")

#     uploaded_files = []

#     # Read the zip file content into memory
#     zip_content = await zip_file.read()
#     zip_io = io.BytesIO(zip_content)

#     # Open the zip file from memory
#     with zipfile.ZipFile(zip_io, 'r') as zip_ref:
#         # Iterate through the files in the zip
#         for file_info in zip_ref.infolist():
#             if file_info.filename.endswith('/'):  # Skip directories
#                 continue

#             # Read the file content
#             with zip_ref.open(file_info) as file:
#                 file_content = file.read()

#             # Determine the content type
#             content_type, _ = mimetypes.guess_type(file_info.filename)
#             if content_type is None:
#                 content_type = 'application/octet-stream'

#             # Remove leading slashes and normalize the path
#             normalized_filename = os.path.normpath(file_info.filename.lstrip('/'))
            
#             # Upload the file to S3
#             file_key = f"{folder_name}/{normalized_filename}"
#             try:
#                 s3_client.put_object(
#                     Bucket=WEBSITE_BUCKET_NAME,
#                     Key=file_key,
#                     Body=file_content,
#                     ContentType=content_type
#                 )
#                 uploaded_files.append(normalized_filename)
#             except ClientError as e:
#                 print(f"Error uploading {normalized_filename}: {e}")

#     if not uploaded_files:
#         raise HTTPException(status_code=400, detail="No files were uploaded")

#     return JSONResponse(content={
#         "message": "Website folder uploaded successfully",
#         "folder_name": folder_name,
#         "uploaded_files": uploaded_files
#     }, status_code=200)