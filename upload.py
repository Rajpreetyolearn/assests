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
from typing import Optional
import asyncio
from utils.code_renderer import render_code_to_image

# Load environment variables from .env
load_dotenv()

# --- Pydantic Models ---
class UploadResponse(BaseModel):
    success: bool
    uploaded_url: str
    message: str

class ImageUploadRequest(BaseModel):
    user_id: str
    file_name: str
    file_base64: str
    content_type: str

class MermaidRenderRequest(BaseModel):
    mermaid_code: str
    user_id: str
    style: str = "default"
    file_name: Optional[str] = None

class CodeRenderRequest(BaseModel):
    code: str
    language: str
    user_id: str
    style: str = "default"
    show_line_numbers: bool = True
    file_name: Optional[str] = None

# --- FastAPI App ---
app = FastAPI(
    title="Centralized S3 Media Upload Service",
    description="A service to upload, render, and manage media assets on S3.",
    version="1.0.0"
)

# --- Environment and S3 Setup ---
# S3 config from environment
S3_BUCKET = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

if not S3_BUCKET or not AWS_REGION:
    raise ValueError("AWS_BUCKET_NAME and AWS_REGION environment variables are required")

# Initialize S3 client (automatically uses keys from env)
s3 = boto3.client("s3", region_name=AWS_REGION)

# --- Root and Health Check Endpoints ---
@app.get("/")
def read_root():
    """Provide service information."""
    return {"service_name": "S3 Media Upload Service", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Check service health and S3 connection."""
    try:
        s3.list_buckets()
        return {"status": "healthy", "s3_connection": "ok"}
    except Exception as e:
        return {"status": "unhealthy", "s3_connection": "error", "detail": str(e)}

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
        # Construct the public URL
        public_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{object_key}"
        return public_url
    except Exception as e:
        # Re-raise to be caught by endpoint exception handlers
        raise e

# --- Rendering Functions ---
async def render_mermaid_diagram(code: str, theme: str) -> bytes:
    """Renders Mermaid code to a PNG image using mermaid.ink API."""
    try:
        graphbytes = code.encode("ascii")
        base64_bytes = base64.b64encode(graphbytes)
        base64_string = base64_bytes.decode("ascii")
        
        url = f"https://mermaid.ink/img/{base64_string}?theme={theme}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.content
    except httpx.HTTPStatusError as e:
        # Log or handle the specific error from the external API
        raise Exception(f"Failed to render Mermaid diagram from mermaid.ink: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred during Mermaid rendering: {str(e)}")


# --- Endpoints ---
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

@app.post("/upload/image", response_model=UploadResponse)
async def upload_image(request: ImageUploadRequest):
    """
    Upload an image to S3. Accepts either base64 encoded image data via JSON
    or a direct file upload.
    """
    try:
        # Generate unique object key
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        object_key = f"images/{request.user_id}/{timestamp}_{unique_id}_{request.file_name}"
        
        if request.file_base64:
            # Decode base64 and create a file stream
            image_data = base64.b64decode(request.file_base64)
            image_stream = io.BytesIO(image_data)
        else:
            raise HTTPException(status_code=400, detail="No image data provided. Use 'file_base64' field.")

        public_url = await upload_to_s3_bucket(image_stream, object_key, request.content_type)
        return {"success": True, "uploaded_url": public_url, "message": "Upload successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/image/file", response_model=UploadResponse)
async def upload_image_file(user_id: str = Form(...), file: UploadFile = File(...)):
    """Upload an image file directly to S3."""
    try:
        # Generate unique object key
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        object_key = f"images/{user_id}/{timestamp}_{unique_id}_{file.filename}"
        
        # Read file content
        file_content = await file.read()
        file_stream = io.BytesIO(file_content)
        
        public_url = await upload_to_s3_bucket(file_stream, object_key, file.content_type)
        return {"success": True, "uploaded_url": public_url, "message": "Upload successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/audio", response_model=UploadResponse)
async def upload_audio_file(user_id: str = Form(...), file: UploadFile = File(...)):
    """Upload an audio file directly to S3."""
    try:
        # Generate unique object key
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        object_key = f"audio/{user_id}/{timestamp}_{unique_id}_{file.filename}"

        # Read file content and upload
        file_content = await file.read()
        file_stream = io.BytesIO(file_content)
        
        public_url = await upload_to_s3_bucket(file_stream, object_key, file.content_type)
        return {"success": True, "uploaded_url": public_url, "message": "Upload successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/render-and-upload/mermaid", response_model=UploadResponse)
async def handle_mermaid_render(request: MermaidRenderRequest):
    """
    Renders a Mermaid diagram to a PNG and uploads it to S3.
    """
    try:
        # Render the mermaid diagram to an image
        image_bytes = await render_mermaid_diagram(request.mermaid_code, request.style)
        image_stream = io.BytesIO(image_bytes)

        # Generate a unique file name
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        file_name = request.file_name or f"{timestamp}_{unique_id}.png"
        object_key = f"generated/mermaid/{request.user_id}/{file_name}"

        # Upload the rendered image to S3
        public_url = await upload_to_s3_bucket(image_stream, object_key, "image/png")
        return {"success": True, "uploaded_url": public_url, "message": "Mermaid diagram rendered and uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render and upload Mermaid diagram: {str(e)}")

@app.post("/render-and-upload/code", response_model=UploadResponse)
async def handle_code_render(request: CodeRenderRequest):
    """
    Renders a code snippet to a PNG image and uploads it to S3.
    """
    try:
        # Render the code to an image
        image_bytes = await render_code_to_image(request.code, request.language, request.style, request.show_line_numbers)
        image_stream = io.BytesIO(image_bytes)

        # Generate a unique file name
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        file_name = request.file_name or f"{timestamp}_{unique_id}.png"
        object_key = f"generated/code/{request.user_id}/{file_name}"

        # Upload the rendered image to S3
        public_url = await upload_to_s3_bucket(image_stream, object_key, "image/png")
        return {"success": True, "uploaded_url": public_url, "message": "Code snippet rendered and uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render and upload code: {str(e)}")
