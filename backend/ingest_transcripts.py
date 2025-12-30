
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path

import lancedb
import pandas as pd

from backend.data_models import Article
from backend.constants import (
    VECTOR_DATABASE_PATH,
    LANCEDB_TABLE_NAME,
    TRANSCRIPTS_FOLDER,
    TRANSCRIPT_CHUNKS_PARQUET,
)




def load_from_parquet() -> list[dict]:
  
    df = pd.read_parquet(TRANSCRIPT_CHUNKS_PARQUET)

 
    if "chunk_text" not in df.columns and "text" in df.columns:
        df = df.rename(columns={"text": "chunk_text"})

    required_cols = {"id", "chunk_text"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns in parquet file: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    articles: list[dict] = []
    for _, row in df.iterrows():
        articles.append(
            {
          
                "doc_id": str(row["id"]),
        
                "filepath": str(row.get("source_file", "")),
                
                "filename": str(row.get("video_id") or row["id"]),
               
                "content": str(row["chunk_text"]),
            }
        )

    print(f"Loaded {len(articles)} chunks from {TRANSCRIPT_CHUNKS_PARQUET}")
    return articles


def load_from_transcripts_folder() -> list[dict]:
   
    transcripts_dir = Path(TRANSCRIPTS_FOLDER)

    if not transcripts_dir.exists():
        print(f"Transcript folder not found: {transcripts_dir.resolve()}")
        return []

    articles: list[dict] = []

    for path in transcripts_dir.glob("*.txt"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="latin-1")

        articles.append(
            {
                "doc_id": path.stem,
                "filepath": str(path.resolve()),
                "filename": path.stem,
                "content": text,
            }
        )

    print(f"Loaded {len(articles)} raw articles from {transcripts_dir}")
    return articles


def main():
 
    VECTOR_DATABASE_PATH.mkdir(parents=True, exist_ok=True)


    try:
        articles = load_from_parquet()
    except FileNotFoundError:
        print(f"Parquet file not found at {TRANSCRIPT_CHUNKS_PARQUET}, falling back to raw transcripts…")
        articles = []
    except ValueError as e:
        print(f"Error loading parquet: {e}. Falling back to raw transcripts…")
        articles = []

    if not articles:
        articles = load_from_transcripts_folder()

    if not articles:
        print("No transcripts found – nothing to ingest.")
        return

    db = lancedb.connect(str(VECTOR_DATABASE_PATH))

    if LANCEDB_TABLE_NAME in db.table_names():
        table = db.open_table(LANCEDB_TABLE_NAME)
        table.add(articles)
        print(f"Added {len(articles)} rows to existing table '{LANCEDB_TABLE_NAME}'")
    else:
        table = db.create_table(LANCEDB_TABLE_NAME, schema=Article)
        table.add(articles)
        print(f"Created table '{LANCEDB_TABLE_NAME}' with {len(articles)} rows")


if __name__ == "__main__":
    main()
