from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.rag import ask


app = FastAPI(
    title="Enterprise RAG Knowledge Assistant",
    description=(
        "RAG-based enterprise knowledge assistant using "
        "Azure OpenAI and Azure AI Search."
    ),
    version="1.0.0"
)


class ChatMessage(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="User question"
    )

    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Optional recent conversation history"
    )


class SourceResponse(BaseModel):
    chunk_id: str | None = None
    document_name: str | None = None
    department: str | None = None
    section: str | None = None
    effective_year: int | None = None
    is_current: bool | None = None


class UsageResponse(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AskResponse(BaseModel):
    question: str
    rewritten_question: str | None = None
    answer: str
    sources: list[SourceResponse]
    usage: UsageResponse | None = None


def serialize_sources(sources):

    serialized = []

    for source in sources:

        serialized.append(
            {
                "chunk_id": source.get("chunk_id"),
                "document_name": source.get("document_name"),
                "department": source.get("department"),
                "section": source.get("section"),
                "effective_year": source.get("effective_year"),
                "is_current": source.get("is_current")
            }
        )

    return serialized


@app.get("/")
def root():

    return {
        "service": "Enterprise RAG Knowledge Assistant",
        "status": "running"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.post(
    "/ask",
    response_model=AskResponse
)
def ask_question(
    request: AskRequest
):

    try:

        history = [
            message.model_dump()
            for message in request.history
        ]

        result = ask(
            question=request.question,
            history=history
        )

        return {
            "question": result["question"],
            "rewritten_question": result.get(
                "rewritten_question"
            ),
            "answer": result["answer"],
            "sources": serialize_sources(
                result.get("sources", [])
            ),
            "usage": result.get("usage")
        }

    except Exception as exc:

        print(
            "API ERROR:",
            repr(exc)
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process RAG request."
        ) from exc