from pathlib import Path
from typing import List

import pandas as pd

from backend.constants import TRANSCRIPTS_FOLDER, TRANSCRIPT_CHUNKS_PARQUET


CHUNK_SIZE = 800     
CHUNK_OVERLAP = 200  

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
 
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - overlap  
    return chunks


def main() -> None:
    transcripts_dir = Path(TRANSCRIPTS_FOLDER)

    if not transcripts_dir.exists():
        print(f" Transcripts folder not found: {transcripts_dir}")
        return

    rows = []

    
    md_files = sorted(transcripts_dir.glob("*.md"))
    txt_files = sorted(transcripts_dir.glob("*.txt"))
    all_files = md_files + txt_files

    if not all_files:
        print(f" No .md or .txt files found in {transcripts_dir}")
        return

    for path in all_files:
        video_id = path.stem
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="latin-1")

        chunks = chunk_text(text)
        if not chunks:
            print(f"⚠️  No text found in {path}, skipping.")
            continue

        for idx, chunk in enumerate(chunks):
            rows.append(
                {
                "id": f"{video_id}_{idx}",
                "video_id": video_id,
                "chunk_index": idx,
                "chunk_text": chunk,     
                "source_file": str(path),
                }
            )

    if not rows:
        print(" No transcript chunks created – check your markdown files.")
        return

    df = pd.DataFrame(rows)
    out_path = Path(TRANSCRIPT_CHUNKS_PARQUET)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(out_path, index=False)
    print(f" Wrote {len(df)} chunks to {out_path}")


if __name__ == "__main__":
    main()
