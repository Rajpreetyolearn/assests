from fastapi import FastAPI
from .routers import media
import boto3
import os

app = FastAPI(
    title="Centralized S3 Media Upload Service",
    description="A service to upload, render, and manage media assets on S3.",
    version="1.0.0"
)

app.include_router(media.router)

# --- Root and Health Check Endpoints ---
@app.get("/")
def read_root():
    """Provide service information."""
    return {"service_name": "S3 Media Upload Service", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Check service health and S3 connection."""
    try:
        # A quick check to see if we can connect to S3
        s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
        s3.list_buckets()
        return {"status": "healthy", "s3_connection": "ok"}
    except Exception as e:
        return {"status": "unhealthy", "s3_connection": "error", "detail": str(e)} 