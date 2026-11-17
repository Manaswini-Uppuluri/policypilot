"""
Database Models for PolicyPilot.
Defines schema for Policies, Document Chunks (with embeddings and FTS),
and Chat History.
"""
import uuid
from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), default="General", index=True)
    version = Column(String(50), default="1.0")
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    effective_date = Column(String(100), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), unique=True, index=True, nullable=False)
    total_pages = Column(Integer, default=1)
    total_chunks = Column(Integer, default=0)

    # Relationship to chunks
    chunks = relationship("DocumentChunk", back_populates="policy", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "document_name": self.document_name,
            "category": self.category,
            "version": self.version,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "effective_date": self.effective_date,
            "total_pages": self.total_pages,
            "total_chunks": self.total_chunks,
        }

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    policy_id = Column(String(36), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=False)
    section_heading = Column(String(255), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    
    # Store embedding floats as JSON array: [0.012, -0.045, ...]
    embedding_json = Column(Text, nullable=False)

    policy = relationship("Policy", back_populates="chunks")

    @property
    def embedding(self) -> list[float]:
        try:
            return json.loads(self.embedding_json)
        except Exception:
            return []

    @embedding.setter
    def embedding(self, val: list[float]):
        self.embedding_json = json.dumps(val)

    def to_dict(self):
        return {
            "id": self.id,
            "policy_id": self.policy_id,
            "document_name": self.policy.document_name if self.policy else "Unknown",
            "chunk_text": self.chunk_text,
            "page_number": self.page_number,
            "section_heading": self.section_heading,
            "chunk_index": self.chunk_index,
        }

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(64), nullable=False, index=True)
    user_query = Column(Text, nullable=False)
    interpreted_intent = Column(Text, nullable=True)
    hyde_passage = Column(Text, nullable=True)
    assistant_response = Column(Text, nullable=False)
    verification_status = Column(String(30), default="UNVERIFIED")
    retrieved_evidence = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "user_query": self.user_query,
            "interpreted_intent": self.interpreted_intent,
            "hyde_passage": self.hyde_passage,
            "assistant_response": self.assistant_response,
            "verification_status": self.verification_status,
            "retrieved_evidence": self.retrieved_evidence,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

