from __future__ import annotations

import os
import sys

if __name__ == "__main__":
    print("=== Starting RAG Data Observability & Chatbot Ecosystem ===")
    print("1. Launching FastAPI Data Observability Web Dashboard at http://localhost:8000 ...")
    print("2. Launching Streamlit RAG Chatbot Sandbox at http://localhost:8501 ...")
    
    os.system("uv run python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload &")
    os.system("uv run streamlit run app.py")
