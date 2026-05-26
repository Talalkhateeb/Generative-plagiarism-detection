from sentence_transformers import SentenceTransformer
import torch

MODEL_NAME = "BAAI/bge-m3"
BATCH_SIZE = 16

# Load once — not per request
_model = None
def get_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = SentenceTransformer(MODEL_NAME, device=device)
    return _model

def encode_chunks(chunks) -> list[tuple[str, str, list[float]]]:
    """
    Takes (doc_id, chunk_text) tuples.
    Returns (doc_id, chunk_text, embedding) tuples.
    BGE-M3 does not use query/passage prefixes — no prefix added.
    """
    model = get_model()

    doc_ids = [doc_id for doc_id, _ in chunks]
    texts = [chunk_text for _, chunk_text in chunks]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=BATCH_SIZE,
        convert_to_numpy=True,
    )

    return [(doc_ids[i], chunks[i][1], embeddings[i].tolist()) for i in range(len(chunks))]