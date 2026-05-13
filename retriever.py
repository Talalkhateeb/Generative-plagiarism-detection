from collections import defaultdict
from pipeline.chunker import chunk_document
from pipeline.encoder import encode_chunks
from qdrant_store import search
from rank_bm25 import BM25Okapi

AGGREGATION_METHODS = ("max", "mean")
ALPHA = 0.57  # weight for dense scores; (1 - ALPHA) for BM25


def aggregate_chunk_scores(
    chunk_results: list[tuple[str, float]],
    method="max"
) -> dict[str, float]:
    """
    Collapses chunk-level (doc_id, score) pairs into one score per document.
    """
    if method not in AGGREGATION_METHODS:
        raise ValueError(f"Unknown aggregation method '{method}'. Choose from: {AGGREGATION_METHODS}")

    scores = defaultdict(list)
    for doc_id, score in chunk_results:
        scores[doc_id].append(score)

    if method == "max":
        return {doc_id: max(s) for doc_id, s in scores.items()}
    elif method == "mean":
        return {doc_id: sum(s) / len(s) for doc_id, s in scores.items()}


def min_max_normalize(doc_scores: dict) -> dict:
    if not doc_scores:
        return doc_scores
    lo, hi = min(doc_scores.values()), max(doc_scores.values())
    if hi == lo:
        return {k: 1.0 for k in doc_scores}
    return {k: (v - lo) / (hi - lo) for k, v in doc_scores.items()}


def run_bm25(source_texts: dict[str, str], query_text: str) -> dict[str, float]:
    """
    Builds a BM25 index from source_texts and scores the query.
    Returns dict: doc_id -> raw BM25 score.
    """
    doc_ids = list(source_texts.keys())
    tokenized_corpus = [text.lower().split() for text in source_texts.values()]
    tokenized_query = query_text.lower().split()

    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(tokenized_query)

    return {doc_id: float(score) for doc_id, score in zip(doc_ids, scores)}


def fuse(
    dense_scores: dict[str, float],
    bm25_scores: dict[str, float],
    alpha: float = ALPHA,
) -> dict[str, float]:
    """
    Weighted sum fusion:
        final_score = alpha * dense_norm + (1 - alpha) * bm25_norm
    """
    dense_norm = min_max_normalize(dense_scores)
    bm25_norm  = min_max_normalize(bm25_scores)
    all_docs   = set(dense_norm.keys()) | set(bm25_norm.keys())

    return {
        doc_id: alpha * dense_norm.get(doc_id, 0.0) + (1 - alpha) * bm25_norm.get(doc_id, 0.0)
        for doc_id in all_docs
    }


def retrieve(
    workspace_id,
    query_text,
    top_k: int | None = None,
    aggregation="mean",
    chunk_pool=100,
    source_texts: dict[str, str] | None = None,
) -> list[tuple[str, float]]:
    """
    Full retrieval pipeline: chunk query → encode → search → aggregate → (optionally fuse with BM25) → rank.

    Args:
        workspace_id:  Qdrant collection to search in
        query_text:    raw query text (will be chunked and encoded internally)
        top_k:         how many documents to return (None = return all)
        aggregation:   score aggregation method — "max" or "mean"
        chunk_pool:    how many chunks to fetch per query chunk before aggregating
        source_texts:  optional dict {doc_id: text} — if provided, BM25 is run and fused with dense

    Returns:
        list of (doc_id, score) sorted by score descending
    """
    # Step 1: chunk the query
    query_chunks = chunk_document(doc_id="query", text=query_text)

    # Step 2: encode all query chunks in one batch
    encoded_query_chunks = encode_chunks(query_chunks)

    # Step 3: for each query chunk, search Qdrant and pool all results
    all_chunk_results = []
    for _, _, query_embedding in encoded_query_chunks:
        results = search(workspace_id, query_embedding, top_k=chunk_pool)
        all_chunk_results.extend(results)

    # Step 4: collapse to one score per document
    doc_scores = aggregate_chunk_scores(all_chunk_results, method=aggregation)

    # Step 5: optionally fuse with BM25
    if source_texts:
        bm25_scores = run_bm25(source_texts, query_text)
        doc_scores = fuse(doc_scores, bm25_scores)

    # Step 6: sort documents by score descending
    ranked = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

    # Step 7: optionally truncate
    if top_k is not None:
        ranked = ranked[:top_k]

    return ranked