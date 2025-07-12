#!/usr/bin/env python3
"""
Test script for the Centralized S3 Media Upload Service
This script demonstrates how to use all the endpoints with example data.
"""

import requests
import base64
import json
from io import BytesIO
from PIL import Image
import time
import os

# Service configuration
SERVICE_URL = os.getenv("SERVICE_URL", "http://localhost:8001")
TEST_USER_ID = "test_user_123"

def create_test_image() -> str:
    """Create a simple test image and return as base64"""
    # Create a simple colored rectangle
    image = Image.new('RGB', (200, 100), color='blue')
    
    # Convert to base64
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    return base64.b64encode(image_bytes).decode()

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{SERVICE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_service_info():
    """Test the service info endpoint"""
    print("\n📋 Testing service info...")
    try:
        response = requests.get(f"{SERVICE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Service info failed: {e}")
        return False

def test_image_upload():
    """Test base64 image upload"""
    print("\n🖼️  Testing image upload (base64)...")
    try:
        test_image_b64 = create_test_image()
        
        data = {
            "file_base64": test_image_b64,
            "file_name": "test_image.png",
            "user_id": TEST_USER_ID,
            "content_type": "image/png"
        }
        
        response = requests.post(f"{SERVICE_URL}/upload/image", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Image uploaded successfully!")
            print(f"S3 URL: {result['s3_url']}")
            print(f"File Path: {result['file_path']}")
            return True
        else:
            print(f"❌ Upload failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Image upload test failed: {e}")
        return False

def test_mermaid_rendering():
    """Test Mermaid diagram rendering"""
    print("\n📊 Testing Mermaid diagram rendering...")
    try:
        mermaid_code = """
        graph TD
            A[Start] --> B[Process Data]
            B --> C{Decision}
            C -->|Yes| D[Success]
            C -->|No| E[Error]
            D --> F[End]
            E --> F[End]
        """
        
        data = {
            "mermaid_code": mermaid_code,
            "file_name": "test_flowchart",
            "user_id": TEST_USER_ID
        }
        
        response = requests.post(f"{SERVICE_URL}/render-and-upload/mermaid", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Mermaid diagram rendered and uploaded!")
            print(f"S3 URL: {result['s3_url']}")
            print(f"File Path: {result['file_path']}")
            return True
        else:
            print(f"❌ Mermaid rendering failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Mermaid rendering test failed: {e}")
        return False

def test_audio_upload():
    """Test audio upload from URL"""
    print("\n🎵 Testing audio upload from URL...")
    try:
        # Using a test audio URL (this would normally be from a podcast generation service)
        # Note: This will fail if the URL doesn't exist, but demonstrates the endpoint
        data = {
            "source_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
            "file_name": "test_audio.wav",
            "user_id": TEST_USER_ID,
            "content_type": "audio/wav"
        }
        
        response = requests.post(f"{SERVICE_URL}/upload/audio", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Audio uploaded successfully!")
            print(f"S3 URL: {result['s3_url']}")
            print(f"File Path: {result['file_path']}")
            return True
        else:
            print(f"⚠️  Audio upload failed (expected if test URL unavailable): {response.text}")
            return False
            
    except Exception as e:
        print(f"⚠️  Audio upload test failed (expected if test URL unavailable): {e}")
        return False

def test_image_upload_from_text_file():
    """Test uploading an image using the base64 string stored in text.txt"""
    print("\n🖼️  Testing image upload (base64 from text.txt)...")
    try:
        # Read base64 string from text.txt
        with open("text.txt", "r", encoding="utf-8") as f:
            b64_data = f.read().strip()

        if not b64_data:
            print("❌ text.txt is empty or could not be read")
            return False

        data = {
            "file_base64": b64_data,
            "file_name": "text_file_image.png",
            "user_id": TEST_USER_ID,
            "content_type": "image/png"
        }

        response = requests.post(f"{SERVICE_URL}/upload/image", json=data)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Image uploaded successfully from text.txt!")
            print(f"S3 URL: {result['s3_url']}")
            print(f"File Path: {result['file_path']}")
            return True
        else:
            print(f"❌ Upload failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Image upload test from text.txt failed: {e}")
        return False

def test_code_render_and_upload():
    """Test rendering source code and uploading it to S3"""
    print("\n🎨 Testing code rendering and upload...")
    try:
        # Sample Python code
        python_code = """
import os

def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
"""
        data = {
            "code": python_code,
            "language": "python",
            "file_name": "hello_world_code.png",
            "user_id": TEST_USER_ID,
            "style": "solarized-dark"
        }
        
        response = requests.post(f"{SERVICE_URL}/render-and-upload/code", json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Code rendering and upload successful: {result['s3_url']}")
            # You can add more assertions here, e.g., check if the URL is valid
            return True
        else:
            print(f"❌ Code rendering and upload failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ An error occurred during code rendering test: {e}")
        return False

def test_complex_mermaid_render():
    """Test rendering a complex Mermaid diagram provided by the user"""
    print("\n🔬 Testing complex Mermaid diagram rendering...")
    try:
        mermaid_code = "flowchart TD\\n    A[Cellular Respiration] -->|Overall Process| B[Glycolysis]\\n    A -->|Overall Process| C[Krebs Cycle (Citric Acid Cycle)]\\n    A -->|Overall Process| D[Electron Transport Chain]\\n\\n    B -->|Occurs in| E[Cytoplasm]\\n    B -->|Starts with| F[Glucose]\\n    F -->|Yields| B\\n    B -->|Produces| G[Pyruvate]\\n    B -->|Generates small| H[ATP]\\n    B -->|Generates| I[NADH]\\n\\n    G -->|Converted to| J[Acetyl-CoA]\\n    J -->|Enters| C\\n    C -->|Occurs in| K[Mitochondria]\\n    C -->|Generates small| H\\n    C -->|Generates| I\\n    C -->|Generates| L[FADH2]\\n    C -->|Releases| M[Carbon Dioxide]\\n\\n    I -->|Donates electrons to| D\\n    L -->|Donates electrons to| D\\n    D -->|Occurs in| K\\n    D -->|Utilizes| N[Oxygen]\\n    N -->|Final electron acceptor in| D\\n    D -->|Generates large amount of| H\\n    D -->|Produces| O[Water]\\n\\n    H -->|Provides energy for cellular activities| A"
        
        data = {
            "mermaid_code": mermaid_code,
            "file_name": "cellular_respiration_diagram.png",
            "user_id": TEST_USER_ID,
            "chart_type": "concept map"  # Extra field to test robustness
        }
        
        response = requests.post(f"{SERVICE_URL}/render-and-upload/mermaid", json=data, timeout=60)
        
        if response.status_code == 200:
            print("✅ PASSED: Complex Mermaid diagram rendered and uploaded successfully.")
            print(f"   S3 URL: {response.json().get('s3_url')}")
            return True
        else:
            print(f"❌ FAILED: Complex Mermaid test failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Could not connect to service: {e}")
        return False

def run_all_tests():
    """Runs all defined tests and summarizes the results"""
    print("🚀 Starting full test suite...")
    
    # List of all test functions
    tests_to_run = [
        test_service_info,
        test_health_check,
        test_image_upload,
        test_audio_upload,
        test_image_upload_from_text_file,
        test_code_render_and_upload,
        test_complex_mermaid_render,
    ]
    
    results = {"passed": 0, "failed": 0, "total": len(tests_to_run)}
    
    for test_func in tests_to_run:
        print(f"\n{'='*20} Running {test_func.__name__.replace('_', ' ')} {'='*20}")
        if test_func():
            results["passed"] += 1
            print("✅ PASSED")
        else:
            results["failed"] += 1
            print("❌ FAILED")
        time.sleep(1)  # Small delay between tests
    
    print(f"\n{'='*60}")
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    for key, value in results.items():
        print(f"{key:<15}: {value}")
    
    print(f"\nOverall: {results['passed']}/{results['total']} tests passed")
    
    if results['passed'] == results['total']:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check your service configuration and AWS credentials.")

if __name__ == "__main__":
    run_all_tests() 