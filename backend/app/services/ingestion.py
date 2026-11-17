"""
Document Ingestion Service for PolicyPilot.
Extracts text from PDF via PyMuPDF (fitz), detects section headings,
chunks text with overlap, generates embeddings, and saves to database.
"""
import os
import hashlib
import re
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
import fitz  # PyMuPDF

from app.core.config import settings
from app.models.policy import Policy, DocumentChunk
from app.services.embeddings import generate_embeddings_batch

logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file for deduplication."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

def extract_text_by_page(file_path: str) -> List[Tuple[int, str]]:
    """
    Extract text per page from PDF using PyMuPDF.
    Returns list of (page_number, page_text).
    """
    pages_data = []
    try:
        doc = fitz.open(file_path)
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            text = page.get_text("text") or ""
            pages_data.append((page_idx + 1, text.strip()))
        doc.close()
    except Exception as e:
        logger.error(f"Failed to read PDF with PyMuPDF: {e}")
        raise ValueError(f"Invalid or corrupted PDF file: {e}")
    return pages_data

def detect_section_heading(text: str) -> str:
    """
    Detect probable section heading from chunk text (e.g., 'SECTION 4', 'Article 2', '4. Attendance Rules').
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return "General"
    first_line = lines[0]
    heading_patterns = [
        r"^(SECTION|ARTICLE|CHAPTER|PART|POLICY|RULE)\s+[0-9IVX]+",
        r"^[0-9]+(\.[0-9]+)*\s+[A-Z]",
        r"^[A-Z\s]{4,40}$"
    ]
    for pattern in heading_patterns:
        if re.search(pattern, first_line, re.IGNORECASE):
            return first_line[:100]
    return first_line[:50] if len(first_line) < 50 else "Section"

def chunk_page_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """
    Chunk text with sliding window overlap based on character count / sentences.
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break
        
        # Try to break on paragraph or sentence boundary
        break_pt = text.rfind("\n\n", start, end)
        if break_pt == -1 or break_pt <= start + (chunk_size // 2):
            break_pt = text.rfind(". ", start, end)
        if break_pt == -1 or break_pt <= start + (chunk_size // 2):
            break_pt = end
        else:
            break_pt += 1  # include period or newline

        chunk = text[start:break_pt].strip()
        if chunk:
            chunks.append(chunk)
        start = max(start + 1, break_pt - overlap)

    return chunks

def ingest_pdf_file(
    file_path: str,
    original_filename: str,
    category: str = "General",
    version: str = "1.0",
    effective_date: str = "2026-2027",
    db: Session = None
) -> Policy:
    """
    Complete ingestion pipeline:
    1. Check SHA256 to avoid duplicate ingestion.
    2. Extract text per page via PyMuPDF.
    3. Split into overlapping chunks.
    4. Generate embeddings.
    5. Save Policy and DocumentChunks to DB.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_hash = calculate_sha256(file_path)

    # Check for duplicate
    existing = db.query(Policy).filter(Policy.file_hash == file_hash).first()
    if existing:
        logger.info(f"Policy '{existing.document_name}' already ingested (hash: {file_hash[:8]}).")
        return existing

    # Extract text by page
    pages_data = extract_text_by_page(file_path)
    if not pages_data:
        raise ValueError("PDF contains no readable text or is empty.")

    # Create policy record
    policy = Policy(
        document_name=original_filename,
        category=category,
        version=version,
        effective_date=effective_date,
        file_path=file_path,
        file_hash=file_hash,
        total_pages=len(pages_data),
        total_chunks=0
    )
    db.add(policy)
    db.flush()  # get policy.id

    # Create chunks
    all_chunks_text = []
    chunk_metadata = []
    chunk_counter = 0

    for page_num, page_text in pages_data:
        if not page_text.strip():
            continue
        page_chunks = chunk_page_text(page_text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        for chunk_txt in page_chunks:
            section_head = detect_section_heading(chunk_txt)
            all_chunks_text.append(chunk_txt)
            chunk_metadata.append({
                "policy_id": policy.id,
                "page_number": page_num,
                "section_heading": section_head,
                "chunk_index": chunk_counter
            })
            chunk_counter += 1

    if not all_chunks_text:
        raise ValueError("Could not extract any textual chunks from the document.")

    # Generate embeddings in batch
    embeddings = generate_embeddings_batch(all_chunks_text)

    # Save DocumentChunk entities
    for i, meta in enumerate(chunk_metadata):
        chunk_obj = DocumentChunk(
            policy_id=policy.id,
            chunk_text=all_chunks_text[i],
            page_number=meta["page_number"],
            section_heading=meta["section_heading"],
            chunk_index=meta["chunk_index"]
        )
        chunk_obj.embedding = embeddings[i]
        db.add(chunk_obj)

    policy.total_chunks = len(all_chunks_text)
    db.commit()
    db.refresh(policy)
    logger.info(f"Ingested policy '{policy.document_name}' with {policy.total_chunks} chunks.")
    return policy

