"""FastAPI application with multi-tenant auth, database persistence, and conversational RAG.

Endpoints:
- POST /auth/signup, /auth/login — User authentication with JWT
- POST /upload — Upload and ingest PDF (auth required)
- GET /textbooks — List user's textbooks (auth required)
- DELETE /textbooks/{id} — Delete textbook (auth required)
- POST /ask — Ask question with conversational context (auth required)
- POST /ask/stream — Stream answer via SSE (auth required)
- GET /sessions?textbook_id=... — List chat sessions (auth required)
- GET /sessions/{id}/messages — Get full message history (auth required)
- GET /health — Health check
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.auth_routes import router as auth_router
from app.database import get_db, init_db, close_db
from app.embeddings import get_embeddings
from app.models import ChatMessage, ChatSession, Textbook, User
from app.rag_chain import ask_question
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="Textbook Q&A RAG",
    description="Multi-tenant interactive Q&A system for textbooks",
    version="0.2.0",
)

# CORS middleware for Vite frontend
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

# Include auth routes
app.include_router(auth_router)


# ==================== Pydantic Models ====================

class TextbookResponse(BaseModel):
    """Textbook information."""
    id: int
    filename: str
    uploaded_at: str
    page_count: int
    chunk_count: int

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """PDF upload response."""
    filename: str
    num_pages: int
    num_chunks: int
    upsert_count: int
    textbook_id: int
    message: str


class QuestionRequest(BaseModel):
    """Q&A request."""
    question: str
    textbook_id: int
    session_id: Optional[int] = None  # If None, create new session
    top_k: int = 4


class SourceInfo(BaseModel):
    """Source document reference."""
    page: int
    text: str
    section: Optional[str] = None


class QuestionResponse(BaseModel):
    """Q&A response."""
    answer: str
    sources: list[SourceInfo]
    standalone_question: str
    session_id: int
    num_sources: int


class ChatMessageResponse(BaseModel):
    """Chat message in history."""
    id: int
    role: str
    content: str
    sources: Optional[list] = None
    standalone_question: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Chat session information."""
    id: int
    textbook_id: int
    created_at: str
    title: Optional[str] = None

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str
    version: str


# ==================== Event Handlers ====================

@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    """Close database on shutdown."""
    await close_db()


# ==================== Health ====================

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Textbook Q&A RAG API is running",
        version="0.2.0",
    )


@app.get("/")
async def root():
    """API information."""
    return {
        "status": "ok",
        "message": "Textbook Q&A RAG API",
        "documentation": "/docs",
        "version": "0.2.0",
    }


# ==================== Textbook Management ====================

@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and ingest a PDF for the current user."""
    # Import here to defer spacy/thinc loading until needed
    from app.ingest import ingest_pdf_to_pinecone
    
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        # Save temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            content = await file.read()
            async with aiofiles.open(tmp_path, "wb") as f:
                await f.write(content)

            # Create namespace scoped to this textbook
            namespace = f"user_{current_user.id}_textbook_{file.filename}"

            # Run ingestion
            summary = ingest_pdf_to_pinecone(
                pdf_path=tmp_path,
                index_name="textbook-qa",
                namespace=namespace,
                embedding_provider=None,
                chunk_size=800,
                chunk_overlap=100,
                verbose=False,
            )

            # Save textbook record to DB
            textbook = Textbook(
                user_id=current_user.id,
                filename=file.filename,
                pinecone_namespace=namespace,
                page_count=summary["num_pages"],
                chunk_count=summary["num_chunks"],
            )
            db.add(textbook)
            await db.commit()
            await db.refresh(textbook)

            return UploadResponse(
                filename=file.filename,
                num_pages=summary["num_pages"],
                num_chunks=summary["num_chunks"],
                upsert_count=summary["upsert_count"],
                textbook_id=textbook.id,
                message=f"Successfully ingested {file.filename}",
            )

        finally:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/textbooks", response_model=list[TextbookResponse])
async def list_textbooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all textbooks for the current user."""
    stmt = select(Textbook).where(Textbook.user_id == current_user.id)
    result = await db.execute(stmt)
    textbooks = result.scalars().all()
    return textbooks


@app.delete("/textbooks/{textbook_id}")
async def delete_textbook(
    textbook_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a textbook (only if owned by current user)."""
    stmt = select(Textbook).where(
        and_(Textbook.id == textbook_id, Textbook.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    textbook = result.scalar_one_or_none()

    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")

    # TODO: Delete Pinecone namespace here
    await db.delete(textbook)
    await db.commit()

    return {"message": "Textbook deleted", "textbook_id": textbook_id}


# ==================== Q&A with Conversational Support ====================

@app.post("/ask", response_model=QuestionResponse)
async def ask(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ask a question about a textbook (supports follow-ups with context)."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Verify textbook ownership
    stmt = select(Textbook).where(
        and_(Textbook.id == request.textbook_id, Textbook.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    textbook = result.scalar_one_or_none()

    if not textbook:
        raise HTTPException(status_code=403, detail="Access denied: textbook not found")

    # Get or create session
    if request.session_id:
        # Verify session ownership
        stmt = select(ChatSession).where(
            and_(
                ChatSession.id == request.session_id,
                ChatSession.user_id == current_user.id,
                ChatSession.textbook_id == request.textbook_id,
            )
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=403, detail="Access denied: session not found")
    else:
        # Create new session
        session = ChatSession(
            user_id=current_user.id,
            textbook_id=request.textbook_id,
            title=request.question[:100],  # Use first question as title
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    try:
        # Ask question with conversational context
        result = await ask_question(
            question=request.question,
            session_id=session.id,
            textbook_id=request.textbook_id,
            db=db,
            index_name="textbook-qa",
            embedding_provider=None,
            top_k=request.top_k,
            namespace=textbook.pinecone_namespace,
            verbose=False,
        )

        # Save messages to DB
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=request.question,
            standalone_question=result.get("standalone_question"),
        )
        db.add(user_message)

        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=result["answer"],
            sources=result.get("sources"),
        )
        db.add(assistant_message)
        await db.commit()

        return QuestionResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            standalone_question=result.get("standalone_question", request.question),
            session_id=session.id,
            num_sources=result.get("num_sources", 0),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")


@app.post("/ask/stream")
async def ask_stream(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream answer tokens via Server-Sent Events."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Verify textbook ownership
    stmt = select(Textbook).where(
        and_(Textbook.id == request.textbook_id, Textbook.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    textbook = result.scalar_one_or_none()

    if not textbook:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get or create session
    if request.session_id:
        stmt = select(ChatSession).where(
            and_(
                ChatSession.id == request.session_id,
                ChatSession.user_id == current_user.id,
                ChatSession.textbook_id == request.textbook_id,
            )
        )
        result_obj = await db.execute(stmt)
        session = result_obj.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        session = ChatSession(
            user_id=current_user.id,
            textbook_id=request.textbook_id,
            title=request.question[:100],
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    async def generate():
        """SSE generator."""
        try:
            # TODO: Implement streaming with chain.astream()
            yield f"data: {{'type': 'error', 'message': 'Streaming not yet implemented'}}\n\n"
        except Exception as e:
            yield f"data: {{'type': 'error', 'message': '{str(e)}'}}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ==================== Session Management ====================

@app.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    textbook_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List chat sessions for a textbook."""
    # Verify textbook ownership
    stmt = select(Textbook).where(
        and_(Textbook.id == textbook_id, Textbook.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    textbook = result.scalar_one_or_none()

    if not textbook:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get sessions
    stmt = select(ChatSession).where(
        ChatSession.textbook_id == textbook_id
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return sessions


@app.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full message history for a session."""
    # Verify session ownership
    stmt = (
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .options(selectinload(ChatSession.messages))
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Return messages in chronological order
    messages = sorted(session.messages, key=lambda m: m.created_at)
    return messages

# python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000