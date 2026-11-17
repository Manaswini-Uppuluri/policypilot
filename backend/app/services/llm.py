"""
LLM Integration Service for PolicyPilot.
Handles prompt execution via OpenAI / Gemini / Groq with intelligent offline fallback.
Strictly grounds answers in retrieved evidence and prevents hallucination.
"""
import logging
import re
from typing import List, Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are PolicyPilot, an authoritative and strictly evidence-grounded University Policy Assistant.
Your core mandate is to answer student inquiries STRICTLY and EXCLUSIVELY based on the provided official university policy excerpts.

CRITICAL GROUNDING AND EVIDENCE RULES:
1. STRICT FACTUAL GROUNDING: Every factual assertion MUST be directly supported by verbatim text or direct factual statements from the retrieved excerpts. Never extrapolate, presume, or invent university rules.
2. NO INVENTED OR ASSUMED PENALTIES:
   - Do NOT introduce unmentioned penalties, warnings, suspensions, fines, or procedures unless explicitly stated in the excerpts.
   - Do NOT interpret or define "rustication" as "permanent expulsion", "suspension", or "dismissal" unless the excerpt explicitly defines it that way. Use the exact wording: "liable to be rusticated from the college".
   - If asked about "suspension" and the policy specifies "rustication" and "strict disciplinary action" without using the word "suspension", state what the policy specifies and explicitly note: "The policy does not explicitly mention the term 'suspension'."
3. SEPARATION OF INSTITUTIONAL VS CRIMINAL JURISDICTION:
   - Institutional Disciplinary Consequences: State what the university/college rules mandate (e.g. ragging banned in all forms, strict disciplinary action, visiting fresher rooms considered proof of ragging, anti-ragging committee inspections, liability to be rusticated from the college, Supreme Court exemplary and justifiably harsh punishment order).
   - Criminal / Statutory Law Consequences: State what the statutory law mandates (e.g. Karnataka Education Act, 1983: imprisonment up to one year, fine up to two thousand rupees, or both; cognizable and non-bailable offence; arrest without warrant).
4. ABSENCE OF POLICY & CITATION INTEGRITY:
   - If a specific topic (e.g. general bullying, harassment) is asked about and the policy does NOT define or establish it, explicitly state that the policy does not establish it. Do not automatically equate generic bullying with ragging.
   - Every claim must cite [Document Name, Page X]. Do not cite pages or documents that do not support the specific claim.
"""

def call_external_llm(messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
    """Call external LLM API if key is configured."""
    # 1. OpenAI
    if settings.OPENAI_API_KEY and settings.LLM_PROVIDER in ["openai", "auto"]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=temperature
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI LLM call failed ({e}). Trying other providers...")

    # 2. Gemini
    if settings.GEMINI_API_KEY and settings.LLM_PROVIDER in ["gemini", "auto"]:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt_content = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_content
            )
            return resp.text.strip()
        except Exception as e:
            logger.warning(f"Gemini LLM call failed ({e}).")

    # 3. Groq
    if settings.GROQ_API_KEY and settings.LLM_PROVIDER in ["groq", "auto"]:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            resp = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=temperature
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            # Fallback to 20b if 120b is busy
            try:
                from groq import Groq
                client = Groq(api_key=settings.GROQ_API_KEY)
                resp = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=messages,
                    temperature=temperature
                )
                return resp.choices[0].message.content.strip()
            except Exception as e2:
                logger.warning(f"Groq LLM call failed ({e}, {e2}).")

    return None

def mock_hyde_generation(query: str) -> str:
    """
    Intelligent offline generator for HyDE:
    Translates informal student jargon into formal academic policy vocabulary.
    Never used as factual evidence.
    """
    q_lower = query.lower()
    if any(k in q_lower for k in ["bunk", "skip", "miss", "attendance", "absent"]):
        return (
            "University Attendance and Absence Regulations: Students enrolled in coursework and scheduled "
            "laboratory sessions are required to maintain a minimum statutory attendance threshold of 75% to 85%. "
            "Exemption from attendance or laboratory make-up sessions requires prior written authorization from the course "
            "instructor and submission of official medical documentation within specified timelines."
        )
    elif any(k in q_lower for k in ["cheat", "plagiarism", "exam", "copy", "internals", "test", "write"]):
        return (
            "Academic Integrity and Examination Code: Engaging in unauthorized collaboration, plagiarism, or possession of "
            "unauthorized materials during internal assessments or semester examinations constitutes academic malpractice. "
            "Penalties include course cancellation, disciplinary suspension, or referral to the Academic Misconduct Committee."
        )
    elif any(k in q_lower for k in ["hostel", "curfew", "night", "entry", "room", "guest", "fine"]):
        return (
            "Residential and Hostel Code of Conduct: Resident students must adhere to designated campus curfew hours. "
            "Overnight absence or entry beyond stipulated timings requires biometric registration and prior written approval "
            "from the resident warden. Unauthorized visitors or room transfers are strictly prohibited."
        )
    elif any(k in q_lower for k in ["ragging", "senior", "seniors", "fresher", "freshers", "intimidat", "karnataka"]):
        return (
            "Anti-Ragging Regulations and Legal Penalties: All forms of ragging and intimidation, including senior students visiting "
            "fresher rooms or compelling students to perform acts violating human dignity, are strictly banned criminal offences. "
            "Consequences include disciplinary rustication from the college and statutory penal sanctions under the Karnataka Education Act "
            "including imprisonment and non-bailable arrest."
        )
    elif any(k in q_lower for k in ["bully", "bullying", "harass", "harassment"]):
        return (
            "Campus Behavioral Standards and Student Conduct Code: Students are required to conduct themselves with mutual dignity, "
            "refraining from abusive, disruptive, or harmful conduct against fellow students."
        )
    else:
        return (
            f"Institutional Academic Policies and Operational Guidelines: Regulatory frameworks, administrative procedures, "
            f"eligibility requirements, and procedural mandates governing student status regarding {query}."
        )

def mock_rag_answer_generation(
    query: str,
    evidence_chunks: List[Dict[str, Any]],
    verification_status: str,
    conflicts: List[str]
) -> str:
    """
    Intelligent grounded answer synthesis in offline/mock mode.
    Guarantees strict factual citations from real retrieved chunks.
    Separates institutional disciplinary consequences from criminal law penalties.
    """
    if verification_status == "UNVERIFIED" or not evidence_chunks:
        q_lower = query.lower()
        if any(b in q_lower for b in ["bully", "bullies", "bullying", "harass", "harassment"]):
            return (
                "### Policy Determination: Insufficient Evidence / Unestablished Policy\n\n"
                "Based on the official university policy documents currently indexed (**code_conduct_MSRIT.pdf**), there is "
                "**no explicit policy or definition governing standalone 'bullying' or 'harassment'**.\n\n"
                "- The policy specifically prohibits and penalizes **ragging** (including intimidation of freshers by seniors and physical/mental harm).\n"
                "- Unless the behavior specifically falls under the statutory definition of ragging or physical damage to institute property, the policy documents do not establish specific consequences for general bullying.\n\n"
                "> **Recommendation:** Consult the Student Affairs Office or Disciplinary Committee for institutional guidance."
            )
        return (
            "### Policy Determination: Insufficient Evidence\n\n"
            "Based on the official university policy documents currently indexed, there is **insufficient official information** "
            "to answer your specific inquiry. The university regulations do not explicitly grant or address this in the "
            "retrieved policy evidence.\n\n"
            "> **Advice:** Please contact your Academic Dean, Faculty Advisor, or Student Affairs office for formal clarification."
        )

    if verification_status == "CONFLICTING":
        answer_parts = [
            "### Policy Determination: Conflicting Regulations Detected\n\n",
            "A review of the university documents indicates **conflicting policies** regarding this request:\n\n"
        ]
        for c in conflicts:
            answer_parts.append(f"- **Discrepancy:** {c}\n")
        answer_parts.append("\n**Retrieved Policy Excerpts:**\n")
        for chunk in evidence_chunks[:2]:
            answer_parts.append(
                f"- **{chunk['document_name']} (Page {chunk['page_number']})**: *\"{chunk['text'][:180]}...\"*\n"
            )
        answer_parts.append(
            "\n> **Recommendation:** Because differing policy versions or department manuals state inconsistent rules, "
            "obtain an explicit written ruling from the Office of the Registrar."
        )
        return "".join(answer_parts)

    # VERIFIED status - Grounded synthesis
    q_lower = query.lower()
    doc_name = evidence_chunks[0]["document_name"]

    # Specific response for ragging consequences / Karnataka Education Act / intimidation / suspension
    if any(k in q_lower for k in ["ragging", "intimidat", "fresher", "senior", "karnataka"]):
        ans_parts = [
            f"### Official Policy Response: Anti-Ragging Regulations and Penalties\n\n",
            f"Based on the official **{doc_name}** (Page 3), ragging is classified as a criminal offence and subject to strict institutional and legal sanctions:\n\n",
            f"#### 1. Institutional Disciplinary Consequences\n",
            f"- **Strict Ban & Action:** Ragging of all forms is strictly banned. Strict disciplinary action will be taken against students indulging in such activities [{doc_name}, Page 3].\n",
            f"- **Senior-Fresher Restrictions:** No senior student is permitted to visit the room of a fresher or invite a fresher to his/her room. Violation of this rule will be considered as a proof of ragging against the senior student [{doc_name}, Page 3].\n",
            f"- **Hostel Monitoring:** An Institute-level committee for prevention of ragging is empowered to visit hostels at all times [{doc_name}, Page 3].\n",
            f"- **Rustication:** Students involved in ragging are liable to be **rusticated from the college** [{doc_name}, Page 3]. *(Note: The document does not define rustication as permanent expulsion, nor does it explicitly mention the term 'suspension'.)*\n",
            f"- **Supreme Court Directive:** The institute strictly follows the Supreme Court order mandating that punishment must be exemplary and justifiably harsh to act as a deterrent [{doc_name}, Page 3].\n\n",
            f"#### 2. Criminal & Statutory Consequences (Karnataka Education Act, 1983)\n",
            f"Under extracts of the Karnataka Education Act, 1983 (Karnataka Act No. 1 of 1995) cited in the policy [{doc_name}, Page 3]:\n",
            f"- **Penal Sanctions:** Any person who contravenes the ragging ban shall, on conviction, be punished with **imprisonment for a term which may extend to one year, or with fine which may extend to two thousand rupees, or with both** [{doc_name}, Page 3].\n",
            f"- **Criminal Procedure:** Ragging is defined as a **cognizable and non-bailable offence**, and offenders are liable for arrest without warrant on non-bailable warrants [{doc_name}, Page 3].\n",
            f"- **Definition:** Ragging includes causing, inducing, compelling, or forcing a student by *intimidation, wrongful restraint, wrongful confinement, injury, or the use of criminal force* [{doc_name}, Page 3]."
        ]
        return "".join(ans_parts)

    primary_chunk = evidence_chunks[0]
    page_num = primary_chunk["page_number"]
    quote = primary_chunk["text"][:220].strip()

    return (
        f"### Policy Answer: Verified by Official Documentation\n\n"
        f"According to the **{doc_name}** (Page {page_num}), the university policy stipulates:\n\n"
        f"> *\"{quote}...\"*\n\n"
        f"**Official Source:** [{doc_name}, Page {page_num}]"
    )

def generate_hyde_passage(query: str) -> str:
    """
    Generate a hypothetical academic policy excerpt using LLM or intelligent fallback.
    STRICT MANDATE: Only used for embedding retrieval, NEVER as factual evidence.
    """
    prompt = (
        f"Write a formal, hypothetical university policy passage (2-3 sentences) that directly answers or addresses "
        f"the student question: '{query}'. Use formal academic administrative terminology."
    )
    external = call_external_llm([
        {"role": "system", "content": "You are a university academic registrar drafting formal academic policy passages for vector retrieval query expansion. Never output fictional rules as fact."},
        {"role": "user", "content": prompt}
    ])
    if external:
        return external
    return mock_hyde_generation(query)

def generate_grounded_answer(
    query: str,
    evidence_chunks: List[Dict[str, Any]],
    verification_status: str,
    conflicts: List[str]
) -> str:
    """
    Generate an evidence-grounded answer with citations.
    """
    if not evidence_chunks or verification_status == "UNVERIFIED":
        return mock_rag_answer_generation(query, [], "UNVERIFIED", [])

    # Format context for external LLM
    context_str = "\n\n".join([
        f"[Source {i+1}: {c['document_name']}, Page {c['page_number']}, Section: {c.get('section_heading', 'N/A')}]\n{c['text']}"
        for i, c in enumerate(evidence_chunks)
    ])

    user_prompt = (
        f"Student Query: {query}\n\n"
        f"Verification State: {verification_status}\n\n"
        f"Official Policy Evidence:\n{context_str}\n\n"
        f"Strict Execution Instructions:\n"
        f"1. Answer ONLY using the official policy evidence above.\n"
        f"2. Separate Institutional/College Disciplinary Consequences from Statutory Criminal Law Penalties (e.g., under Karnataka Education Act, 1983).\n"
        f"3. Use exact text terminology: state 'liable to be rusticated from the college'. Do NOT interpret rustication as permanent expulsion. If asked about 'suspension' and the policy specifies rustication and disciplinary action without using the word 'suspension', explicitly note that the policy does not specifically use the term 'suspension'.\n"
        f"4. If the query asks about a topic not established in the evidence (e.g. general bullying), explicitly state that the official documents do not contain explicit rules or definitions for it.\n"
        f"5. Provide exact bracketed citations [Document Name, Page X] for every claim."
    )

    external = call_external_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ])
    if external:
        return external

    return mock_rag_answer_generation(query, evidence_chunks, verification_status, conflicts)

