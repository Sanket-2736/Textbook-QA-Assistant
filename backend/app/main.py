import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ingest import ingest_pdf_to_pinecone
from app.rag_chain import ask_question, build_rag_chain

app = FastAPI(
    title="Textbook Q&A RAG",
    description="Interactive Q&A system for textbooks using RAG",
    version="0.1.0",
)

# Add CORS middleware for Vite frontend (http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Models ====================

class QuestionRequest(BaseModel):
    """Request model for asking a question."""
    question: str
    index_name: str = "textbook-qa"
    top_k: int = 4
    namespace: str = ""


class QuestionResponse(BaseModel):
    """Response model for question with sources."""
    answer: str
    sources: list
    num_sources: int
    question: str


class UploadResponse(BaseModel):
    """Response model for PDF upload."""
    filename: str
    num_pages: int
    num_chunks: int
    upsert_count: int
    index_name: str
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str
    version: str


# ==================== Endpoints ====================

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Textbook Q&A RAG API is running",
        version="0.1.0",
    )


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    index_name: str = "textbook-qa",
    namespace: str = "",
):
    """
    Upload and ingest a PDF file.

    - **file**: PDF file to upload
    - **index_name**: Pinecone index name (default: "textbook-qa")
    - **namespace**: Optional Pinecone namespace

    Returns:
        Upload summary with page count, chunk count, and upsert count
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    if not file.content_type or "pdf" not in file.content_type:
        raise HTTPException(status_code=400, detail="Invalid content type")

    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
            dir=None,
        ) as tmp_file:
            tmp_path = tmp_file.name

        # Write file contents async
        try:
            content = await file.read()
            async with aiofiles.open(tmp_path, "wb") as f:
                await f.write(content)

            # Run ingestion pipeline (blocking but in executor)
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None,
                ingest_pdf_to_pinecone,
                tmp_path,
                index_name,
                namespace,
                None,  # embedding_provider (use env var)
                800,  # chunk_size
                100,  # chunk_overlap
                False,  # verbose
            )

            return UploadResponse(
                filename=file.filename,
                num_pages=summary["num_pages"],
                num_chunks=summary["num_chunks"],
                upsert_count=summary["upsert_count"],
                index_name=index_name,
                message=f"Successfully ingested {file.filename}",
            )

        finally:
            # Clean up temp file
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/ask", response_model=QuestionResponse)
async def ask(request: QuestionRequest) -> QuestionResponse:
    """
    Ask a question and get answer with sources.

    - **question**: The question to ask
    - **index_name**: Pinecone index to query
    - **top_k**: Number of source documents to retrieve
    - **namespace**: Optional Pinecone namespace

    Returns:
        Answer with source documents and page numbers
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Run Q&A in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            ask_question,
            request.question,
            request.index_name,
            None,  # embedding_provider
            request.top_k,
            request.namespace,
            False,  # verbose
        )

        return QuestionResponse(
            answer=result["answer"],
            sources=result["sources"],
            num_sources=result["num_sources"],
            question=result["question"],
        )

    except ValueError as e:
        if "retrieve" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Index not found or empty. Please upload a PDF first: {str(e)}",
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")


@app.post("/ask/stream")
async def ask_stream(request: QuestionRequest):
    """
    Stream answer tokens via Server-Sent Events.

    Uses LangChain's async streaming to support real-time token generation
    from Cerebras LLM.

    - **question**: The question to ask
    - **index_name**: Pinecone index to query
    - **top_k**: Number of source documents to retrieve
    - **namespace**: Optional Pinecone namespace

    Returns:
        Server-Sent Events stream of answer tokens
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    async def generate():
        """Generator for SSE streaming."""
        try:
            # Build the RAG chain
            chain, retriever = build_rag_chain(
                index_name=request.index_name,
                embedding_provider=None,
                top_k=request.top_k,
                namespace=request.namespace,
            )

            # Retrieve sources first
            try:
                retrieved_docs = retriever.invoke(request.question)
            except Exception as e:
                yield f"data: {{'error': 'Failed to retrieve documents: {str(e)}'}}\n\n"
                return

            # Send initial event with sources
            sources = []
            for doc in retrieved_docs:
                page = doc.metadata.get("page_number", "Unknown")
                section = doc.metadata.get("heading", "")
                text = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                sources.append({"page": page, "section": section, "text": text})

            yield f"data: {{'type': 'sources', 'count': {len(sources)}, 'sources': {sources}}}\n\n"

            # Stream answer tokens
            try:
                async for token in chain.astream(request.question):
                    if token:
                        # Escape for SSE
                        escaped_token = token.replace("\n", "\\n").replace('"', '\\"')
                        yield f"data: {{'type': 'token', 'text': '{escaped_token}'}}\n\n"
                        await asyncio.sleep(0)  # Allow other tasks to run

            except Exception as e:
                yield f"data: {{'type': 'error', 'message': 'Streaming failed: {str(e)}'}}\n\n"

            # Send completion event
            yield f"data: {{'type': 'done'}}\n\n"

        except Exception as e:
            yield f"data: {{'type': 'error', 'message': '{str(e)}'}}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ==================== Root & Info ====================

@app.get("/")
async def root():
    """API root with documentation links."""
    return {
        "status": "ok",
        "message": "Textbook Q&A RAG API is running",
        "documentation": "/docs",
        "endpoints": {
            "health": "GET /health",
            "upload_pdf": "POST /upload",
            "ask_question": "POST /ask",
            "ask_streaming": "POST /ask/stream",
        },
    }


# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Generic exception handler."""
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "status_code": 500,
    }
