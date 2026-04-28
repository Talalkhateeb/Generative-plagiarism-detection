# Guide for AI Model Partner
## What you receive from Django (JSON)

```json
{
  "submission_id": 5,
  "document_id": 1,
  "document_name": "thesis.pdf",
  "document_url": "http://127.0.0.1:9000/veritas/documents/1/uuid.pdf?token=...",
  "sources": [
    {
      "source_id": 1,
      "source_name": "paper1.pdf",
      "source_url": "http://127.0.0.1:9000/veritas/sources/1/uuid.pdf?token=..."
    }
  ],
  "result_callback_url": "http://127.0.0.1:8002/result"
}
```

## What you do
1. Download files from the URLs (they expire in 2 hours)
2. Run your plagiarism analysis
3. POST result to result_callback_url

## What you POST back (to result_callback_url)

```json
{
  "submission_id": 5,
  "document_id": 1,
  "plagiarism_score": 23.5,
  "original_percentage": 76.5,
  "matched_sources": [
    {"source_name": "paper1.pdf", "match_percentage": 15.0},
    {"source_name": "paper2.pdf", "match_percentage": 8.5}
  ],
  "highlighted_paragraphs": [
    {
      "text": "The fundamental principles of quantum mechanics...",
      "source": "paper1.pdf",
      "match_percentage": 15.0
    }
  ]
}
```

## FastAPI endpoint template

```python
from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

class AnalyzeRequest(BaseModel):
    submission_id: int
    document_id: int
    document_name: str
    document_url: str
    sources: list
    result_callback_url: str

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    # 1. Download document
    doc_bytes = requests.get(req.document_url).content
    
    # 2. Download sources
    sources = []
    for src in req.sources:
        src_bytes = requests.get(src["source_url"]).content
        sources.append({"name": src["source_name"], "bytes": src_bytes})
    
    # 3. YOUR AI MODEL HERE
    result = your_model.analyze(doc_bytes, sources)
    
    # 4. POST result back to storage service
    requests.post(req.result_callback_url, json={
        "submission_id": req.submission_id,
        "document_id": req.document_id,
        "plagiarism_score": result["score"],
        "original_percentage": 100 - result["score"],
        "matched_sources": result["matched_sources"],
        "highlighted_paragraphs": result["paragraphs"],
    })
    
    return {"status": "processing"}
```
