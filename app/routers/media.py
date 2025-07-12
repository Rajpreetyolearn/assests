from fastapi import APIRouter, UploadFile, File, Form, HTTPException
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
from typing import Optional
import asyncio
from app.utils.code_renderer import render_code_to_image

# Load environment variables from .env
load_dotenv()

router = APIRouter()

# --- Pydantic Models ---
class UploadResponse(BaseModel):
    success: bool
    uploaded_url: str
    message: str

class ImageUploadRequest(BaseModel):
    file_name: str
    file_base64: str
    content_type: str

class MermaidRenderRequest(BaseModel):
    mermaid_code: str
    style: str = "default"
    file_name: Optional[str] = None

class CodeRenderRequest(BaseModel):
    code: str
    language: str
    style: str = "default"
    show_line_numbers: bool = True
    file_name: Optional[str] = None

# --- Environment and S3 Setup ---
S3_BUCKET = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

if not S3_BUCKET or not AWS_REGION:
    raise ValueError("AWS_BUCKET_NAME and AWS_REGION environment variables are required")

s3 = boto3.client("s3", region_name=AWS_REGION)

# Helper function to upload to S3
async def upload_to_s3_bucket(file_stream: io.BytesIO, object_key: str, content_type: str) -> str:
    """
    Uploads a file stream to an S3 bucket.
    Returns the public URL of the uploaded file.
    """
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=object_key,
            Body=file_stream.getvalue(),
            ContentType=content_type
        )
        public_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{object_key}"
        return public_url
    except Exception as e:
        raise e

async def render_mermaid_diagram(code: str, theme: str) -> bytes:
    """Renders Mermaid code to a PNG image using mermaid.ink API."""
    try:
        graphbytes = code.encode("ascii")
        base64_bytes = base64.b64encode(graphbytes)
        base64_string = base64_bytes.decode("ascii")
        
        url = f"https://mermaid.ink/img/{base64_string}?theme={theme}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.content
    except httpx.HTTPStatusError as e:
        raise Exception(f"Failed to render Mermaid diagram from mermaid.ink: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred during Mermaid rendering: {str(e)}")

# --- Endpoints ---
@router.post("/upload/")
async def upload_generic_file(
    file_type: str = Form(...),
    file: UploadFile = File(...)
):
    unique_id = str(uuid.uuid4())
    object_key = f"{file_type}/{unique_id}/{file.filename}"
    content = await file.read()
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=object_key,
        Body=content,
        ContentType=file.content_type
    )
    public_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{object_key}"
    return {
        "s3_key": object_key,
        "public_url": public_url,
        "message": "Upload successful and file is public"
    }

@router.post("/upload/image", response_model=UploadResponse)
async def upload_image(request: ImageUploadRequest):
    try:
        unique_id = str(uuid.uuid4())
        object_key = f"images/{unique_id}/{request.file_name}"
        if request.file_base64:
            image_data = base64.b64decode(request.file_base64)
            image_stream = io.BytesIO(image_data)
        else:
            raise HTTPException(status_code=400, detail="No image data provided. Use 'file_base64' field.")
        public_url = await upload_to_s3_bucket(image_stream, object_key, request.content_type)
        return {"success": True, "uploaded_url": public_url, "message": "Upload successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/image/file", response_model=UploadResponse)
async def upload_image_file(file: UploadFile = File(...)):
    try:
        unique_id = str(uuid.uuid4())
        object_key = f"images/{unique_id}/{file.filename}"
        file_content = await file.read()
        file_stream = io.BytesIO(file_content)
        public_url = await upload_to_s3_bucket(file_stream, object_key, file.content_type)
        return {"success": True, "uploaded_url": public_url, "message": "Upload successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/audio", response_model=UploadResponse)
async def upload_audio_file(file: UploadFile = File(...)):
    try:
        unique_id = str(uuid.uuid4())
        object_key = f"audio/{unique_id}/{file.filename}"
        file_content = await file.read()
        file_stream = io.BytesIO(file_content)
        public_url = await upload_to_s3_bucket(file_stream, object_key, file.content_type)
        return {"success": True, "uploaded_url": public_url, "message": "Upload successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/render-and-upload/mermaid", response_model=UploadResponse)
async def handle_mermaid_render(request: MermaidRenderRequest):
    try:
        image_bytes = await render_mermaid_diagram(request.mermaid_code, request.style)
        image_stream = io.BytesIO(image_bytes)
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        file_name = request.file_name or f"{timestamp}_{unique_id}.png"
        object_key = f"generated/mermaid/{unique_id}/{file_name}"
        public_url = await upload_to_s3_bucket(image_stream, object_key, "image/png")
        return {"success": True, "uploaded_url": public_url, "message": "Mermaid diagram rendered and uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render and upload Mermaid diagram: {str(e)}")

@router.post("/render-and-upload/code", response_model=UploadResponse)
async def handle_code_render(request: CodeRenderRequest):
    try:
        image_bytes = await render_code_to_image(request.code, request.language, request.style, request.show_line_numbers)
        image_stream = io.BytesIO(image_bytes)
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        file_name = request.file_name or f"{timestamp}_{unique_id}.png"
        object_key = f"generated/code/{unique_id}/{file_name}"
        public_url = await upload_to_s3_bucket(image_stream, object_key, "image/png")
        return {"success": True, "uploaded_url": public_url, "message": "Code snippet rendered and uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render and upload code: {str(e)}") 