# backend/rag.py

from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
import lancedb
from pydantic_ai import Agent

from backend.data_models import RagResponse
from backend.constants import VECTOR_DATABASE_PATH, LANCEDB_TABLE_NAME



vector_db = lancedb.connect(uri=str(VECTOR_DATABASE_PATH))
table = vector_db.open_table(LANCEDB_TABLE_NAME)


#LLM
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
        "- In the final answer, clearly mention which transcript filename(s) "
        "  you used as source.\n"
    ),
    output_type=RagResponse,
)


@rag_agent.tool_plain
def retrieve_top_chunks(query: str, k: int = 3) -> str:
    """
    Uses vector search to find the closest k matching transcript chunks to the query.

    Returns a formatted text block that the agent can use as context.
    """
    results = table.search(query).limit(k).to_list()

    if not results:
        return "No matching transcript chunks were found in the database."

    contexts = []
    for i, row in enumerate(results, start=1):
        contexts.append(
            f"--- Chunk {i} ---\n"
            f"Filename: {row.get('filename', '')}\n"
            f"Filepath: {row.get('filepath', '')}\n"
            f"Content:\n{row.get('content', '')}\n"
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
    print("\nSource filename:", r.filename)
    print("Source filepath:", r.filepath)
