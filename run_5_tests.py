"""
Live verification test against PolicyPilot Backend (http://127.0.0.1:8000/api/chat).
Tests all 5 queries with real Groq LLM inference.
"""
import urllib.request
import json
import time

test_queries = [
    "What are the consequences for ragging?",
    "What happens if seniors intimidate freshers?",
    "Can a student be suspended for ragging?",
    "What happens if someone bullies another student?",
    "What is the punishment for ragging under the Karnataka Education Act?"
]

print("======================================================================")
print(" POLICYPILOT - 5 QUERIES VERIFICATION TEST (LIVE BACKEND + GROQ)")
print("======================================================================\n")

for i, query in enumerate(test_queries, 1):
    print(f"----------------------------------------------------------------------")
    print(f"TEST {i}: {query}")
    print(f"----------------------------------------------------------------------")
    
    payload = json.dumps({
        "query": query,
        "search_mode": "hybrid_hyde",
        "top_k": 4
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - start
            
            status = data.get("verification_status")
            answer = data.get("answer", "")
            citations = data.get("citations", [])
            trace = data.get("evidence_trace", {})
            
            print(f"[*] Latency: {elapsed:.2f}s | Status: {status}")
            print(f"[*] HyDE Passage Generated: {bool(trace.get('hyde_passage'))}")
            if trace.get("hyde_passage"):
                print(f"    HyDE Preview: {trace['hyde_passage'][:140]}...")
            
            print(f"[*] Retrieved Chunks ({len(trace.get('retrieved_chunks', []))}):")
            for c in trace.get("retrieved_chunks", [])[:3]:
                print(f"    - Page {c['page_number']} [Score: {c['score']}] Heading: {c.get('section_heading', 'General')}")
                print(f"      Text: {c['text'][:110]}...")
            
            print(f"[*] Citations Returned ({len(citations)}):")
            for cit in citations:
                print(f"    - [{cit['document_name']}, Page {cit['page_number']}] Section: {cit.get('section_heading')}")
            
            print(f"\n[*] Final Generated Answer:")
            print(answer)
            print()
            
    except Exception as e:
        print(f"[!] Request failed: {e}")
        print()

print("======================================================================")
print(" ALL 5 TESTS COMPLETE")
print("======================================================================")
