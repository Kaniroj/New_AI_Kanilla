# backend/constants.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Paths
DATA_DIR = BASE_DIR / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
LANCEDB_DIR = DATA_DIR / "lancedb"

# LanceDB config
LANCEDB_TABLE_NAME = "transcript_chunks"
VECTOR_COL = "embedding"

# Embeddings
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
