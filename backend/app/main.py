"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Textbook Q&A RAG",
    description="Interactive Q&A system for textbooks using RAG",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Textbook Q&A RAG API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
