"""
Hypothetical Document Embeddings (HyDE) Service for PolicyPilot.
Implements the HyDE query expansion technique:
1. Generates hypothetical formal policy text using LLM.
2. Embeds the hypothetical text.
3. Performs vector retrieval against official policy chunks.
4. STRICT MANDATE: The hypothetical passage is strictly used for retrieval,
   never as factual evidence.
"""
import time
import logging
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from app.services.llm import generate_hyde_passage
from app.services.embeddings import generate_embedding, cosine_similarity
from app.models.policy import DocumentChunk, Policy

logger = logging.getLogger(__name__)

def execute_hyde_search(
    query: str,
    db: Session,
    top_k: int = 5,
    hypothetical_passage: str = None
) -> Dict[str, Any]:
    """
    Executes HyDE search:
    Returns:
    - original_query
    - hyde_passage
    - retrieved_chunks (list of dicts with real chunk content & scores)
    - latency_ms (total end-to-end)
    - retrieval_latency_ms (vector similarity & ranking time)
    - generation_latency_ms (LLM hypothetical passage synthesis time)
    """
    start_time = time.time()
    generation_ms = 0.0

    # Step 1: Synthesize hypothetical formal policy text (if not precomputed)
    if not hypothetical_passage:
        t_gen_start = time.time()
        hypothetical_passage = generate_hyde_passage(query)
        generation_ms = (time.time() - t_gen_start) * 1000.0

    # Step 2: Generate embedding of the hypothetical passage
    t_ret_start = time.time()
    hypo_embedding = generate_embedding(hypothetical_passage)

    # Step 3: Fetch all document chunks and compute similarity
    chunks = db.query(DocumentChunk).join(Policy).all()

    scored_chunks: List[Tuple[float, DocumentChunk]] = []
    for chunk in chunks:
        chunk_vec = chunk.embedding
        if chunk_vec:
            sim = cosine_similarity(hypo_embedding, chunk_vec)
            scored_chunks.append((sim, chunk))

    # Sort descending by similarity
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_results = scored_chunks[:top_k]

    retrieval_ms = (time.time() - t_ret_start) * 1000.0
    total_ms = (time.time() - start_time) * 1000.0

    retrieved_data = []
    for score, chunk in top_results:
        retrieved_data.append({
            "chunk_id": chunk.id,
            "policy_id": chunk.policy_id,
            "document_name": chunk.policy.document_name if chunk.policy else "Unknown",
            "page_number": chunk.page_number,
            "section_heading": chunk.section_heading,
            "text": chunk.chunk_text,
            "score": round(score, 4),
            "retrieval_method": "hyde_semantic"
        })

    return {
        "original_query": query,
        "hyde_passage": hypothetical_passage,
        "retrieved_chunks": retrieved_data,
        "latency_ms": round(total_ms, 2),
        "retrieval_latency_ms": round(retrieval_ms, 2),
        "generation_latency_ms": round(generation_ms, 2)
    }

