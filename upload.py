from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import boto3
import os
import uuid
import base64
import io
import httpx
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from typing import Optional
import asyncio
from utils.code_renderer import render_code_to_image

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

# Pydantic models for request/response
class ImageUploadRequest(BaseModel):
    file_base64: Optional[str] = None
    file_name: str
    user_id: str
    content_type: str

class AudioUploadRequest(BaseModel):
    source_url: str
    file_name: str
    user_id: str
    content_type: str

class MermaidRenderRequest(BaseModel):
    mermaid_code: str
    file_name: str
    user_id: str

class CodeRenderRequest(BaseModel):
    code: str
    language: str
    style: Optional[str] = "default"
    file_name: str
    user_id: str

class UploadResponse(BaseModel):
    s3_url: str
    file_path: str
    message: str = "Upload successful"

# Helper function to upload to S3
async def upload_to_s3_bucket(file_stream: io.BytesIO, object_key: str, content_type: str) -> str:
    """Upload a file stream to S3 and return the public URL"""
    try:
        s3.upload_fileobj(
            file_stream,
            S3_BUCKET,
            object_key,
            ExtraArgs={'ContentType': content_type}
        )
        
        # Construct public URL
        public_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{object_key}"
        return public_url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

# Helper function to render Mermaid diagrams
async def render_mermaid_diagram(mermaid_code: str) -> bytes:
    """Render Mermaid code to PNG image using Playwright"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <style>
            body {{ margin: 0; padding: 20px; background: white; }}
            .mermaid {{ background: white; }}
        </style>
    </head>
    <body>
        <div class="mermaid">{mermaid_code}</div>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                themeVariables: {{
                    primaryColor: '#fff',
                    primaryTextColor: '#000',
                    primaryBorderColor: '#000',
                    lineColor: '#000'
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content)
            
            # Wait for Mermaid to render
            await page.wait_for_selector(".mermaid svg", timeout=10000)
            
            # Get the rendered diagram element
            diagram_element = await page.query_selector(".mermaid")
            
            if not diagram_element:
                raise Exception("Mermaid diagram failed to render")
            
            # Take screenshot of the diagram
            image_bytes = await diagram_element.screenshot(type="png")
            await browser.close()
            
            return image_bytes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mermaid rendering failed: {str(e)}")

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Centralized S3 Media Upload Service",
        "version": "1.0.0",
        "endpoints": [
            "/upload/image",
            "/upload/audio", 
            "/render-and-upload/mermaid",
            "/render-and-upload/code",
            "/upload/"
        ]
    }

@app.post("/upload/image", response_model=UploadResponse)
async def upload_image(request: ImageUploadRequest):
    """
    Upload an image to S3. Accepts either base64 encoded image data via JSON
    or supports multipart form data for raw file uploads.
    """
    try:
        # Generate unique object key
        unique_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        object_key = f"images/{request.user_id}/{timestamp}_{unique_id}_{request.file_name}"
        
        if request.file_base64:
            # Handle base64 encoded image
            try:
                # Remove data URL prefix if present (e.g., "data:image/png;base64,")
                if request.file_base64.startswith('data:'):
                    request.file_base64 = request.file_base64.split(',')[1]
                
                image_data = base64.b64decode(request.file_base64)
                image_stream = io.BytesIO(image_data)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="file_base64 is required for image upload")
        
        # Upload to S3
        s3_url = await upload_to_s3_bucket(image_stream, object_key, request.content_type)
        
        return UploadResponse(
            s3_url=s3_url,
            file_path=object_key,
            message="Image upload successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

@app.post("/upload/image/file")
async def upload_image_file(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload an image file directly via multipart form data.
    Alternative to the JSON-based image upload endpoint.
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique object key
        unique_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        object_key = f"images/{user_id}/{timestamp}_{unique_id}_{file.filename}"
        
        # Read file content
        content = await file.read()
        file_stream = io.BytesIO(content)
        
        # Upload to S3
        s3_url = await upload_to_s3_bucket(file_stream, object_key, file.content_type)
        
        return UploadResponse(
            s3_url=s3_url,
            file_path=object_key,
            message="Image file upload successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image file upload failed: {str(e)}")

@app.post("/upload/audio", response_model=UploadResponse)
async def upload_audio(request: AudioUploadRequest):
    """
    Download audio from a source URL and upload it to S3.
    Designed for handling audio files generated by external services.
    """
    try:
        # Generate unique object key
        unique_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        object_key = f"podcasts/{request.user_id}/{timestamp}_{unique_id}_{request.file_name}"
        
        # Download audio from source URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(request.source_url)
                response.raise_for_status()
                
                if not response.headers.get('content-type', '').startswith('audio/'):
                    # Still proceed but log warning
                    print(f"Warning: Source URL may not be audio content. Content-Type: {response.headers.get('content-type')}")
                
                audio_stream = io.BytesIO(response.content)
                
            except httpx.HTTPError as e:
                raise HTTPException(status_code=400, detail=f"Failed to download audio from source URL: {str(e)}")
        
        # Upload to S3
        s3_url = await upload_to_s3_bucket(audio_stream, object_key, request.content_type)
        
        return UploadResponse(
            s3_url=s3_url,
            file_path=object_key,
            message="Audio upload successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio upload failed: {str(e)}")

@app.post("/render-and-upload/mermaid", response_model=UploadResponse)
async def render_and_upload_mermaid(request: MermaidRenderRequest):
    """
    Render Mermaid diagram code to PNG image and upload to S3.
    Uses Playwright to render the diagram in a headless browser.
    """
    try:
        # Generate unique object key
        unique_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Ensure filename has .png extension
        file_name = request.file_name
        if not file_name.lower().endswith('.png'):
            file_name += '.png'
            
        object_key = f"diagrams/{request.user_id}/{timestamp}_{unique_id}_{file_name}"
        
        # Render Mermaid diagram to PNG
        image_bytes = await render_mermaid_diagram(request.mermaid_code)
        image_stream = io.BytesIO(image_bytes)
        
        # Upload to S3
        s3_url = await upload_to_s3_bucket(image_stream, object_key, "image/png")
        
        return UploadResponse(
            s3_url=s3_url,
            file_path=object_key,
            message="Mermaid diagram rendered and uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mermaid rendering and upload failed: {str(e)}")

@app.post("/render-and-upload/code", response_model=UploadResponse)
async def render_and_upload_code(request: CodeRenderRequest):
    """
    Render source code to a PNG image and upload it to S3.
    """
    try:
        # Generate a unique object key
        unique_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Ensure the filename has a .png extension
        file_name = request.file_name
        if not file_name.lower().endswith('.png'):
            file_name += '.png'
            
        object_key = f"code/{request.user_id}/{timestamp}_{unique_id}_{file_name}"
        
        # Render the source code to a PNG image
        image_bytes = await render_code_to_image(
            code=request.code,
            language=request.language,
            style=request.style
        )
        image_stream = io.BytesIO(image_bytes)
        
        # Upload the image to S3
        s3_url = await upload_to_s3_bucket(image_stream, object_key, "image/png")
        
        return UploadResponse(
            s3_url=s3_url,
            file_path=object_key,
            message="Source code rendered and uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code rendering and upload failed: {str(e)}")

@app.post("/upload/")
async def upload_generic_file(
    user_email: str = Form(...),
    file_type: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Generic file upload endpoint (legacy support).
    Maintains backward compatibility with existing systems.
    """
    try:
        # Generate unique ID and timestamped object key
        unique_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        object_key = f"{file_type}/{timestamp}_{unique_id}_{file.filename}"

        # Upload to S3
        content = await file.read()
        file_stream = io.BytesIO(content)
        s3_url = await upload_to_s3_bucket(file_stream, object_key, file.content_type or "application/octet-stream")

        return {
            "s3_key": object_key,
            "public_url": s3_url,
            "message": "Upload successful and file is public"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generic upload failed: {str(e)}")

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test S3 connection
        s3.head_bucket(Bucket=S3_BUCKET)
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "s3_connection": "ok"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
