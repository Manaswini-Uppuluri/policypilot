"""
Search & Retrieval Service for PolicyPilot.
Implements:
1. Semantic search (vector similarity)
2. Keyword search (PostgreSQL Full-Text Search / Lexical match)
3. Reciprocal Rank Fusion (RRF) for Hybrid retrieval
4. HyDE hybrid combinations
"""
import time
import math
import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.models.policy import DocumentChunk, Policy
from app.services.embeddings import generate_embedding, cosine_similarity
from app.services.hyde import execute_hyde_search

def semantic_search(query: str, db: Session, top_k: int = 5) -> List[Dict[str, Any]]:
    """Direct query embedding semantic search."""
    q_vec = generate_embedding(query)
    chunks = db.query(DocumentChunk).join(Policy).all()

    scored = []
    for chunk in chunks:
        c_vec = chunk.embedding
        if c_vec:
            sim = cosine_similarity(q_vec, c_vec)
            scored.append((sim, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, chunk in scored[:top_k]:
        results.append({
            "chunk_id": chunk.id,
            "policy_id": chunk.policy_id,
            "document_name": chunk.policy.document_name if chunk.policy else "Unknown",
            "page_number": chunk.page_number,
            "section_heading": chunk.section_heading,
            "text": chunk.chunk_text,
            "score": round(score, 4),
            "retrieval_method": "semantic"
        })
    return results

STOPWORDS = {
    "the", "and", "a", "an", "in", "on", "of", "for", "to", "with", "is", "are", 
    "from", "by", "that", "this", "can", "how", "what", "many", "does", "do", "it", 
    "as", "at", "be", "or", "have", "has", "had", "my", "your", "we", "they",
    "if", "someone", "another", "happens", "happen", "under", "per"
}

def stem_token(word: str) -> str:
    """Stem token for robust query-to-chunk keyword matching."""
    word = word.lower().strip()
    if len(word) <= 3:
        return word
    for suffix in ["ing", "tion", "tions", "ies", "es", "ed", "s", "ment"]:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            word = word[:-len(suffix)]
            break
    if word.endswith("e") and len(word) > 3:
        word = word[:-1]
    return word

def keyword_search(query: str, db: Session, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Keyword search:
    Uses stemmed token frequency, substring matching, and phrase bonuses to match informal queries.
    """
    chunks = db.query(DocumentChunk).join(Policy).all()
    all_tokens = re.findall(r"\w+", query.lower())
    query_tokens = [t for t in all_tokens if t not in STOPWORDS and len(t) > 2]
    if not query_tokens:
        query_tokens = [t for t in all_tokens if len(t) > 2]
    if not query_tokens:
        return []

    query_stems = set(stem_token(t) for t in query_tokens)

    scored = []
    for chunk in chunks:
        text_lower = chunk.chunk_text.lower()
        chunk_words = re.findall(r"\w+", text_lower)
        if not chunk_words:
            continue

        chunk_word_set = set(chunk_words)
        chunk_stems = set(stem_token(w) for w in chunk_words)

        exact_matches = sum(1 for t in query_tokens if t in chunk_word_set)
        stem_matches = sum(1 for s in query_stems if s in chunk_stems)
        substring_matches = sum(1 for s in query_stems if any(s in w for w in chunk_words))

        phrase_bonus = 3.0 if query.lower() in text_lower else 0.0
        
        score = (exact_matches * 1.5 + stem_matches * 1.0 + substring_matches * 0.5) / (len(query_tokens) * 2.5) + phrase_bonus
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, chunk in scored[:top_k]:
        results.append({
            "chunk_id": chunk.id,
            "policy_id": chunk.policy_id,
            "document_name": chunk.policy.document_name if chunk.policy else "Unknown",
            "page_number": chunk.page_number,
            "section_heading": chunk.section_heading,
            "text": chunk.chunk_text,
            "score": round(score, 4),
            "retrieval_method": "keyword"
        })
    return results

def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    k: int = 60,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Combines multiple ranked lists using Reciprocal Rank Fusion (RRF):
    RRF_score(chunk) = SUM( 1.0 / (k + rank_i) )
    """
    rrf_scores = defaultdict(float)
    chunk_map = {}

    for r_list in ranked_lists:
        for rank, item in enumerate(r_list, start=1):
            cid = item["chunk_id"]
            rrf_scores[cid] += 1.0 / (k + rank)
            if cid not in chunk_map:
                chunk_map[cid] = item.copy()

    # Sort descending by fused RRF score
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    final_results = []
    for cid, score in sorted_items[:top_k]:
        item = chunk_map[cid]
        item["score"] = round(score, 5)
        item["retrieval_method"] = "hybrid_rrf"
        final_results.append(item)

    return final_results

def hybrid_search(query: str, db: Session, use_hyde: bool = True, top_k: int = 5, hyde_passage: str = None) -> Dict[str, Any]:
    """
    Executes hybrid retrieval:
    1. If use_hyde: Run HyDE semantic search (reusing hypothetical passage if provided), otherwise standard semantic search.
    2. Run keyword search.
    3. Fuse lists using RRF.
    """
    start_time = time.time()
    generation_ms = 0.0

    if use_hyde:
        hyde_res = execute_hyde_search(query, db, top_k=top_k * 2, hypothetical_passage=hyde_passage)
        semantic_list = hyde_res["retrieved_chunks"]
        hyde_passage = hyde_res["hyde_passage"]
        generation_ms = hyde_res.get("generation_latency_ms", 0.0)
    else:
        semantic_list = semantic_search(query, db, top_k=top_k * 2)

    keyword_list = keyword_search(query, db, top_k=top_k * 2)

    fused_results = reciprocal_rank_fusion([semantic_list, keyword_list], k=settings.RRF_K, top_k=top_k)
    total_latency_ms = (time.time() - start_time) * 1000.0
    retrieval_latency_ms = max(0.0, total_latency_ms - generation_ms)

    return {
        "query": query,
        "mode": "hybrid_hyde" if use_hyde else "hybrid",
        "results": fused_results,
        "hyde_passage": hyde_passage,
        "latency_ms": round(total_latency_ms, 2),
        "retrieval_latency_ms": round(retrieval_latency_ms, 2),
        "generation_latency_ms": round(generation_ms, 2)
    }

def unified_retrieval(query: str, mode: str, db: Session, top_k: int = 5, hyde_passage: str = None) -> Dict[str, Any]:
    """
    Unified entry point supporting:
    - 'semantic'
    - 'semantic_hyde'
    - 'keyword'
    - 'hybrid'
    - 'hybrid_hyde'
    """
    start = time.time()
    if mode == "semantic":
        res = semantic_search(query, db, top_k=top_k)
        ret_ms = round((time.time() - start) * 1000, 2)
        return {
            "query": query, "mode": mode, "results": res, "hyde_passage": None,
            "latency_ms": ret_ms, "retrieval_latency_ms": ret_ms, "generation_latency_ms": 0.0
        }
    elif mode == "semantic_hyde":
        hyde_res = execute_hyde_search(query, db, top_k=top_k, hypothetical_passage=hyde_passage)
        return {
            "query": query, "mode": mode, "results": hyde_res["retrieved_chunks"],
            "hyde_passage": hyde_res["hyde_passage"], "latency_ms": hyde_res["latency_ms"],
            "retrieval_latency_ms": hyde_res.get("retrieval_latency_ms", hyde_res["latency_ms"]),
            "generation_latency_ms": hyde_res.get("generation_latency_ms", 0.0)
        }
    elif mode == "keyword":
        res = keyword_search(query, db, top_k=top_k)
        ret_ms = round((time.time() - start) * 1000, 2)
        return {
            "query": query, "mode": mode, "results": res, "hyde_passage": None,
            "latency_ms": ret_ms, "retrieval_latency_ms": ret_ms, "generation_latency_ms": 0.0
        }
    elif mode == "hybrid":
        return hybrid_search(query, db, use_hyde=False, top_k=top_k)
    else: # hybrid_hyde
        return hybrid_search(query, db, use_hyde=True, top_k=top_k, hyde_passage=hyde_passage)

