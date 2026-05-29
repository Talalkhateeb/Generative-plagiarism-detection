from sentence_transformers import CrossEncoder
from transformers import AutoTokenizer
from pipeline.cleaner import clean_text
import torch

RERANKER_NAME     = "BAAI/bge-reranker-v2-m3"
QUERY_CHUNK_SIZE  = 512   # tokens per query chunk for reranking
SOURCE_TRUNC      = 1000  # tokens to take from source doc for reranking
RERANK_TOP_K      = 150   # how many fused candidates to rerank
RERANK_BATCH_SIZE = 32    # cross-encoder batch size
BETA              = 0.7   # weight for reranker score; (1 - BETA) for fusion score

reranker_tokenizer = AutoTokenizer.from_pretrained(RERANKER_NAME)

# Load once — not per request
_cross_encoder = None

def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _cross_encoder = CrossEncoder(RERANKER_NAME, device=device, max_length=1600)
    return _cross_encoder


def chunk_query_for_reranking(query_text: str) -> list[str]:
    """
    Splits a query document into 512-token chunks using the reranker tokenizer.
    These shorter chunks are in-distribution for the cross-encoder.
    """
    token_ids = reranker_tokenizer.encode(query_text, add_special_tokens=False)
    chunks = []
    for i in range(0, len(token_ids), QUERY_CHUNK_SIZE):
        chunk_ids  = token_ids[i : i + QUERY_CHUNK_SIZE]
        chunk_text = reranker_tokenizer.decode(chunk_ids, skip_special_tokens=True)
        if chunk_text.strip():
            chunks.append(chunk_text)
    return chunks


def truncate_source_for_reranking(source_text: str) -> str:
    """
    Takes the first SOURCE_TRUNC tokens of a source document.
    For academic papers this reliably covers the abstract + start of introduction.
    """
    token_ids = reranker_tokenizer.encode(source_text, add_special_tokens=False)
    truncated = token_ids[:SOURCE_TRUNC]
    return reranker_tokenizer.decode(truncated, skip_special_tokens=True)


def min_max_normalize(scores: dict) -> dict:
    if not scores:
        return scores
    lo, hi = min(scores.values()), max(scores.values())
    if hi == lo:
        return {k: 1.0 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def rerank(
    fused_results: list[tuple[str, float]],
    query_text: str,
    source_texts: dict[str, str],
    top_k: int = RERANK_TOP_K,
    batch_size: int = RERANK_BATCH_SIZE,
    beta: float = BETA,
) -> list[tuple[str, float]]:
    """
    Reranks the top RERANK_TOP_K fused candidates, then blends the reranker
    score with the original fusion score using beta blending.

    Query side  : split into 512-token chunks (reranker tokenizer).
    Source side : first 1000 tokens only (covers abstract + intro start).

    Scoring:
        reranker score = max cross-encoder score across all query chunks
        fusion score   = original hybrid retrieval score (pre-reranking)
        final score    = beta * norm(reranker) + (1 - beta) * norm(fusion)

    Both scores are min-max normalized within the top-k window before blending.
    Tail (ranks top_k+1 onward) is kept in fusion order unchanged.

    Args:
        fused_results:  sorted list of (doc_id, fusion_score) from retriever
        query_text:     full cleaned query document text
        source_texts:   dict {doc_id: raw source text} for all candidates
        top_k:          how many top candidates to rerank
        batch_size:     cross-encoder inference batch size
        beta:           blend weight for reranker score

    Returns:
        list of (doc_id, final_score) sorted descending, tail appended unchanged
    """
    if not fused_results:
        return []

    query_text = clean_text(query_text)

    to_rerank = fused_results[:top_k]
    tail      = fused_results[top_k:]

    # split query into 512-token chunks for cross-encoder
    query_chunks = chunk_query_for_reranking(query_text)
    if not query_chunks:
        return fused_results

    cross_encoder = get_cross_encoder()

    # build all (query_chunk, truncated_source) pairs
    all_pairs  = []
    pair_index = []  # tracks (chunk_idx, doc_idx) for each pair
    for c_idx, q_chunk in enumerate(query_chunks):
        for d_idx, (doc_id, _) in enumerate(to_rerank):
            src_text = truncate_source_for_reranking(
                clean_text(source_texts.get(doc_id, ""))
            )
            all_pairs.append((q_chunk, src_text))
            pair_index.append((c_idx, d_idx))

    # run cross-encoder in batches
    all_scores = []
    for i in range(0, len(all_pairs), batch_size):
        batch_scores = cross_encoder.predict(
            all_pairs[i : i + batch_size],
            show_progress_bar=False,
        )
        all_scores.extend(
            batch_scores.tolist() if hasattr(batch_scores, "tolist") else batch_scores
        )

    # aggregate: max reranker score over query chunks per source document
    n_docs  = len(to_rerank)
    doc_max = [-float("inf")] * n_docs
    for score, (c_idx, d_idx) in zip(all_scores, pair_index):
        if score > doc_max[d_idx]:
            doc_max[d_idx] = score

    # beta blending — both normalized within the top-k window
    raw_reranker    = {doc_id: doc_max[d_idx] for d_idx, (doc_id, _) in enumerate(to_rerank)}
    original_scores = {doc_id: score          for doc_id, score      in to_rerank}

    reranker_norm = min_max_normalize(raw_reranker)
    original_norm = min_max_normalize(original_scores)

    blended = {
        doc_id: beta * reranker_norm[doc_id] + (1 - beta) * original_norm[doc_id]
        for doc_id in reranker_norm
    }

    reranked_top = sorted(blended.items(), key=lambda x: x[1], reverse=True)
    return reranked_top + tail
