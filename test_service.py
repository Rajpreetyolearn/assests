#!/usr/bin/env python3
"""
Test script for the Centralized S3 Media Upload Service
This script demonstrates how to use all the endpoints with example data.
"""

from fastapi.testclient import TestClient
import pytest
from upload import app  # Import your FastAPI app
import base64
from PIL import Image
from io import BytesIO

# Create a TestClient instance
client = TestClient(app)

def create_test_image() -> str:
    """Create a simple test image and return as base64"""
    image = Image.new('RGB', (200, 100), color='blue')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    return base64.b64encode(image_bytes).decode()

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "s3_connection" in data

def test_service_info():
    """Test the service info endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service_name" in response.json()

def test_upload_image_base64():
    """Test uploading a base64 encoded image"""
    image_b64 = create_test_image()
    payload = {
        "file_name": "test_image.png",
        "file_base64": image_b64,
        "content_type": "image/png"
    }
    response = client.post("/upload/image", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "uploaded_url" in data
    assert data["uploaded_url"].startswith("https://")
    assert "test_image.png" in data["uploaded_url"]

def test_upload_image_file():
    """Test uploading an image as a file"""
    image = Image.new('RGB', (100, 50), color = 'red')
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    
    files = {'file': ('test_file_upload.jpg', buffer, 'image/jpeg')}
    
    response = client.post("/upload/image/file", files=files)
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "uploaded_url" in res_data
    assert res_data["uploaded_url"].startswith("https://")
    assert "test_file_upload.jpg" in res_data["uploaded_url"]

def test_render_and_upload_mermaid():
    """Test rendering a Mermaid diagram and uploading it"""
    mermaid_code = "graph TD; A-->B;"
    payload = {
        "mermaid_code": mermaid_code,
        "style": "default"
    }
    response = client.post("/render-and-upload/mermaid", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "uploaded_url" in data
    assert data["uploaded_url"].startswith("https://")
    assert ".png" in data["uploaded_url"]

def test_render_and_upload_code():
    """Test rendering a code snippet and uploading it"""
    code_snippet = "print('Hello, World!')"
    payload = {
        "code": code_snippet,
        "language": "python",
    }
    response = client.post("/render-and-upload/code", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "uploaded_url" in data
    assert data["uploaded_url"].startswith("https://")
    assert ".png" in data["uploaded_url"]

# To run these tests, execute `pytest` in your terminal. 