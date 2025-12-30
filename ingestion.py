from typing import List, Tuple
import lancedb
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from backend.constants import (
    TRANSCRIPTS_DIR,
    LANCEDB_DIR,
    EMBEDDING_MODEL_NAME,
    LANCEDB_TABLE_NAME,
)


class TranscriptChunk(BaseModel):

    video_id: str
    chunk_id: int
    text: str


def load_transcripts() -> List[Tuple[str, str]]:

    transcripts: List[Tuple[str, str]] = []

    if not TRANSCRIPTS_DIR.exists():
        raise RuntimeError(f"Transcript directory does not exist: {TRANSCRIPTS_DIR}")

    for path in TRANSCRIPTS_DIR.glob("*"):
        if path.suffix.lower() not in [".md", ".txt"]:
            continue

        video_id = path.stem
        text = path.read_text(encoding="utf-8")
        transcripts.append((video_id, text))

    return transcripts


def chunk_text(
    text: str,
    video_id: str,
    chunk_size: int = 800,
    overlap: int = 150,
) -> List[TranscriptChunk]:

    chunks: List[TranscriptChunk] = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]

        chunks.append(
            TranscriptChunk(
                video_id=video_id,
                chunk_id=chunk_id,
                text=chunk_text,
            )
        )

        chunk_id += 1
        start = end - overlap

    return chunks


def build_lancedb():

    transcripts = load_transcripts()
    if not transcripts:
        raise RuntimeError(f"No transcript files found in {TRANSCRIPTS_DIR}")

    print(f"Found {len(transcripts)} transcript files")


    all_chunks: List[TranscriptChunk] = []
    for video_id, full_text in transcripts:
        video_chunks = chunk_text(full_text, video_id)
        all_chunks.extend(video_chunks)

    print(f"Total chunks: {len(all_chunks)}")


    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    texts = [c.text for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True)


    LANCEDB_DIR.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(LANCEDB_DIR))


    if LANCEDB_TABLE_NAME in db.table_names():
        db.drop_table(LANCEDB_TABLE_NAME)

    rows = []
    for chunk, emb in zip(all_chunks, embeddings):
        rows.append(
            {
                "video_id": chunk.video_id,
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "embedding": emb,
            }
        )

    table = db.create_table(
        LANCEDB_TABLE_NAME,
        data=rows,  
    )

    print(f"LanceDB table '{LANCEDB_TABLE_NAME}' created with {table.count_rows()} rows")
    print(f"LanceDB path: {LANCEDB_DIR}")



if __name__ == "__main__":
    build_lancedb()
