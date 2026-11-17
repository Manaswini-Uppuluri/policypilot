"""
MCP Policy Tools Implementation.
Exposes core university policy queries using the database session.
"""
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure backend app is on sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.database import get_session, get_engine
from app.models.policy import Policy, DocumentChunk
from app.services.search import unified_retrieval
from app.services.guardrails import evaluate_guardrails

def tool_search_policy(query: str, top_k: int = 4) -> Dict[str, Any]:
    """
    Search official university policies using hybrid semantic + keyword retrieval.
    """
    db = get_session()
    try:
        res = unified_retrieval(query=query, mode="hybrid_hyde", db=db, top_k=top_k)
        chunks = res["results"]
        return {
            "query": query,
            "retrieval_mode": "hybrid_hyde",
            "chunks_found": len(chunks),
            "results": [
                {
                    "document_name": c["document_name"],
                    "page_number": c["page_number"],
                    "section_heading": c.get("section_heading", "General"),
                    "text": c["text"],
                    "relevance_score": c["score"]
                }
                for c in chunks
            ]
        }
    finally:
        db.close()

def tool_get_policy_section(document_name: str, page_number: int) -> Dict[str, Any]:
    """
    Retrieve exact policy content for a specific document and page number.
    """
    db = get_session()
    try:
        policy = db.query(Policy).filter(Policy.document_name.ilike(f"%{document_name}%")).first()
        if not policy:
            return {"error": f"Policy matching '{document_name}' was not found."}

        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.policy_id == policy.id,
            DocumentChunk.page_number == page_number
        ).order_by(DocumentChunk.chunk_index.asc()).all()

        if not chunks:
            return {"error": f"Page {page_number} not found in policy '{policy.document_name}'."}

        combined_text = "\n\n".join([c.chunk_text for c in chunks])
        return {
            "document_name": policy.document_name,
            "version": policy.version,
            "category": policy.category,
            "page_number": page_number,
            "content": combined_text
        }
    finally:
        db.close()

def tool_list_available_policies() -> Dict[str, Any]:
    """
    List all indexed university policies with category, version, and page count.
    """
    db = get_session()
    try:
        policies = db.query(Policy).all()
        return {
            "total_policies": len(policies),
            "policies": [
                {
                    "id": p.id,
                    "document_name": p.document_name,
                    "category": p.category,
                    "version": p.version,
                    "effective_date": p.effective_date,
                    "total_pages": p.total_pages,
                    "total_chunks": p.total_chunks
                }
                for p in policies
            ]
        }
    finally:
        db.close()

def tool_check_policy_evidence(claim: str) -> Dict[str, Any]:
    """
    Evaluate whether a policy-related claim has sufficient supporting evidence.
    Returns status: VERIFIED, CONFLICTING, or UNVERIFIED.
    """
    db = get_session()
    try:
        res = unified_retrieval(query=claim, mode="hybrid_hyde", db=db, top_k=4)
        chunks = res["results"]
        status, conflicts, confidence = evaluate_guardrails(claim, chunks)

        return {
            "claim": claim,
            "verification_status": status,
            "confidence_score": confidence,
            "conflict_notes": conflicts,
            "supporting_evidence_count": len(chunks),
            "top_supporting_excerpt": chunks[0]["text"] if chunks else None
        }
    finally:
        db.close()
