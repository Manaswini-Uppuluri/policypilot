"""
Guardrails & Verification Service for PolicyPilot.
Implements:
1. Relevance threshold checks.
2. Prompt injection & override defense.
3. Policy conflict detection across different retrieved chunks.
4. Tri-state status determination: VERIFIED, CONFLICTING, UNVERIFIED.
5. Verification that all citations correspond to actual document pages.
"""
import re
import json
import logging
from typing import List, Dict, Any, Tuple
from app.services.llm import call_external_llm

logger = logging.getLogger(__name__)

# Minimum relevance score threshold to consider evidence valid
SEMANTIC_RELEVANCE_THRESHOLD = 0.20
HYBRID_RELEVANCE_THRESHOLD = 0.01

INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"disregard all rules",
    r"you are now an administrator",
    r"grant me an exemption",
    r"system prompt override",
    r"pretend to be the dean"
]

def sanitize_user_query(query: str) -> Tuple[str, bool]:
    """
    Checks for and neutralizes prompt injection or policy override attempts.
    Returns (cleaned_query, was_injection_detected).
    """
    detected = False
    cleaned = query
    for pat in INJECTION_PATTERNS:
        if re.search(pat, cleaned, re.IGNORECASE):
            detected = True
            cleaned = re.sub(pat, "[FILTERED_OVERRIDE_ATTEMPT]", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(), detected

def detect_policy_conflicts(evidence_chunks: List[Dict[str, Any]]) -> List[str]:
    """
    Analyzes retrieved chunks for apparent contradictions or disparate numerical thresholds.
    E.g. attendance percentage discrepancies (75% vs 80% vs 65%), differing deadlines.
    """
    conflicts = []
    if len(evidence_chunks) < 2:
        return conflicts

    # 1. Check for conflicting percentages across documents and sections
    percentages = {}
    for c in evidence_chunks:
        doc = c["document_name"]
        sec = c.get("section_heading") or "General"
        label = f"{doc} - {sec}"
        text = c["text"]
        matches = re.findall(r"(\d{2})%", text)
        if matches:
            percentages[label] = set(int(m) for m in matches)

    if len(percentages) >= 2:
        unique_vals = set()
        for vals in percentages.values():
            unique_vals.update(vals)
        if len(unique_vals) > 1:
            diff_docs = [f"{lbl} specifies {sorted(list(vals))}%" for lbl, vals in percentages.items()]
            conflicts.append(f"Inconsistent percentage requirements found: {'; '.join(diff_docs)}")

    # 2. Check for differing deadlines / days
    days_map = {}
    for c in evidence_chunks:
        doc = c["document_name"]
        sec = c.get("section_heading") or "General"
        label = f"{doc} - {sec}"
        text = c["text"]
        matches = re.findall(r"within\s+(\d+)\s+(?:working\s+)?days", text, re.IGNORECASE)
        if matches:
            days_map[label] = set(int(d) for d in matches)

    if len(days_map) >= 2:
        unique_days = set()
        for vals in days_map.values():
            unique_days.update(vals)
        if len(unique_days) > 1:
            diff_days = [f"{lbl} states {sorted(list(vals))} days" for lbl, vals in days_map.items()]
            conflicts.append(f"Contradictory timeline requirements: {'; '.join(diff_days)}")

    return conflicts

def stem_token(word: str) -> str:
    """Stem token for query-chunk relevance checking."""
    word = word.lower().strip()
    if len(word) <= 3:
        return word
    for suffix in ["ing", "tion", "tions", "ies", "es", "ed", "s", "ment"]:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            word = word[:-len(suffix)]
            break
    if word.endswith("e") and len(word) > 3:
        word = word[:-1]
    return word

def verify_evidence_sufficiency(query: str, evidence_chunks: List[Dict[str, Any]]) -> Tuple[bool, bool, str, str]:
    """
    Performs claim-level evidence verification:
    Evaluates whether the retrieved passages directly support/establish the answer to the query,
    or merely discuss a related topic without directly answering the specific inquiry.

    Returns: (is_sufficient, has_conflict, reason, conflict_details)
    """
    if not evidence_chunks:
        return False, False, "No policy evidence retrieved.", ""

    # Pass up to top 3 retrieved chunks as context for strict claim-level verification
    context_passages = "\n\n".join([
        f"[Passage {i+1} - {c['document_name']}, Page {c['page_number']}]\n{c['text']}"
        for i, c in enumerate(evidence_chunks[:3])
    ])

    verification_prompt = f"""You are a strict academic policy evidence validator for a university policy assistant.
Evaluate whether the retrieved official policy passages directly and sufficiently provide the answer to the student query.

Student Query: "{query}"

Retrieved Official Policy Passages:
{context_passages}

CRITICAL RULES:
1. "sufficient": true ONLY if the passages contain direct, explicit statements that answer the specific question asked.
2. "sufficient": false if the passages only discuss a related general topic (for example: general attendance rules when asked about sports exemption; or prohibited exam electronics/books when asked about dogs/pets; or general conduct when asked about hostel curfew) but DO NOT establish the specific rule, exemption, or permission asked about.
3. "sufficient": false if answering requires indirect assumptions, extrapolation, or guessing what invigilators/officials might decide.
4. "has_conflict": true if the passages contradict each other on deadlines, percentages, or rules.

Reply ONLY with valid JSON in this exact structure:
{{
  "sufficient": true,
  "has_conflict": false,
  "conflict_reason": "",
  "reason": "1-2 sentence explanation"
}}"""

    try:
        raw_res = call_external_llm([{"role": "user", "content": verification_prompt}], temperature=0.0)
        if raw_res:
            # Clean possible markdown formatting
            cleaned_json = raw_res.strip()
            if cleaned_json.startswith("```"):
                cleaned_json = re.sub(r"^```(?:json)?\s*", "", cleaned_json)
                cleaned_json = re.sub(r"\s*```$", "", cleaned_json)
            parsed = json.loads(cleaned_json)
            return (
                bool(parsed.get("sufficient", False)),
                bool(parsed.get("has_conflict", False)),
                str(parsed.get("reason", "")),
                str(parsed.get("conflict_reason", ""))
            )
    except Exception as e:
        logger.warning(f"LLM evidence verification failed or timed out: {e}")

    # Fallback to deterministic token-level validation if LLM call is unavailable
    return fallback_evidence_sufficiency(query, evidence_chunks)

def fallback_evidence_sufficiency(query: str, evidence_chunks: List[Dict[str, Any]]) -> Tuple[bool, bool, str, str]:
    """
    Deterministic fallback when external LLM is offline or unreachable.
    Checks whether key substantive inquiry terms actually appear in the retrieved text.
    """
    q_lower = query.lower()
    all_text = " ".join([c.get("text", "").lower() for c in evidence_chunks[:3]])

    # 1. Check for known unsupported domain queries
    unsupported_topics = [
        (["dog", "dogs", "pet", "pets", "animal", "animals"], "examinations", "The policy documents do not mention dogs, pets, or animals."),
        (["sport", "sports", "athletic", "tournament"], "attendance", "The policy documents do not contain attendance exemptions for sports competitions."),
        (["curfew", "in-time", "out-time", "closing time"], "hostel", "The policy documents do not specify hostel curfew timings."),
        (["bully", "bullies", "bullying"], "conduct", "Standalone bullying is not defined or established in the code of conduct.")
    ]
    for terms, domain, reason in unsupported_topics:
        if any(t in q_lower for t in terms) and not any(t in all_text for t in terms):
            return False, False, reason, ""

    # 2. Extract substantive query tokens
    generic_words = {
        "can", "i", "a", "an", "the", "in", "to", "and", "or", "is", "for", "with", 
        "my", "what", "how", "if", "does", "do", "policy", "rules", "rule", "university", 
        "campus", "student", "students", "make", "get", "there", "any", "someone",
        "another", "happens", "happen", "under", "per"
    }
    query_tokens = [w for w in re.findall(r"\w+", q_lower) if (len(w) > 2 or w.isdigit()) and w not in generic_words]
    query_stems = [stem_token(w) for w in query_tokens]

    all_words = set(re.findall(r"\w+", all_text))
    all_stems = set(stem_token(w) for w in all_words)

    matched = sum(1 for i, t in enumerate(query_tokens) if t in all_words or query_stems[i] in all_stems)
    ratio = (matched / len(query_tokens)) if query_tokens else 0.0

    if ratio >= 0.5:
        return True, False, "Sufficient keyword alignment with retrieved policy text.", ""
    return False, False, "Insufficient direct evidence in retrieved passages.", ""

def evaluate_guardrails(
    query: str,
    evidence_chunks: List[Dict[str, Any]]
) -> Tuple[str, List[str], float]:
    """
    Determines verification state:
    - VERIFIED: All substantive claims directly supported by retrieved policy evidence.
    - CONFLICTING: Multiple policy chunks have contradictory requirements.
    - UNVERIFIED: Insufficient direct supporting evidence in retrieved passages.
    Returns: (status, conflict_reasons, confidence_score)
    """
    if not evidence_chunks:
        return "UNVERIFIED", ["No relevant policy documents match the query."], 0.0

    top_chunk = evidence_chunks[0]
    top_score = top_chunk.get("score", 0.0)

    # Step 1: Detect policy conflicts across retrieved chunks
    conflicts = detect_policy_conflicts(evidence_chunks)

    # Step 2: Perform Claim-Level Evidence Verification
    is_sufficient, has_conflict_llm, reason, conflict_details = verify_evidence_sufficiency(query, evidence_chunks)

    if has_conflict_llm and conflict_details:
        conflicts.append(conflict_details)

    if conflicts and any(k in query.lower() for k in ["attendance", "percentage", "%", "deadline", "days", "lab"]):
        return "CONFLICTING", conflicts, round(min(0.65, top_score if top_score < 1.0 else 0.65), 2)

    # If the evidence does not directly support the specific question asked -> UNVERIFIED
    if not is_sufficient:
        return "UNVERIFIED", [reason] if reason else ["Insufficient evidence in retrieved policy documents."], 0.0

    confidence = min(0.98, max(0.60, top_score * 1.2 if top_score < 1.0 else 0.95))
    return "VERIFIED", [], round(confidence, 2)

def extract_valid_citations(evidence_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts structured, verified citations pointing to real pages and documents.
    Only includes chunks with substantive relevance.
    """
    citations = []
    seen = set()
    for c in evidence_chunks:
        # Avoid citing chunks with near-zero relevance score
        if c.get("score", 0.0) <= 0.005:
            continue
        key = (c["document_name"], c["page_number"])
        if key not in seen:
            seen.add(key)
            citations.append({
                "document_name": c["document_name"],
                "page_number": c["page_number"],
                "section_heading": c.get("section_heading", "General"),
                "quote": c["text"][:160].strip(),
                "score": c.get("score", 0.0)
            })
    return citations

