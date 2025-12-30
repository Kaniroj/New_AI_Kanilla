# backend/app.py

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.rag import chat_once, RagResponse


app = FastAPI(title="RAG YouTuber API",  root_path="/api")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Query(BaseModel):
    question: str


@app.get("/")
def health_check():
    return {"status": "online", "message": "RAG API is running 🎉"}


@app.post("/ask", response_model=RagResponse)
def ask_endpoint(q: Query):
    """
    Main chat endpoint for the RAG bot.
    """
    return chat_once(q.question)
