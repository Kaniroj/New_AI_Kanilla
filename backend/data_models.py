from pydantic import BaseModel, Field


class Prompt(BaseModel):
    prompt: str = Field(description="User question")


class RagResponse(BaseModel):
    answer: str = Field(description="Answer based on retrieved transcript chunks")
    sources: list[str] = Field(
        default_factory=list,
        description="List of sources used, format: video_id#chunk_id",
    )
