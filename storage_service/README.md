# GPD Storage Microservice

This service now lives at the repository root, separate from `GPD_back/`.

## Setup
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## MinIO Setup
1. Download MinIO from https://min.io/download
2. Run:
```bash
minio server ./storage --console-address :9001
```
3. Open http://localhost:9001 (admin / password123)
4. Create bucket: veritas

## API Docs
Open http://localhost:8002/docs for interactive API documentation

## Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| POST | /upload/source?workspace_id=1 | Upload source file |
| POST | /upload/document?workspace_id=1 | Upload document file |
| GET | /file/{file_key} | Get presigned download URL |
| DELETE | /file/{file_key} | Delete a file |
| POST | /result | AI model stores result |
| GET | /result/{submission_id}/{document_id} | Get result |
