# Centralized S3 Media Upload Service

A robust, standalone microservice for handling all media generation, processing, and uploading to Amazon S3. This service provides specialized endpoints for different types of media uploads and processing, designed to be called by various AI agents for centralized asset management.

## 🚀 Features

- **Image Upload**: Handle base64 encoded images and raw file uploads
- **Audio Upload**: Download audio from URLs and upload to S3
- **Mermaid Rendering**: Convert Mermaid diagram code to PNG images using headless browser
- **S3 Integration**: Seamless upload to Amazon S3 with proper folder organization
- **User Organization**: Files organized by user ID and media type
- **Health Monitoring**: Built-in health check endpoints
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## 📁 Project Structure

```
assests/
├── upload.py          # Main FastAPI application
├── requirements.txt   # Python dependencies
├── setup.py          # Setup and installation script
├── .env.example      # Environment variables template
├── Dockerfile        # Docker configuration
└── README.md         # This documentation
```

## 🛠️ Installation & Setup

### 1. Quick Setup
```bash
# Clone and navigate to the project
cd assests

# Run the setup script
python setup.py
```

### 2. Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (required for Mermaid rendering)
playwright install chromium

# Copy environment template
cp .env.example .env
# Edit .env with your AWS credentials
```

### 3. Environment Configuration

Create a `.env` file with your AWS credentials:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_BUCKET_NAME=your_s3_bucket_name
AWS_REGION=us-east-1
```

### 4. Run the Service

```bash
# Development mode with auto-reload
uvicorn upload:app --reload

# Production mode
python upload.py
```

The API will be available at:
- **Service**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### 1. Image Upload (`/upload/image`)

**Method**: `POST`  
**Content-Type**: `application/json`

Upload images from base64 encoded data.

**Request Body**:
```json
{
  "file_base64": "iVBORw0KGgoAAAANSUhEUgAA...", // Base64 encoded image
  "file_name": "infographic_topic.png",
  "user_id": "user123",
  "content_type": "image/png"
}
```

**Response**:
```json
{
  "s3_url": "https://bucket.s3.region.amazonaws.com/images/user123/20241201_143022_uuid_infographic_topic.png",
  "file_path": "images/user123/20241201_143022_uuid_infographic_topic.png",
  "message": "Image upload successful"
}
```

**Example Usage**:
```python
import requests
import base64

# Read and encode image
with open("image.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

response = requests.post("http://localhost:8000/upload/image", json={
    "file_base64": image_base64,
    "file_name": "my_image.png",
    "user_id": "user123",
    "content_type": "image/png"
})
```

### 2. Image File Upload (`/upload/image/file`)

**Method**: `POST`  
**Content-Type**: `multipart/form-data`

Upload image files directly via form data.

**Form Fields**:
- `user_id`: String - User identifier
- `file`: File - Image file to upload

**Example Usage**:
```python
import requests

files = {'file': open('image.png', 'rb')}
data = {'user_id': 'user123'}

response = requests.post("http://localhost:8000/upload/image/file", 
                        files=files, data=data)
```

### 3. Audio Upload (`/upload/audio`)

**Method**: `POST`  
**Content-Type**: `application/json`

Download audio from a URL and upload to S3.

**Request Body**:
```json
{
  "source_url": "https://example.com/audio.mp3",
  "file_name": "podcast_episode.mp3",
  "user_id": "user123",
  "content_type": "audio/mpeg"
}
```

**Response**:
```json
{
  "s3_url": "https://bucket.s3.region.amazonaws.com/podcasts/user123/20241201_143022_uuid_podcast_episode.mp3",
  "file_path": "podcasts/user123/20241201_143022_uuid_podcast_episode.mp3",
  "message": "Audio upload successful"
}
```

**Example Usage**:
```python
import requests

response = requests.post("http://localhost:8000/upload/audio", json={
    "source_url": "https://api.speechservice.com/audio/generated_audio.mp3",
    "file_name": "my_podcast.mp3",
    "user_id": "user123",
    "content_type": "audio/mpeg"
})
```

### 4. Mermaid Diagram Rendering (`/render-and-upload/mermaid`)

**Method**: `POST`  
**Content-Type**: `application/json`

Render Mermaid diagram code to PNG and upload to S3.

**Request Body**:
```json
{
  "mermaid_code": "graph TD; A-->B; B-->C;",
  "file_name": "concept_map",
  "user_id": "user123"
}
```

**Response**:
```json
{
  "s3_url": "https://bucket.s3.region.amazonaws.com/diagrams/user123/20241201_143022_uuid_concept_map.png",
  "file_path": "diagrams/user123/20241201_143022_uuid_concept_map.png",
  "message": "Mermaid diagram rendered and uploaded successfully"
}
```

**Example Usage**:
```python
import requests

mermaid_code = """
graph TD
    A[Start] --> B[Process]
    B --> C[End]
    C --> D[Result]
"""

response = requests.post("http://localhost:8000/render-and-upload/mermaid", json={
    "mermaid_code": mermaid_code,
    "file_name": "my_flowchart",
    "user_id": "user123"
})
```

### 5. Generic File Upload (`/upload/`)

**Method**: `POST`  
**Content-Type**: `multipart/form-data`

Legacy endpoint for backward compatibility.

**Form Fields**:
- `user_email`: String - User email
- `file_type`: String - Type/category of file
- `file`: File - File to upload

## 🔧 Agent Integration Examples

### MistakeHeatmapAgent Integration

```python
import requests
import base64

class MistakeHeatmapAgent:
    def __init__(self, upload_service_url="http://localhost:8000"):
        self.upload_service_url = upload_service_url
    
    def save_heatmap_image(self, image_bytes: bytes, user_id: str, filename: str) -> str:
        """Upload heatmap image to S3 via upload service"""
        # Encode image to base64
        image_base64 = base64.b64encode(image_bytes).decode()
        
        # Upload via service
        response = requests.post(f"{self.upload_service_url}/upload/image", json={
            "file_base64": image_base64,
            "file_name": filename,
            "user_id": user_id,
            "content_type": "image/png"
        })
        
        if response.status_code == 200:
            return response.json()["s3_url"]
        else:
            raise Exception(f"Upload failed: {response.text}")
```

### PodcastAgent Integration

```python
import requests

class PodcastAgent:
    def __init__(self, upload_service_url="http://localhost:8000"):
        self.upload_service_url = upload_service_url
    
    def process_audio_url(self, external_audio_url: str, user_id: str, filename: str) -> str:
        """Download and upload audio to our S3 bucket"""
        response = requests.post(f"{self.upload_service_url}/upload/audio", json={
            "source_url": external_audio_url,
            "file_name": filename,
            "user_id": user_id,
            "content_type": "audio/mpeg"
        })
        
        if response.status_code == 200:
            return response.json()["s3_url"]
        else:
            raise Exception(f"Audio upload failed: {response.text}")
```

### ConceptMapGeneratorAgent Integration

```python
import requests

class ConceptMapGeneratorAgent:
    def __init__(self, upload_service_url="http://localhost:8000"):
        self.upload_service_url = upload_service_url
    
    def render_and_upload_mermaid(self, mermaid_code: str, user_id: str, filename: str) -> str:
        """Render Mermaid diagram and upload to S3"""
        response = requests.post(f"{self.upload_service_url}/render-and-upload/mermaid", json={
            "mermaid_code": mermaid_code,
            "file_name": filename,
            "user_id": user_id
        })
        
        if response.status_code == 200:
            return response.json()["s3_url"]
        else:
            raise Exception(f"Mermaid render and upload failed: {response.text}")
```

## 📁 S3 Folder Structure

Files are organized in S3 with the following structure:

```
your-bucket/
├── images/
│   └── user123/
│       └── 20241201_143022_uuid_filename.png
├── podcasts/
│   └── user123/
│       └── 20241201_143022_uuid_filename.mp3
├── diagrams/
│   └── user123/
│       └── 20241201_143022_uuid_filename.png
└── [file_type]/
    └── [timestamp]_[uuid]_[filename]
```

## 🐳 Docker Deployment

```bash
# Build the Docker image
docker build -t s3-media-upload .

# Run the container
docker run -p 8000:8000 --env-file .env s3-media-upload
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key | Yes | - |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | Yes | - |
| `AWS_BUCKET_NAME` | S3 Bucket Name | Yes | - |
| `AWS_REGION` | AWS Region | Yes | - |

### S3 Bucket Configuration

Ensure your S3 bucket has:
1. **Public read access** configured via bucket policy
2. **CORS policy** for web applications:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "POST", "PUT"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

## 🔍 Health Monitoring

The service includes health check endpoints:

- `GET /health` - Check service and S3 connection status
- `GET /` - Basic service information and available endpoints

## 🚨 Error Handling

The service provides detailed error responses:

```json
{
  "detail": "Descriptive error message"
}
```

Common error scenarios:
- Invalid base64 data
- Network issues downloading from URLs
- S3 upload failures
- Mermaid rendering errors
- Invalid file types

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Playwright Documentation](https://playwright.dev/python/)
- [Mermaid Documentation](https://mermaid.js.org/) 