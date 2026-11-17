"""
Pydantic Schemas for Request & Response Validation in PolicyPilot.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

# Chat Schemas
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Student's query or question")
    conversation_id: Optional[str] = Field(default=None, description="Session ID for chat continuity")
    search_mode: Literal["semantic", "semantic_hyde", "keyword", "hybrid", "hybrid_hyde"] = Field(
        default="hybrid_hyde",
        description="Retrieval strategy to employ"
    )
    top_k: int = Field(default=4, ge=1, le=10, description="Number of evidence chunks to retrieve")

class Citation(BaseModel):
    document_name: str
    page_number: int
    section_heading: Optional[str] = None
    quote: str
    score: float

class EvidenceChunk(BaseModel):
    chunk_id: str
    document_name: str
    page_number: int
    section_heading: Optional[str] = None
    text: str
    score: float
    retrieval_method: str

class EvidenceTrace(BaseModel):
    original_query: str
    interpreted_intent: str
    hyde_passage: Optional[str] = None
    retrieval_mode: str
    retrieval_latency_ms: float
    retrieved_chunks: List[EvidenceChunk]
    verification_status: Literal["VERIFIED", "CONFLICTING", "UNVERIFIED", "OUT_OF_SCOPE"]
    conflict_notes: Optional[str] = None
    confidence_score: float

class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    verification_status: Literal["VERIFIED", "CONFLICTING", "UNVERIFIED", "OUT_OF_SCOPE"]
    citations: List[Citation]
    evidence_trace: Optional[EvidenceTrace] = None

# Document Schemas
class DocumentResponse(BaseModel):
    id: str
    document_name: str
    category: str
    version: str
    upload_date: Optional[str] = None
    effective_date: Optional[str] = None
    total_pages: int
    total_chunks: int

class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse

# Search Schemas
class SearchRequest(BaseModel):
    query: str
    mode: Literal["semantic", "semantic_hyde", "keyword", "hybrid", "hybrid_hyde"] = "hybrid_hyde"
    top_k: int = 5

class SearchResponse(BaseModel):
    query: str
    mode: str
    results: List[Dict[str, Any]]
    hyde_passage: Optional[str] = None
    latency_ms: float

# Evaluation Schemas
class MetricScore(BaseModel):
    recall_at_3: float
    recall_at_5: float
    mrr: float
    avg_latency_ms: float
    avg_retrieval_latency_ms: Optional[float] = None
    avg_generation_latency_ms: Optional[float] = None

class EvaluationResult(BaseModel):
    modes: Dict[str, MetricScore]
    test_queries_evaluated: int
    summary: str
    detailed_results: List[Dict[str, Any]]

