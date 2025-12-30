# backend/rag.py

from dotenv import load_dotenv
load_dotenv()

import lancedb
from pydantic_ai import Agent
from sentence_transformers import SentenceTransformer

from backend.data_models import RagResponse
from backend.constants import (
    LANCEDB_DIR,
    LANCEDB_TABLE_NAME,
    EMBEDDING_MODEL_NAME,
    VECTOR_COL,
)

# Connect to LanceDB
vector_db = lancedb.connect(uri=str(LANCEDB_DIR))
table = vector_db.open_table(LANCEDB_TABLE_NAME)

# Embedder (must match ingestion)
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

# LLM agent
rag_agent = Agent(
    model="google-gla:gemini-2.5-flash",
    retries=2,
    system_prompt=(
        "You are a friendly YouTuber and data engineering teacher. "
        "You answer questions based only on the retrieved transcript chunks "
        "from your YouTube lectures.\n\n"
        "Guidelines:\n"
        "- Always base your answer on the provided transcript content.\n"
        "- You may use your own expertise to clarify and structure the answer, "
        "  but do NOT invent facts that are not supported by the transcripts.\n"
        "- If the user asks something outside the retrieved knowledge, say you "
        "  cannot answer based on the course videos.\n"
        "- Keep answers clear and concise, maximum 6 sentences.\n"
        "- In the final answer, clearly mention which transcript source ids "
        "  you used (video_id#chunk_id).\n"
    ),
    output_type=RagResponse,
)


@rag_agent.tool_plain
def retrieve_top_chunks(query: str, k: int = 3) -> str:
    """
    Uses vector search to find the closest k matching transcript chunks to the query.
    Returns a formatted text block that the agent can use as context.
    """
    # Convert query -> vector (must match ingestion embedding model)
    query_vec = embedder.encode(query)

    # Search using the correct vector column
    results = table.search(query_vec, vector_column_name=VECTOR_COL).limit(k).to_list()

    if not results:
        return "No matching transcript chunks were found in the database."

    contexts = []
    for i, row in enumerate(results, start=1):
        contexts.append(
            f"--- Chunk {i} ---\n"
            f"Source: {row.get('video_id')}#{row.get('chunk_id')}\n"
            f"Content:\n{row.get('text', '')}\n"
        )

    return "\n".join(contexts)


def chat_once(question: str) -> RagResponse:
    """
    Helper for FastAPI (sync).
    """
    result = rag_agent.run_sync(question)
    return result.output


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        user_q = " ".join(sys.argv[1:])
    else:
        user_q = input("Ask the YouTuber a question about the videos: ")

    r = chat_once(user_q)
    print("\n--- ANSWER ---")
    print(r.answer)
    # These fields depend on your RagResponse model; keep if they exist there.
    print("\nSource filename:", getattr(r, "filename", "<n/a>"))
    print("Source filepath:", getattr(r, "filepath", "<n/a>"))
