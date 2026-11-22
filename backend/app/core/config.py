

import os
from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parents[3]
load_dotenv(BASE / "backend" / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

DOCS_DIR = BASE / "data" / "documents"
CHROMA_DIR = str(BASE / "data" / "chroma")

CHUNK_SIZE = 400
CHUNK_OVERLAP = 60

EMBED_MODELS = {
    "bge": "BAAI/bge-small-en-v1.5",
    "openai": "text-embedding-3-small",
}
DEFAULT_EMBED = "bge"



LLM_MODEL = "openai/gpt-oss-20b"

RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DATABASE_URL = os.getenv("DATABASE_URL")