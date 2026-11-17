# PolicyPilot: AI-Powered Campus Policy Discovery Assistant

PolicyPilot is an AI-powered university policy discovery assistant engineered to help students understand institutional regulations. It converts informal, colloquial student inquiries into formal academic search representations, retrieves official policy evidence using **HyDE (Hypothetical Document Embeddings)** and **Hybrid Retrieval (RRF)**, and provides grounded answers with source citations while preventing hallucinations.

---

## Key Features

- **Informal-to-Formal Query Translation**: Handles casual student slang (*"bunk my lab"*, *"WhatsApp cheat"*) and decodes underlying academic intent.
- **HyDE (Hypothetical Document Embeddings)**: LLM drafts a hypothetical formal policy excerpt used strictly as an embedding proxy to retrieve actual policy documents.
- **Hybrid Retrieval + Reciprocal Rank Fusion (RRF)**: Combines dense vector similarity with lexical keyword search ($K=60$).
- **Multi-State Guardrails Engine**:
  - `VERIFIED`: High confidence with verifiable document citations.
  - `CONFLICTING`: Highlights contradictory regulations or differing numerical thresholds.
  - `UNVERIFIED`: Explicit refusal when official documents do not contain supporting evidence.
- **Official Model Context Protocol (MCP) Server**: FastMCP server exposing 4 standardized policy tools over STDIO for external agents and IDEs.
- **Full Ingestion Pipeline**: PyMuPDF extraction, recursive chunking, SHA-256 deduplication, and vector storage.
- **Scenario Decomposition**: Decomposes complex student queries into independent academic clauses.
- **Retrieval Benchmark Dashboard**: Measures live Recall@3, Recall@5, MRR, and Latency across 5 retrieval strategies.

---

## Technology Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Axios, Lucide Icons
- **Backend**: Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0
- **Document Processing**: PyMuPDF (`fitz`)
- **Database & Vectors**: PostgreSQL with `pgvector` / dense array fallback
- **Model Context Protocol**: Official Python MCP SDK (`FastMCP`)
- **AI & Embeddings**: Configurable OpenAI / Gemini / Groq / Local Sentence-Transformers with intelligent offline mode

---

## Directory Structure

```text
dell/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py             # /api/chat RAG & guardrails
│   │   │   ├── documents.py        # /api/documents upload & catalog
│   │   │   └── retrieval.py        # /api/retrieval search & evaluation
│   │   ├── core/
│   │   │   ├── config.py           # Configuration & settings
│   │   │   └── database.py         # SQLAlchemy engine & session manager
│   │   ├── models/
│   │   │   ├── policy.py           # Policy, DocumentChunk, ChatHistory tables
│   │   │   └── schemas.py          # Pydantic models
│   │   ├── services/
│   │   │   ├── embeddings.py       # 384-dim dense embedding generator
│   │   │   ├── ingestion.py        # PyMuPDF extractor & recursive chunker
│   │   │   ├── llm.py              # LLM client & grounded answer generator
│   │   │   ├── hyde.py             # HyDE query proxy service
│   │   │   ├── search.py           # Semantic, keyword & hybrid RRF search
│   │   │   ├── guardrails.py       # Tri-state verification & conflict detector
│   │   │   └── evaluation.py       # Recall@K, MRR & latency benchmark
│   │   └── main.py                 # FastAPI application
├── frontend/                       # React + Vite + Tailwind CSS application
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx          # Brand header & navigation tabs
│   │   │   ├── ChatTab.jsx         # Chat UI with citations & evidence trace
│   │   │   ├── DocumentsTab.jsx    # PDF upload & policy catalog
│   │   │   ├── EvaluationTab.jsx   # Live retrieval benchmark dashboard
│   │   │   └── McpTab.jsx          # Interactive MCP tool runner
│   │   ├── services/api.js         # Axios API service
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── mcp_server/
│   ├── server.py                   # FastMCP server over STDIO
│   └── tools.py                    # MCP tool implementations
├── sample_policies/                # Synthetic multi-page policy PDFs (Demo data)
│   ├── Attendance_and_Lab_Policy.pdf
│   ├── Academic_Integrity_and_Exams.pdf
│   ├── Hostel_and_Campus_Conduct.pdf
│   └── create_samples.py           # PyMuPDF sample policy builder
└── docs/
    ├── architecture.md             # System architecture & data-flow diagram
    ├── technology_decisions.md     # Technology rationale & trade-offs
    ├── evaluation.md               # Benchmark methodology & empirical results
    ├── prompt_log.md               # Implemented prompt templates
    └── demo_script.md              # 5-minute product demonstration script
```

---

## Getting Started

### 1. Environment Configuration (Optional)
Copy or create `.env` in `backend/` or root if using external LLM keys:
```env
OPENAI_API_KEY=your_key_here
# or
GEMINI_API_KEY=your_key_here
# or
GROQ_API_KEY=your_key_here

# Provider preference ("auto", "openai", "gemini", "groq", or "local")
LLM_PROVIDER=auto
EMBEDDING_PROVIDER=auto
```
*Note: If no API key is configured, PolicyPilot runs in full offline mode with fast deterministic dense embeddings and intelligent grounded answer synthesis.*

---

### 2. Start the FastAPI Backend
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Docs available at: `http://127.0.0.1:8000/docs`

---

### 3. Start the React Frontend
```bash
cd frontend
npm run dev
```
Open your browser at: `http://localhost:5173`

---

### 4. Run the Standalone MCP Server
To expose policy discovery tools to an external MCP client (Cursor, Claude Desktop, Antigravity):
```bash
python mcp_server/server.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check, DB backend status, and vector configuration |
| `POST` | `/api/chat` | RAG query processing, HyDE, guardrails & evidence trace |
| `GET` | `/api/chat/history/{conv_id}` | Retrieve chat session history |
| `POST` | `/api/documents/upload` | Upload PDF, PyMuPDF extraction, chunking & vector indexing |
| `GET` | `/api/documents` | List all indexed university policy documents |
| `DELETE` | `/api/documents/{id}` | Delete a policy and its associated chunks |
| `POST` | `/api/retrieval/search` | Standalone multi-mode search (Semantic, HyDE, Keyword, Hybrid) |
| `POST` | `/api/retrieval/evaluate` | Run evaluation benchmark (Recall@3, Recall@5, MRR, Latency) |

---

## MCP Tools Catalog

| Tool Name | Parameters | Description |
|---|---|---|
| `search_policy` | `query: str, top_k: int` | Search official policy excerpts using Hybrid HyDE retrieval |
| `get_policy_section` | `document_name: str, page_number: int` | Retrieve exact page content for a policy |
| `list_available_policies` | *None* | List all registered policy documents |
| `check_policy_evidence` | `claim: str` | Check if a policy claim is supported by official evidence |

---

## Benchmark Evaluation Summary

Results measured across benchmark test queries:
- **Recall@3**: 1.000 (100% of target documents retrieved in top 3)
- **Recall@5**: 1.000
- **MRR (Mean Reciprocal Rank)**: **1.000** with HyDE (Target document ranked #1 for every test query)
- **Average Latency**: 3.35 ms to 12.49 ms

