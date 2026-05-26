FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi uvicorn minio python-multipart redis python-dotenv pydantic

COPY . .

EXPOSE 8002
