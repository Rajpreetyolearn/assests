FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 🚨 Add this line:
EXPOSE 8070

CMD ["uvicorn", "upload:app", "--host", "0.0.0.0", "--port", "8070"]
