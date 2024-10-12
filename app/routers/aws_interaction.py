from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from typing import Annotated
from ..dependencies import get_s3_client
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
from ..app_data.schemas import UserAuthenticate
from ..app_data import crud, schemas
from sqlalchemy.orm import Session
from ..dependencies import get_db

import io
import zipfile
import mimetypes
from ..dependencies import get_current_user

    
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

    appropriate_content_type = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp", "image/tiff", "image/ico", "image/ppm", "image/x-icon"]
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


@router.post("/user/upload_website/")
async def upload_website(
    current_user: Annotated[UserAuthenticate, Depends(get_current_user)],
    subdomain_name: str = Form(...),
    domain_name: str = Form(...),
    s3_client: boto3.client = Depends(get_s3_client),
    db: Session = Depends(get_db),
    zip_file: UploadFile = File(...),
):
    subdomain = schemas.SubdomainCreate(name=subdomain_name, domain_name=domain_name)
    if not zip_file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Uploaded file must be a ZIP archive")

    domain = crud.get_domain_by_name(db, subdomain.domain_name)
    if not domain:
        raise HTTPException(status_code=400, detail="The specified domain does not exist")
    
    # Check if the user has available website uploads
    if current_user.website_upload_amount <= 0:
        raise HTTPException(status_code=403, detail="You don't have any website uploads left")

    existing_subdomain = crud.get_subdomain_by_name_and_domain(db, subdomain.name, subdomain.domain_name)
    new_subdomain = None 
    if existing_subdomain:
        if existing_subdomain.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="This subdomain is not available")
    elif not existing_subdomain and current_user.subdomain_amount <= 0:
        raise HTTPException(status_code=403, detail="You don't have any subdomains left")
    else:
        new_subdomain = crud.create_subdomain(db, current_user.id, subdomain.name, subdomain.domain_name)

    # if new_subdomain and current_user.subdomain_amount <= 0:
    #     raise HTTPException(status_code=403, detail="You don't have any subdomains left")

    subdomain_decrease = 1 if new_subdomain else 0
    current_user.subdomain_amount = max(0, current_user.subdomain_amount - subdomain_decrease)
    crud.update_user_amounts(db, current_user)

    domain_parts = subdomain.domain_name.split('.')
    folder_name = f"{domain_parts[0]}/{subdomain.name}"

    try:
        s3_client.head_object(Bucket=WEBSITE_BUCKET_NAME, Key=f"{folder_name}/")
        # If the folder exists, we'll update it
    except ClientError as e:
        if e.response['Error']['Code'] != '404':
            raise HTTPException(status_code=500, detail="Error checking folder existence")

    uploaded_files = []

    zip_content = await zip_file.read()
    zip_io = io.BytesIO(zip_content)

    with zipfile.ZipFile(zip_io, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith('/'):  
                continue

            with zip_ref.open(file_info) as file:
                file_content = file.read()

            content_type, _ = mimetypes.guess_type(file_info.filename)
            if content_type is None:
                content_type = 'application/octet-stream'

            normalized_filename = os.path.normpath(file_info.filename.lstrip('/'))
            
            file_key = f"{folder_name}/{normalized_filename}"
            
            try:
                s3_client.put_object(
                    Bucket=WEBSITE_BUCKET_NAME,
                    Key=file_key,
                    Body=file_content,
                    ContentType=content_type
                )
                uploaded_files.append(normalized_filename)
            except ClientError as e:
                print(f"Error uploading {normalized_filename}: {e}")

    if not uploaded_files:
        raise HTTPException(status_code=400, detail="No files were uploaded")

    current_user.website_upload_amount = max(0, current_user.website_upload_amount - 1)
    crud.update_user_amounts(db, current_user)

    return JSONResponse(content={
        "message": "Website folder uploaded successfully",
        "link": f"https://{subdomain.name}.{subdomain.domain_name}",
    }, status_code=200)