"""
GPD Storage Microservice — FastAPI + MinIO
==========================================
Runs independently on port 8002.
Both Django (GPD Management Service) and the AI Model talk to this service.

Endpoints:
  POST   /upload/source              → upload source file, return source_key
  POST   /upload/document            → upload document file, return doc_key
  GET    /file/{file_key:path}       → get presigned download URL
  DELETE /file/{file_key:path}       → delete a file
  POST   /result                     → AI model stores result JSON here
  GET    /result/{result_id}         → Django fetches result by id

Run:
  pip install fastapi uvicorn minio python-multipart
  uvicorn main:app --host 0.0.0.0 --port 8002 --reload
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from minio import Minio
from minio.error import S3Error
from pydantic import BaseModel
from typing import Optional, List
from datetime import timedelta
import uuid, os, json, io
import redis
app = FastAPI(title="GPD Storage Service", version="1.0.0")

# ── MinIO client ──────────────────────────────────────────────────────────────
MINIO_ENDPOINT   = os.getenv("MINIO_ENDPOINT",   "127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password123")
MINIO_BUCKET     = os.getenv("MINIO_BUCKET",     "veritas")

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
   # secure=True,
   secure=False,
)

# In-memory result store (replace with Redis or DB in production)

r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0)
'''
# In store_result():
r.setex(result_id, 3600 * 24, json.dumps(result.dict()))  # TTL = 24h

# In get_result():
cached = r.get(result_id)
if cached: 
    return json.loads(cached)
'''
# ── Startup: ensure bucket exists ─────────────────────────────────────────────
@app.on_event("startup")
def startup():
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
        print(f"Created bucket: {MINIO_BUCKET}")
    else:
        print(f"Bucket ready: {MINIO_BUCKET}")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "bucket": MINIO_BUCKET}


# ── Upload source file ────────────────────────────────────────────────────────
@app.post("/upload/source")
async def upload_source(
    workspace_id: int,
    file: UploadFile = File(...)
):
    """
    Called by Django when user uploads a source file.
    Stores in MinIO under: sources/{workspace_id}/{uuid}.ext
    Returns the file_key to store in SQL DB.
    """
    ext      = os.path.splitext(file.filename)[1].lower()
    file_key = f"sources/{workspace_id}/{uuid.uuid4()}{ext}"
    data     = await file.read()

    client.put_object(
        MINIO_BUCKET,
        file_key,
        io.BytesIO(data),
        length=len(data),
        content_type="application/octet-stream",
    )
    return {
        "file_key":  file_key,
        "file_name": file.filename,
        "file_size": len(data),
    }


# ── Upload document file ──────────────────────────────────────────────────────
@app.post("/upload/document")
async def upload_document(
    workspace_id: int,
    file: UploadFile = File(...)
):
    """
    Called by Django when user uploads a document to check.
    Stores in MinIO under: documents/{workspace_id}/{uuid}.ext
    Returns the file_key to store in SQL DB.
    """
    ext      = os.path.splitext(file.filename)[1].lower()
    file_key = f"documents/{workspace_id}/{uuid.uuid4()}{ext}"
    data     = await file.read()

    client.put_object(
        MINIO_BUCKET,
        file_key,
        io.BytesIO(data),
        length=len(data),
        content_type="application/octet-stream",
    )
    return {
        "file_key":  file_key,
        "file_name": file.filename,
        "file_size": len(data),
    }


# ── Get presigned URL for a file ──────────────────────────────────────────────
@app.get("/file/{file_key:path}")
def get_file_url(file_key: str, expires_minutes: int = 60):
    """
    Returns a temporary presigned URL for the file.
    Both Django and AI model use this to download files.
    URL expires after expires_minutes (default 60 min).
    """
    try:
        url = client.presigned_get_object(
            MINIO_BUCKET,
            file_key,
            expires=timedelta(minutes=expires_minutes),
        )
        return {"url": url, "file_key": file_key, "expires_minutes": expires_minutes}
    except S3Error as e:
        raise HTTPException(status_code=404, detail=f"File not found: {file_key}")


# ── Delete a file ─────────────────────────────────────────────────────────────
@app.delete("/file/{file_key:path}")
def delete_file(file_key: str):
    """Called by Django when user deletes a source or document."""
    try:
        client.remove_object(MINIO_BUCKET, file_key)
        return {"deleted": file_key}
    except S3Error as e:
        raise HTTPException(status_code=404, detail=f"File not found: {file_key}")


# ── AI Model stores result here ───────────────────────────────────────────────
class AnalysisResult(BaseModel):
    submission_id:    int
    document_id:      int
    plagiarism_score: float
    original_percentage: float
    matched_sources: List[dict]           # [{"source_name": str, "match_percentage": float}]
    highlighted_paragraphs: List[dict]    # [{"text": str, "source": str, "match_percentage": float}]

@app.post("/result")
def store_result(result: AnalysisResult):
    result_id  = f"{result.submission_id}:{result.document_id}"
    result_key = f"results/{result.submission_id}/{result.document_id}.json"

    # Save to Redis with 24h TTL
    r.setex(result_id, 3600 * 24, json.dumps(result.dict()))

    # Also persist to MinIO
    data = json.dumps(result.dict()).encode()
    client.put_object(MINIO_BUCKET, result_key, io.BytesIO(data), length=len(data), content_type="application/json")
    return {"result_id": result_id, "result_key": result_key}


@app.get("/result/{submission_id}/{document_id}")
def get_result(submission_id: int, document_id: int):
    result_id  = f"{submission_id}:{document_id}"
    result_key = f"results/{submission_id}/{document_id}.json"

    # Check Redis first
    cached = r.get(result_id)
    if cached:
        return json.loads(cached)

    # Fallback: read from MinIO
    try:
        response = client.get_object(MINIO_BUCKET, result_key)
        data = json.loads(response.read())
        r.setex(result_id, 3600 * 24, json.dumps(data))  # re-cache
        return data
    except S3Error:
        raise HTTPException(status_code=404, detail=f"Result not ready yet for submission {submission_id}, document {document_id}")