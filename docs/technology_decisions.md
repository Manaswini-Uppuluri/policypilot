# Technology Decisions & Architectural Rationale

This document outlines the rationale behind every major architectural and technological choice in PolicyPilot.

---

## 1. Why PostgreSQL & pgvector?
- **Unified Relational & Vector Architecture**: Combining traditional tabular relational data (document metadata, categories, versioning, access timestamps) with vector embeddings in a single database avoids data drift between separate vector stores (like ChromaDB or Pinecone) and operational databases.
- **ACID Compliance**: Document deletion and re-indexing occur within atomic database transactions, guaranteeing that orphaned chunks or missing citations never exist.
- **Graceful Fallback**: In environments where native C extensions are pending compilation, PostgreSQL easily stores unit-normalized dense arrays, providing identical cosine distance scoring semantics.

---

## 2. Why Semantic Search vs. Keyword Search vs. Hybrid Retrieval?
| Approach | Strengths | Failure Mode |
|---|---|---|
| **Keyword Search (PostgreSQL FTS)** | Exact matching on policy section numbers, course codes, and acronyms (e.g., *"CIE"*, *"GPA"*, *"Section 2.1"*). | Complete failure when students use slang (*"bunk"*, *"gig"*, *"WhatsApp cheat"*) absent from formal documents. |
| **Semantic Search (Vector Cosine)** | Captures conceptual semantic proximity and paraphrasing. | Vulnerable to false positives on broad generic academic terms; can miss exact policy codes. |
| **Hybrid Retrieval (RRF)** | Merges reciprocal rankings from both channels without needing arbitrary weight tuning. | Combines semantic intent discovery with exact keyword grounding. |

---

## 3. Why Reciprocal Rank Fusion (RRF)?
Linear score combination ($\alpha \cdot S_{\text{dense}} + (1 - \alpha) \cdot S_{\text{sparse}}$) requires extensive cross-validation to calibrate disparate score distributions (cosine similarities range from $0.0$ to $1.0$, while BM25 scores can be unbounded). 
RRF uses pure rank positions:
$$RRF\_Score(d) = \sum_{m \in M} \frac{1}{K + \text{rank}(d, m)}$$
Setting $K=60$ prevents top-rank outliers from skewing results and ensures consistent multi-source ranking.

---

## 4. Why HyDE (Hypothetical Document Embeddings)?
When students ask questions in conversational or slang language (*"Can I bunk my lab and make it up later?"*), direct semantic embeddings of the query often drift toward social or general conversational vectors rather than institutional policy documents. 
HyDE prompts an LLM to generate a hypothetical administrative excerpt first. Because the hypothetical excerpt speaks the *lingua franca* of official regulations, its embedding lands directly in the semantic cluster of real policy documents.

---

## 5. Why FastMCP (Model Context Protocol)?
MCP is the emerging open standard for exposing tool execution capabilities to LLM hosts. Implementing FastMCP allows PolicyPilot's policy tools to be consumed not only by our own React interface, but also by any standard MCP-compatible client (such as Cursor, Claude Desktop, or custom Python agents) without creating proprietary agent wrappers.

---

## 6. Why PyMuPDF (`fitz`)?
PyMuPDF provides high-speed, C-optimized PDF rendering and text parsing. It accurately extracts bounding boxes, preserves physical page numbering, and handles complex multi-column academic layouts far more reliably than pure Python alternatives.

---

## 7. Cost & Latency Trade-offs
- **Batch Embedding Generation**: Embeddings are calculated only upon PDF ingestion and stored permanently; student search queries require only a single vector calculation.
- **Sub-15ms Hybrid Search**: Vector cosine similarity and token filtering execute in memory in 5–15 milliseconds.
- **Deterministic Guardrails**: Prompt injection defense and conflict detection execute deterministically via regex and numerical cross-checks prior to LLM synthesis, preventing costly LLM hallucination and unnecessary token consumption.

