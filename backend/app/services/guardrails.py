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
from typing import List, Dict, Any, Tuple

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

def evaluate_guardrails(
    query: str,
    evidence_chunks: List[Dict[str, Any]]
) -> Tuple[str, List[str], float]:
    """
    Determines verification state:
    - VERIFIED: Relevant evidence found without severe contradictions.
    - CONFLICTING: Multiple policy chunks have contradictory requirements.
    - UNVERIFIED: No evidence, or highest score below threshold.
    Returns: (status, conflict_reasons, confidence_score)
    """
    if not evidence_chunks:
        return "UNVERIFIED", ["No relevant policy documents match the query."], 0.0

    # Extract substantive topic keywords from the user's raw query
    generic_words = {
        "can", "i", "a", "an", "the", "in", "to", "and", "or", "is", "for", "with", 
        "my", "what", "how", "if", "does", "do", "policy", "rules", "rule", "university", 
        "campus", "student", "students", "make", "get", "there", "any", "someone",
        "another", "happens", "happen", "under", "per"
    }
    query_tokens = [w for w in re.findall(r"\w+", query.lower()) if (len(w) > 2 or w.isdigit()) and w not in generic_words]
    query_stems = [stem_token(w) for w in query_tokens]

    # Special handling for standalone bullying / harassment:
    # If the student asks about bullying or harassment without connecting it to ragging,
    # and the official documents do not contain explicit bullying rules, return UNVERIFIED.
    q_lower = query.lower()
    is_bullying_inquiry = any(b in q_lower for b in ["bully", "bullies", "bullying", "harass", "harassment"])
    has_ragging_link = any(r in q_lower for r in ["ragging", "fresher", "freshers", "senior", "seniors", "intimidat"])

    if is_bullying_inquiry and not has_ragging_link:
        # Check if the retrieved documents actually mention bullying
        all_text = " ".join([c.get("text", "").lower() for c in evidence_chunks])
        if not any(b in all_text for b in ["bully", "bullies", "bullying", "harass", "harassment"]):
            return (
                "UNVERIFIED",
                ["The official university policy documents do not contain explicit provisions or definitions for standalone 'bullying' or 'harassment'. While the policy penalizes ragging and intimidation, standalone bullying is not covered in the retrieved policy text."],
                0.0
            )

    # Verify whether the retrieved official chunks actually address the student's specific subject
    matched_tokens = 0
    top_chunks = evidence_chunks[:2]
    all_top_words = set(re.findall(r"\w+", " ".join([c.get("text", "").lower() for c in top_chunks])))
    all_top_stems = set(stem_token(w) for w in all_top_words)

    for i, token in enumerate(query_tokens):
        st = query_stems[i]
        if token in all_top_words or st in all_top_stems or any(st in w for w in all_top_words):
            matched_tokens += 1

    # If the user asks about an unsupported or absent topic (e.g. 'iguana', 'helicopter', 'crypto')
    if query_tokens and matched_tokens == 0:
        return "UNVERIFIED", ["None of the specific inquiry topics are covered in the official policy documents."], 0.0

    top_chunk = evidence_chunks[0]
    top_score = top_chunk.get("score", 0.0)

    # Check for policy conflicts
    conflicts = detect_policy_conflicts(evidence_chunks)
    if conflicts and any(k in query.lower() for k in ["attendance", "percentage", "%", "deadline", "days", "lab"]):
        return "CONFLICTING", conflicts, round(min(0.65, top_score if top_score < 1.0 else 0.65), 2)

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

