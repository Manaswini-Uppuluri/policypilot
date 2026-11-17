"""
Runner script for PolicyPilot Backend.
Starts Uvicorn server on http://127.0.0.1:8000
"""
import sys
import os
from pathlib import Path
import uvicorn

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    print("==================================================")
    print(" PolicyPilot Backend - FastMCP & FastAPI Server")
    print(" Starting on http://127.0.0.1:8000")
    print(" API Documentation: http://127.0.0.1:8000/docs")
    print("==================================================")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

