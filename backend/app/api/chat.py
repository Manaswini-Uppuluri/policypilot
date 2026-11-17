"""
Chat & Policy Discovery Endpoints for PolicyPilot.
Implements the core RAG workflow:
Sanitize Query -> Intent / Scenario Decomposition -> Retrieval -> Guardrails -> Grounded Answer -> Citations & Evidence Trace.
"""
import uuid
import time
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.policy import ChatHistory
from app.models.schemas import ChatRequest, ChatResponse, Citation, EvidenceTrace, EvidenceChunk
from app.services.guardrails import sanitize_user_query, evaluate_guardrails, extract_valid_citations
from app.services.search import unified_retrieval
from app.services.llm import generate_grounded_answer
from app.services.evaluation import decompose_scenario
from app.services.scope import classify_query_scope

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def policy_chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Primary RAG endpoint:
    Processes student query, performs verified retrieval, enforces guardrails,
    and returns answer with citations and expandable evidence trace.
    """
    clean_query, injection_detected = sanitize_user_query(req.query)
    if not clean_query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty.")

    conv_id = req.conversation_id or str(uuid.uuid4())
    start_time = time.time()

    # Fetch recent conversation history for context resolution if session ID provided
    recent_history = []
    if req.conversation_id:
        try:
            recent_history = db.query(ChatHistory).filter(
                ChatHistory.conversation_id == req.conversation_id
            ).order_by(ChatHistory.timestamp.desc()).limit(10).all()
            recent_history.reverse()
        except Exception as e:
            logger.warning(f"Failed to query conversation history: {e}")

    # Step 0: Scope & Domain Classification
    scope_status, scope_msg, resolved_query = classify_query_scope(clean_query, recent_history)

    # Handle Out-of-Domain queries immediately without running RAG, HyDE or Groq
    if scope_status == "OUT_OF_SCOPE":
        try:
            history_entry = ChatHistory(
                conversation_id=conv_id,
                user_query=req.query,
                interpreted_intent=clean_query,
                assistant_response=scope_msg,
                verification_status="OUT_OF_SCOPE",
                retrieved_evidence=[]
            )
            db.add(history_entry)
            db.commit()
        except Exception as e:
            logger.warning(f"Could not persist chat history: {e}")

        return ChatResponse(
            conversation_id=conv_id,
            answer=scope_msg,
            verification_status="OUT_OF_SCOPE",
            citations=[],
            evidence_trace=None
        )

    # Handle Ambiguous queries requiring clarification
    if scope_status == "NEEDS_CLARIFICATION":
        try:
            history_entry = ChatHistory(
                conversation_id=conv_id,
                user_query=req.query,
                interpreted_intent=clean_query,
                assistant_response=scope_msg,
                verification_status="UNVERIFIED",
                retrieved_evidence=[]
            )
            db.add(history_entry)
            db.commit()
        except Exception as e:
            logger.warning(f"Could not persist chat history: {e}")

        return ChatResponse(
            conversation_id=conv_id,
            answer=scope_msg,
            verification_status="UNVERIFIED",
            citations=[],
            evidence_trace=None
        )

    # Use resolved query for follow-up questions
    effective_query = resolved_query if resolved_query else clean_query

    # Step 1: Scenario Decomposition
    sub_scenarios = decompose_scenario(effective_query)
    interpreted_intent = " & ".join(sub_scenarios) if len(sub_scenarios) > 1 else effective_query

    # Step 2: Retrieval (Only executed for validated in-scope policy questions)
    retrieval_res = unified_retrieval(
        query=effective_query,
        mode=req.search_mode,
        db=db,
        top_k=req.top_k
    )
    raw_chunks = retrieval_res["results"]
    hyde_passage = retrieval_res.get("hyde_passage")
    retrieval_latency = retrieval_res["latency_ms"]

    # Step 3: Guardrails & Anti-Hallucination Evaluation
    verification_status, conflict_notes, confidence_score = evaluate_guardrails(effective_query, raw_chunks)

    # Step 4: Grounded Answer Synthesis
    answer = generate_grounded_answer(
        query=effective_query,
        evidence_chunks=raw_chunks,
        verification_status=verification_status,
        conflicts=conflict_notes
    )

    if injection_detected:
        answer += "\n\n*(Note: System override or prompt injection attempts were detected and neutralized.)*"

    # Step 5: Verified Citations (Only provided when evidence is genuinely verified or conflicting)
    if verification_status == "UNVERIFIED":
        citations = []
    else:
        citations_data = extract_valid_citations(raw_chunks)
        citations = [
            Citation(
                document_name=c["document_name"],
                page_number=c["page_number"],
                section_heading=c.get("section_heading"),
                quote=c["quote"],
                score=c["score"]
            ) for c in citations_data
        ]

    # Step 6: Evidence Trace Construction
    evidence_chunks = [
        EvidenceChunk(
            chunk_id=c["chunk_id"],
            document_name=c["document_name"],
            page_number=c["page_number"],
            section_heading=c.get("section_heading"),
            text=c["text"],
            score=c["score"],
            retrieval_method=c["retrieval_method"]
        ) for c in raw_chunks
    ]

    trace = EvidenceTrace(
        original_query=req.query,
        interpreted_intent=interpreted_intent,
        hyde_passage=hyde_passage,
        retrieval_mode=req.search_mode,
        retrieval_latency_ms=retrieval_latency,
        retrieved_chunks=evidence_chunks,
        verification_status=verification_status,
        conflict_notes="; ".join(conflict_notes) if conflict_notes else None,
        confidence_score=confidence_score
    )

    # Save to Chat History
    try:
        history_entry = ChatHistory(
            conversation_id=conv_id,
            user_query=req.query,
            interpreted_intent=interpreted_intent,
            hyde_passage=hyde_passage,
            assistant_response=answer,
            verification_status=verification_status,
            retrieved_evidence=[c.model_dump() for c in evidence_chunks]
        )
        db.add(history_entry)
        db.commit()
    except Exception as e:
        logger.warning(f"Could not persist chat history: {e}")

    return ChatResponse(
        conversation_id=conv_id,
        answer=answer,
        verification_status=verification_status,
        citations=citations,
        evidence_trace=trace
    )

@router.get("/chat/history/{conversation_id}")
def get_chat_history(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieve chat history for a session."""
    entries = db.query(ChatHistory).filter(
        ChatHistory.conversation_id == conversation_id
    ).order_by(ChatHistory.timestamp.asc()).all()
    return [e.to_dict() for e in entries]
