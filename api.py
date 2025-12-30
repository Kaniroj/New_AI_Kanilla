from fastapi import FastAPI
from backend.rag import rag_agent
from backend.data_models import Prompt

app = FastAPI(title="RAG Youtuber API")

@app.get("/")
def root():
    return {"status": "ok", "message": "RAG Youtuber API is running"}

@app.post("/rag/query")
async def query_documentation(query: Prompt):
    result = await rag_agent.run(query.prompt)
    return {
        "answer": result.output
    }
