from transformers import AutoTokenizer

MODEL_NAME  = "BAAI/bge-m3"
WINDOW_SIZE = 4096   # tokens per chunk
STRIDE      = 3687   # ~10% overlap

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def chunk_document(doc_id: str, text: str) -> list[tuple[str, str]]:
    """
    Splits a document into overlapping token-based chunks.
    Window=4096 tokens, stride=3687 tokens (~10% overlap).
    Returns list of (doc_id, chunk_text) tuples.
    """
    token_ids = tokenizer.encode(text, add_special_tokens=False)

    if len(token_ids) <= WINDOW_SIZE:
        return [(doc_id, text)]

    chunks = []
    for i in range(0, len(token_ids) - WINDOW_SIZE + 1, STRIDE):
        chunk_text = tokenizer.decode(token_ids[i : i + WINDOW_SIZE], skip_special_tokens=True)
        if chunk_text.strip():
            chunks.append((doc_id, chunk_text))

    # ensure the tail of the document is always included
    last_chunk_text = tokenizer.decode(token_ids[-WINDOW_SIZE:], skip_special_tokens=True)
    if last_chunk_text.strip() and (not chunks or last_chunk_text != chunks[-1][1]):
        chunks.append((doc_id, last_chunk_text))

    return chunks