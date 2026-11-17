"""
Query Scope & Context Resolution Service for PolicyPilot.
Determines whether incoming queries are in-scope for university policy discovery,
handles ambiguous inquiries, and resolves conversational follow-ups.

Core principle:
Use conversational context when the user's intention is clear.
Ask for clarification when multiple interpretations are possible.
Never turn an ambiguous assumption into a VERIFIED policy answer.
"""
import re
from typing import Tuple, Optional, List, Dict, Any

# University Policy Topic Definitions with keywords and natural phrasing
POLICY_TOPIC_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "ragging": {
        "label": "someone getting caught ragging",
        "short_name": "ragging",
        "keywords": [
            "ragging", "rag", "ragged", "fresher", "freshers", 
            "senior", "seniors", "junior", "juniors", "intimidation", 
            "intimidat", "bullying", "bully", "bullies", "assault", "harass", "harassment"
        ]
    },
    "attendance": {
        "label": "violating the attendance requirement",
        "short_name": "the attendance requirement",
        "keywords": [
            "attendance", "attend", "absent", "absence", "bunk", "bunking",
            "85%", "85 %", "75%", "75 %", "condonation", "shortage", 
            "falls below", "fall below", "medical certificate", "leave", "leaves"
        ]
    },
    "examinations": {
        "label": "examination malpractice or misconduct",
        "short_name": "examination malpractice",
        "keywords": [
            "exam", "exams", "examination", "examinations", "malpractice", 
            "cheating", "copying", "hall ticket", "internals", "admit card",
            "calculator in exam", "mobile in exam"
        ]
    },
    "hostel": {
        "label": "violating hostel rules or curfew",
        "short_name": "hostel rules",
        "keywords": [
            "hostel", "hostels", "dorm", "dorms", "curfew", "in-time", 
            "out-time", "warden", "overnight", "room allotment", "mess"
        ]
    },
    "property_damage": {
        "label": "damaging college property",
        "short_name": "damaging college property",
        "keywords": [
            "damage to property", "college property", "vandalism", 
            "damaging property", "break furniture", "laboratory equipment"
        ]
    },
    "substance": {
        "label": "substance prohibition or smoking",
        "short_name": "alcohol and smoking policies",
        "keywords": [
            "alcohol", "smoking", "smoke", "drugs", "narcotics", "substance abuse"
        ]
    }
}

# In-domain campus and policy tokens for general scope verification
CAMPUS_DOMAIN_STEMS = {
    "attend", "attendance", "absent", "absence", "bunk", "leave", "medical", 
    "condon", "condonation", "class", "lecture", "lab", "practic", "session",
    "intern", "internal", "exam", "examin", "test", "mark", "grade", "gpa", 
    "sgpa", "cgpa", "credit", "backlog", "makeup", "supplementari", "hall ticket",
    "admit card", "malpractic", "cheat", "copi", "calcul", "phone", "devic",
    "rag", "ragging", "fresh", "fresher", "senior", "junior", "bulli", "bully",
    "harass", "intimid", "intimidat", "assault", "fight", "misconduct", "disciplin",
    "rustic", "rusticat", "suspend", "suspens", "warn", "fine", "penalti", "penalty",
    "expel", "expuls", "debar", "conduct", "violat", "rule", "polici", "prohibit", 
    "ban", "punish", "grievanc", "complaint", "ombudsman",
    "hostel", "dorm", "curfew", "in-time", "out-time", "warden", "visit", "visitor", 
    "guest", "overnight", "room", "mess", "food", "campus", "colleg", "institut", 
    "univers", "msrit", "ramaiah", "dean", "director", "princip", "hod", "prof", 
    "faculti", "teacher",
    "fee", "fees", "refund", "scholarship", "admiss", "bonafid", "concess", 
    "certif", "id card", "ident", "uniform", "dress", "park", "vehicl", 
    "properti", "damag", "vandal", "smoke", "alcohol", "drink", "drug", "substanc"
}

# Out-of-domain categories that belong to general AI, not campus policy
OUT_OF_DOMAIN_CATEGORIES = [
    {
        "category": "sports_entertainment",
        "patterns": [
            r"\b(ipl|bbl|nba|fifa|uefa|epl|premier league|cricket|football|world cup|super bowl)\b",
            r"\b(who will win|match prediction|score of|won the match|t20|odi|batsman|bowler|wicket)\b",
            r"\b(movie review|box office|actor|actress|bollywood|hollywood|netflix|spotify)\b"
        ]
    },
    {
        "category": "science_nature",
        "patterns": [
            r"\b(quantum entanglement|quantum mechanics|theory of relativity|general relativity)\b",
            r"\b(thermodynamics|photosynthesis|mitosis|meiosis|schrodinger|black hole|string theory)\b",
            r"\b(calculus derivative|integration by parts|quadratic formula|solve equation)\b",
            r"\b(nutrition(al)? content|calories in|vitamins? in|health benefits? of|protein in)\b",
            r"\b(solar system|distance to the moon|speed of light|chemical formula of)\b"
        ]
    },
    {
        "category": "programming",
        "patterns": [
            r"\b(teach me|how to code in|write a program|write code in|write a script|debug my code)\b",
            r"\b(write a python program|write a java program|write a c program|write a cpp program)\b",
            r"\b(sort an array|reverse a linked list|fibonacci series|bubble sort|binary search)\b",
            r"\b(java recursion|python script|c\+\+ pointer|javascript promise|html css template|sql query)\b",
            r"\b(leetcode|binary tree traversal|quicksort|merge sort|regex for)\b"
        ]
    },
    {
        "category": "creative_personal",
        "patterns": [
            r"\b(write a birthday message|write a love letter|write a poem|write a song|write an essay on)\b",
            r"\b(birthday wish|gift for my (boyfriend|girlfriend|partner)|dating advice|love message)\b",
            r"\b(tell me a joke|horoscope|zodiac|astrology prediction)\b"
        ]
    },
    {
        "category": "world_trivia",
        "patterns": [
            r"\b(capital of|who is the president of|who is the prime minister of|population of)\b",
            r"\b(tallest mountain|longest river|currency of|history of the roman empire|world war 2)\b",
            r"\b(weather in|recipe for|how to cook|bake a cake)\b"
        ]
    },
    {
        "category": "commercial_recommendations",
        "patterns": [
            r"\b(which laptop should i buy|best smartphone|iphone vs samsung|recommend a car)\b",
            r"\b(stock market|cryptocurrency|bitcoin price|crypto investment|best credit card)\b"
        ]
    }
]

# Patterns where the query asks about consequences of being caught / violating, without naming the violation
AMBIGUOUS_ACTION_PATTERNS = [
    r"^what if (someone|anyone|a student|i|they) (gets? )?caught\??$",
    r"^what happens if (someone|anyone|a student|i|they) (gets? )?caught\??$",
    r"^what is the punishment if (someone|anyone|i|they) (gets? )?caught\??$",
    r"^what are the consequences if (someone|anyone|i|they) (gets? )?caught\??$",
    r"^what happens when caught\??$",
    r"^what consequences if caught\??$",
    r"^what if (someone|anyone|i|they) violates? the rule\??$",
    r"^what happens if (someone|anyone|i|they) violates? the rule\??$",
    r"^what if (someone|anyone|i|they) breaks? the rules?\??$",
    r"^what is the penalty\??$",
    r"^what are the consequences\??$"
]

def identify_query_topics(text: str) -> List[str]:
    """
    Identifies which policy topic domains are explicitly referenced in a piece of text.
    Returns list of topic keys, e.g. ['ragging'], ['attendance'].
    """
    text_lower = text.lower()
    matched_topics = []
    for topic_key, topic_info in POLICY_TOPIC_DEFINITIONS.items():
        for kw in topic_info["keywords"]:
            if kw.endswith("%"):
                if kw in text_lower:
                    matched_topics.append(topic_key)
                    break
            else:
                pattern = rf"\b{re.escape(kw)}\b"
                if re.search(pattern, text_lower):
                    matched_topics.append(topic_key)
                    break
    return matched_topics

def extract_history_topics(history: List[Any]) -> List[str]:
    """
    Extracts distinct policy topic keys discussed across previous user queries in this session,
    in chronological order. Ignores OUT_OF_SCOPE messages.
    """
    if not history:
        return []
    
    seen = set()
    ordered_topics = []
    for entry in history:
        v_status = getattr(entry, "verification_status", None) or (entry.get("verification_status") if isinstance(entry, dict) else "")
        if v_status == "OUT_OF_SCOPE":
            continue
        user_q = getattr(entry, "user_query", None) or (entry.get("user_query") if isinstance(entry, dict) else "")
        if not user_q:
            continue
        topics = identify_query_topics(user_q)
        for t in topics:
            if t not in seen:
                seen.add(t)
                ordered_topics.append(t)
    return ordered_topics

def check_is_ambiguous(q_lower: str) -> bool:
    """
    Checks if a query matches generic consequence/caught patterns without naming the violation.
    """
    return any(re.search(pat, q_lower) for pat in AMBIGUOUS_ACTION_PATTERNS)

def classify_query_scope(query: str, history: List[Any] = None) -> Tuple[str, str, Optional[str]]:
    """
    Classifies an incoming query into one of three states:
    1. "IN_SCOPE": Clear university policy inquiry -> Run RAG.
    2. "OUT_OF_SCOPE": Unrelated general AI query -> Return polite scope message.
    3. "NEEDS_CLARIFICATION": Ambiguous action or multiple possible historical topics -> Prompt for clarification.

    Returns:
        (status, message_or_scope, resolved_query)
    """
    clean_q = query.strip()
    q_lower = clean_q.lower()

    # Step 1: Check for Out-of-Domain Categories (Sports, Physics theory, Coding, Creative writing, etc.)
    for cat in OUT_OF_DOMAIN_CATEGORIES:
        for pat in cat["patterns"]:
            if re.search(pat, q_lower):
                has_policy_anchor = any(p in q_lower for p in ["policy", "rule", "regulat", "msrit", "attendance", "hostel", "ragging"])
                if not has_policy_anchor:
                    scope_msg = (
                        "PolicyPilot is designed to answer questions about university policies. "
                        "Your question is outside its scope."
                    )
                    return "OUT_OF_SCOPE", scope_msg, None

    # Step 2: Identify topics mentioned in the CURRENT query
    current_topics = identify_query_topics(clean_q)
    history_topics = extract_history_topics(history) if history else []

    # Step 3: Handle Ambiguous Action queries (e.g. "What if someone gets caught?")
    is_ambiguous = check_is_ambiguous(q_lower)

    if is_ambiguous:
        # Case 3A: The query itself explicitly contains a topic (e.g. "What if someone gets caught ragging?")
        if len(current_topics) == 1:
            # Explicitly in-scope for that topic!
            return "IN_SCOPE", f"Explicit topic: {current_topics[0]}", clean_q

        # Case 3B: Multiple distinct topics exist in previous conversation history
        # (e.g., Turn 1: ragging, Turn 2: attendance -> Turn 3: What if someone gets caught?)
        if len(history_topics) > 1:
            # Cannot arbitrarily pick the latest topic! Multiple interpretations are possible.
            topic_a = history_topics[0]
            topic_b = history_topics[1]
            label_a = POLICY_TOPIC_DEFINITIONS.get(topic_a, {}).get("label", topic_a)
            label_b = POLICY_TOPIC_DEFINITIONS.get(topic_b, {}).get("label", topic_b)
            
            clarification_msg = f"Are you referring to {label_a} or {label_b}?"
            return "NEEDS_CLARIFICATION", clarification_msg, None

        # Case 3C: Exactly one topic was discussed in conversation history
        # (e.g., Turn 1: ragging -> Turn 2: What if someone gets caught?)
        if len(history_topics) == 1:
            single_topic = history_topics[0]
            # Find the last in-scope entry in history (skipping any OUT_OF_SCOPE turns)
            last_entry = None
            for entry in reversed(history):
                v_status = getattr(entry, "verification_status", None) or (entry.get("verification_status") if isinstance(entry, dict) else "")
                if v_status != "OUT_OF_SCOPE":
                    last_entry = entry
                    break
            last_query = (getattr(last_entry, "user_query", None) or (last_entry.get("user_query") if isinstance(last_entry, dict) else "")) if last_entry else ""
            resolved_q = f"{last_query} (Follow-up inquiry: {clean_q})" if last_query else clean_q
            return "IN_SCOPE", f"Single active topic follow-up: {single_topic}", resolved_q

        # Case 3D: New conversation with no prior topic history
        clarification_msg = (
            "Could you please specify which university regulation or violation you are inquiring about? "
            "For example, are you asking about ragging, examination malpractice, attendance shortages, or hostel curfew violations?"
        )
        return "NEEDS_CLARIFICATION", clarification_msg, None

    # Step 4: Handle Contextual Follow-up inquiries (e.g. "What about the senior?", "What happens if someone falls below 85%?")
    # Check if query has an explicit topic or threshold (e.g. 85%, ragging, senior, attendance)
    if len(current_topics) > 0:
        # Check if this continues an ongoing conversation
        if history and len(history) > 0:
            last_entry = None
            for entry in reversed(history):
                v_status = getattr(entry, "verification_status", None) or (entry.get("verification_status") if isinstance(entry, dict) else "")
                if v_status != "OUT_OF_SCOPE":
                    last_entry = entry
                    break
            if last_entry:
                last_query = getattr(last_entry, "user_query", None) or (last_entry.get("user_query") if isinstance(last_entry, dict) else "")
                last_topics = identify_query_topics(last_query)
                is_followup = any(re.search(pat, q_lower) for pat in [
                    r"^(and )?what about\b", r"^(and )?how about\b", r"^what if\b", r"^what for\b", 
                    r"^and the\b", r"^what happens if\b", r"^what are the consequences\b"
                ])
                # If it's a follow-up pattern or continues the same topic
                if is_followup or (last_topics and current_topics[0] in last_topics):
                    return "IN_SCOPE", f"Contextual follow-up resolved on {current_topics[0]}.", f"{last_query} (Follow-up inquiry: {clean_q})"

        return "IN_SCOPE", f"In-scope topic: {current_topics[0]}", clean_q

    # Step 5: Check general in-domain campus / policy stems
    words = re.findall(r"\w+", q_lower)
    has_campus_anchor = any(
        any(w.startswith(stem) or stem in w for stem in CAMPUS_DOMAIN_STEMS)
        for w in words
    )

    policy_phrasing_patterns = [
        r"\b(rules?|polic(y|ies)|regulat(ion|ions)|guideline|ordinance|statute)\b",
        r"\b(can (i|a student|we)|am i allowed|is it (permitted|allowed|forbidden|banned|mandatory))\b",
        r"\b(what (happens|is the procedure|action is taken|are the consequences|is the penalty))\b",
        r"\b(minimum|threshold|percentage|eligib(le|ility)|criteria|requirement)\b"
    ]
    has_policy_phrasing = any(re.search(pat, q_lower) for pat in policy_phrasing_patterns)

    if has_campus_anchor or has_policy_phrasing:
        return "IN_SCOPE", "General policy inquiry.", clean_q

    # Step 6: Very short queries without campus anchors
    if len(words) <= 3 and not has_campus_anchor:
        greeting_words = {"hi", "hello", "hey", "greetings", "good morning", "good evening"}
        if any(g in q_lower for g in greeting_words):
            return "IN_SCOPE", "Greeting", clean_q
        
        return "OUT_OF_SCOPE", (
            "PolicyPilot is designed to answer questions about university policies. "
            "Your question is outside its scope."
        ), None

    # Default to in-scope
    return "IN_SCOPE", "General policy inquiry.", clean_q
