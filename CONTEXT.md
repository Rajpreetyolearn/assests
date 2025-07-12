# Media Upload Service: Integration Context

## 1. Overview

This document provides all the necessary context for an AI agent or another team to integrate with the Media Upload Service. The service is designed to be a simple, stateless API that accepts various media-related inputs, processes them, and returns a public URL to the final asset stored in AWS S3.

The key design principle is simplicity: send your content to the correct endpoint, and you get a URL back. There is no need to manage user accounts or sessions; each upload is treated as an independent event, and a unique UUID is used to ensure that every file has a distinct, non-clashable storage path.

## 2. Shared Response Model

All endpoints, upon success, return a consistent JSON object. This makes handling responses predictable.

*   **Success Response** (200 OK):
    ```json
    {
      "success": true,
      "uploaded_url": "https://<your-bucket>.s3.<your-region>.amazonaws.com/...",
      "message": "A descriptive message of the outcome."
    }
    ```
    *   `success` (bool): Always `true` for a successful operation.
    *   `uploaded_url` (str): The permanent, public URL of the generated media asset.
    *   `message` (str): A human-readable confirmation message.

*   **Error Response** (4xx or 5xx):
    If an error occurs, the service will return a standard FastAPI error response with a `detail` key containing the error message.

---

## 3. Endpoints and Integration Examples

### 3.1. Render Mermaid Diagram

*   **Use Case**: Your agent has generated a diagram using Mermaid syntax and needs to display it as an image.
*   **Agent Example**: A **Forecast Agent** generating a sequence diagram for a weather prediction model.
*   **Endpoint**: `POST /render-and-upload/mermaid`
*   **Request Body** (`application/json`):
    ```json
    {
      "mermaid_code": "graph TD\\n    A[Start] --> B{Is it raining?};\\n    B -->|Yes| C[Take an umbrella];\\n    B -->|No| D[Enjoy the sun];",
      "file_name": "weather_forecast_flow.png",
      "style": "default"
    }
    ```
    *   `mermaid_code` (str): The raw Mermaid syntax.
    *   `file_name` (str, optional): A descriptive name for the file. If not provided, a unique name will be generated.
    *   `style` (str, optional): The Mermaid theme to use (e.g., `default`, `dark`, `neutral`).

### 3.2. Render Source Code

*   **Use Case**: Your agent has written a block of code and wants to present it with syntax highlighting in a visually appealing image.
*   **Agent Example**: A **Code-Gen Agent** demonstrating a Python function.
*   **Endpoint**: `POST /render-and-upload/code`
*   **Request Body** (`application/json`):
    ```json
    {
      "code": "def calculate_sum(a, b):\\n    return a + b",
      "language": "python",
      "file_name": "sum_function.png",
      "style": "monokai"
    }
    ```
    *   `code` (str): The raw source code.
    *   `language` (str): The language for syntax highlighting (e.g., `python`, `javascript`).
    *   `file_name` (str, optional): A descriptive name for the file.
    *   `style` (str, optional): A `pygments` style name.

### 3.3. Upload Base64 Image

*   **Use Case**: Your agent has generated an image in memory as a Base64-encoded string and needs to upload it to get a public URL.
*   **Agent Example**: A **Mystic Heatmap Agent** or an **Infographic Agent** that generates PNG data directly.
*   **Endpoint**: `POST /upload/image`
*   **Request Body** (`application/json`):
    ```json
    {
      "file_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
      "file_name": "generated_heatmap.png",
      "content_type": "image/png"
    }
    ```
    *   `file_base64` (str): The raw, Base64-encoded image data.
    *   `file_name` (str): A descriptive name for the file.
    *   `content_type` (str): The MIME type of the image (e.g., `image/png`, `image/jpeg`).

### 3.4. Direct File Upload

*   **Use Case**: Your system has a file on disk (image, audio, etc.) and needs to upload it directly.
*   **Agent Example**: An agent that has saved a generated audio clip locally and needs to upload it.
*   **Endpoint**: `POST /upload/image/file` or `POST /upload/audio`
*   **Request Body**: `multipart/form-data`
    This is not a JSON request. The file should be sent as part of a form. Here's a Python `requests` example:
    ```python
    import requests

    file_path = 'path/to/your/local_image.png'
    upload_url = 'http://localhost:8001/upload/image/file'

    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'image/png')}
        response = requests.post(upload_url, files=files)
        
        if response.status_code == 200:
            print("Upload successful:", response.json()['uploaded_url'])
        else:
            print("Upload failed:", response.text)
    ```
    This same pattern works for the `/upload/audio` endpoint by changing the URL and providing an audio file. 