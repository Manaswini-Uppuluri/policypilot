import sys
sys.path.insert(0, "backend")
from app.core.database import get_session
from app.services.evaluation import run_retrieval_evaluation

print("Running retrieval evaluation...")
with get_session() as db:
    data = run_retrieval_evaluation(db=db)
    print("\nSUCCESS!")
    print("Summary:", data["summary"])
    print("\nModes:")
    for m, v in data["modes"].items():
        r = v["avg_retrieval_latency_ms"]
        g = v["avg_generation_latency_ms"]
        t = v["avg_latency_ms"]
        print(f"  {m:<15}: pure_ret={r}ms | groq_gen={g}ms | total={t}ms (check: {round(r+g, 2)}ms)")
