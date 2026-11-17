"""
Main FastAPI Application Entrypoint for PolicyPilot.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_engine, get_db, Base, is_sqlite_active, is_pgvector_active
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.retrieval import router as retrieval_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("policypilot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables are created
    logger.info("Initializing database tables...")
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
    logger.info("Database initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down PolicyPilot backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Campus Policy Discovery Assistant with HyDE, Hybrid Search & MCP",
    lifespan=lifespan
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(retrieval_router, prefix="/api/retrieval", tags=["Retrieval"])

@app.get("/", tags=["Root"])
def root():
    return {
        "service": "PolicyPilot Backend",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """
    Verify application health, database connectivity, and vector capabilities.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1")).fetchone()
    except Exception as e:
        db_status = f"unhealthy: {e}"

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": {
            "status": db_status,
            "backend": "sqlite" if (is_sqlite_active() or getattr(db.bind.dialect, "name", "") == "sqlite") else "postgresql",
            "pgvector_active": is_pgvector_active()
        },
        "config": {
            "llm_provider": settings.LLM_PROVIDER,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "rrf_k": settings.RRF_K
        }
    }

