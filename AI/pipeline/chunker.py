<<<<<<< HEAD
import nltk
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
from nltk.tokenize import sent_tokenize

WINDOW_SIZE = 6
STRIDE = 2

def split_sentences(text):
    """
    Splits text into sentences and strips whitespace
    """
    return [s.strip() for s in sent_tokenize(text) if s.strip()]

def sliding_window(sentences, win=WINDOW_SIZE, stride=STRIDE):
    """
    Creates overlapping chunks from a list of sentences
    """
    if len(sentences) <= win:
        return [" ".join(sentences)]
    
    return [
        (" ".join(sentences[i:i+win]))
        for i in range(0, len(sentences) - win + 1, stride)
    ]

def chunk_document(doc_id, text):
    """
    Returns list of (doc_id, chunk_text) tuples for a single document
    """
    sentences = split_sentences(text)
    windows = sliding_window(sentences)
    return [(doc_id, chunk_text) for chunk_text in windows]
=======
from transformers import AutoTokenizer
from pipeline.cleaner import clean_text


MODEL_NAME  = "BAAI/bge-m3"
WINDOW_SIZE = 4096   # tokens per chunk
STRIDE      = 3687   # ~10% overlap

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def chunk_document(doc_id: str, text: str) -> list[tuple[str, str]]:
    """
    Calls cleaner to apply cleaning transformations on the text.
    Splits a document into overlapping token-based chunks.
    Window=4096 tokens, stride=3687 tokens (~10% overlap).
    Returns list of (doc_id, chunk_text) tuples.
    """
    text = clean_text(text)
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
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
