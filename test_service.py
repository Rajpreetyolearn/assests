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

TEST_USER_ID = "test_user_123"

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
    assert "service" in response.json()

def test_image_upload_base64():
    """Test base64 image upload"""
    test_image_b64 = create_test_image()
    
    data = {
        "file_base64": test_image_b64,
        "file_name": "test_image.png",
        "user_id": TEST_USER_ID,
        "content_type": "image/png"
    }
    
    response = client.post("/upload/image", json=data)
    assert response.status_code == 200
    result = response.json()
    assert "s3_url" in result
    assert "file_path" in result
    assert result['s3_url'].startswith("https://")

def test_mermaid_rendering_and_upload():
    """Test Mermaid diagram rendering and upload"""
    mermaid_code = """
    graph TD
        A[Start] --> B[Process Data]
        B --> C{Decision}
        C -->|Yes| D[Success]
        C -->|No| E[Error]
    """
    
    data = {
        "mermaid_code": mermaid_code,
        "file_name": "test_flowchart",
        "user_id": TEST_USER_ID
    }
    
    response = client.post("/render-and-upload/mermaid", json=data)
    assert response.status_code == 200
    result = response.json()
    assert "s3_url" in result
    assert "file_path" in result
    assert result['file_path'].endswith('.png')

def test_code_rendering_and_upload():
    """Test rendering source code and uploading it"""
    python_code = """
import os

def hello_world():
    print("Hello, World!")
"""
    data = {
        "code": python_code,
        "language": "python",
        "file_name": "hello_world_code.png",
        "user_id": TEST_USER_ID,
        "style": "default"
    }
    
    response = client.post("/render-and-upload/code", json=data)
    assert response.status_code == 200
    result = response.json()
    assert "s3_url" in result
    assert "file_path" in result
    assert result['file_path'].endswith('.png')

def test_image_file_upload():
    """Test uploading an image file directly."""
    image = Image.new('RGB', (100, 100), color = 'red')
    image_bytes = BytesIO()
    image.save(image_bytes, format='jpeg')
    image_bytes.seek(0)

    files = {'file': ('test_image.jpg', image_bytes, 'image/jpeg')}
    data = {'user_id': TEST_USER_ID}
    response = client.post("/upload/image/file", data=data, files=files)
    
    assert response.status_code == 200
    result = response.json()
    assert "s3_url" in result
    assert "file_path" in result
    assert result['file_path'].endswith('.jpg')

# To run these tests, execute `pytest` in your terminal. 