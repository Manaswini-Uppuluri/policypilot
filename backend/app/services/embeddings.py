"""
Embedding Service for PolicyPilot.
Supports OpenAI, Gemini, local sentence-transformers, or deterministic TF-IDF/Hash embedding.
Dimension: 384 floats.
"""
import math
import hashlib
import re
import numpy as np
from typing import List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Cache local sentence transformer model if loaded
_local_model = None

def get_local_model():
    global _local_model
    if _local_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Fast, lightweight 384-dim model
            _local_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded sentence-transformers 'all-MiniLM-L6-v2' model.")
        except Exception as e:
            logger.warning(f"Could not load sentence-transformers ({e}). Using deterministic dense vectorizer.")
            _local_model = False
    return _local_model

STOPWORDS = {
    "the", "and", "a", "an", "in", "on", "of", "for", "to", "with", "is", "are", 
    "from", "by", "that", "this", "can", "how", "what", "many", "does", "do", "it", 
    "as", "at", "be", "or", "have", "has", "had", "my", "your", "we", "they"
}

def deterministic_dense_embed(text: str, dim: int = 384) -> List[float]:
    """
    Fallback deterministic dense embedding based on subword n-gram hashing and tf-idf weighting.
    Normalized to unit length for cosine similarity.
    """
    vec = np.zeros(dim, dtype=np.float32)
    all_words = re.findall(r"\w+", text.lower())
    words = [w for w in all_words if w not in STOPWORDS]
    if not words:
        words = all_words
    if not words:
        return vec.tolist()

    for word in words:
        # Hash word into bucket
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        vec[idx] += sign * (1.0 + math.log(1.0 + len(word)))

    # Subword 3-grams
    for i in range(len(text) - 2):
        trigram = text[i:i+3].lower()
        h = int(hashlib.sha256(trigram.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 4) % 2 == 0 else -1.0
        vec[idx] += 0.5 * sign

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()

def generate_embedding(text: str) -> List[float]:
    """
    Generate a 384-dimensional dense vector for a single text.
    """
    if not text.strip():
        return [0.0] * settings.EMBEDDING_DIMENSION

    # 1. Check OpenAI
    if settings.OPENAI_API_KEY and settings.EMBEDDING_PROVIDER in ["openai", "auto"]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            resp = client.embeddings.create(input=text, model="text-embedding-3-small", dimensions=settings.EMBEDDING_DIMENSION)
            return resp.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI embedding failed ({e}), falling back to local.")

    # 2. Check explicitly requested sentence-transformers
    if settings.EMBEDDING_PROVIDER == "sentence-transformers":
        model = get_local_model()
        if model and model is not False:
            try:
                emb = model.encode(text, convert_to_numpy=True)
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                return emb.tolist()
            except Exception as e:
                logger.warning(f"Local sentence-transformers encode failed ({e}).")

    # 3. Deterministic high-speed dense vectorizer (offline, sub-millisecond, unit-normalized)
    return deterministic_dense_embed(text, settings.EMBEDDING_DIMENSION)

def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts.
    """
    return [generate_embedding(t) for t in texts]

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Compute cosine similarity between two unit-normalized float vectors.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(dot / (norm_a * norm_b))
