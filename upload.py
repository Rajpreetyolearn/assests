from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, UTC
import boto3
import os
import uuid
import base64
import io
import httpx
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = FastAPI(
    title="Centralized S3 Media Upload Service",
    description="A robust microservice for handling media generation, processing, and uploading to S3",
    version="1.0.0"
)

# S3 config from environment
S3_BUCKET = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

if not S3_BUCKET or not AWS_REGION:
    raise ValueError("AWS_BUCKET_NAME and AWS_REGION environment variables are required")

# Initialize S3 client (automatically uses keys from env)
s3 = boto3.client("s3", region_name=AWS_REGION)
@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/upload/")
async def upload_generic_file(
    user_email: str = Form(...),
    file_type: str = Form(...),
    file: UploadFile = File(...)
):
    # Generate unique ID and timestamped object key
    unique_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    object_key = f"{file_type}/{unique_id}__{file.filename}"

    # Upload to S3 (no ACL, assumes public access via bucket policy)
    content = await file.read()
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=object_key,
        Body=content,
        ContentType=file.content_type
    )

    # Construct public URL
    public_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{object_key}"

    return {
        "s3_key": object_key,
        "public_url": public_url,
        "message": "Upload successful and file is public"
    }
