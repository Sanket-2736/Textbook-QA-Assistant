"""PDF ingestion pipeline for textbook Q&A RAG system.

Phase 1: Load PDFs, extract metadata, chunk, embed, and upsert to Pinecone.
"""

import os
import re
from pathlib import Path
from typing import List, Optional

import click
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.embeddings import get_embeddings
from app.vectorstore import get_vectorstore, init_pinecone_index

load_dotenv()


def extract_metadata(loader: PyPDFLoader) -> tuple[int, dict]:
    """
    Extract and attach metadata to documents.

    Args:
        loader: PyPDFLoader instance

    Returns:
        Tuple of (num_pages, metadata_dict)
    """
    # Get PDF info
    pdf_path = loader.file_path
    filename = Path(pdf_path).name

    # Get page count
    try:
        num_pages = len(loader.pages)
    except Exception:
        num_pages = 0

    metadata = {
        "source": str(pdf_path),
        "filename": filename,
    }

    return num_pages, metadata


def detect_heading_level(text: str, page_index: int) -> Optional[str]:
    """
    Best-effort detection of chapter/section heading from text patterns.

    Looks for:
    - Lines starting with "Chapter", "Section", "Part"
    - All-caps lines (often headings)
    - Lines shorter than 100 chars and with Title Case

    Args:
        text: Text content to analyze
        page_index: Page number for context

    Returns:
        Detected heading or None
    """
    lines = text.strip().split("\n")

    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if not line or len(line) < 5 or len(line) > 100:
            continue

        # Match explicit heading keywords
        if re.match(r"^(Chapter|Section|Part|Article|Unit)\s+\d+", line, re.IGNORECASE):
            return line

        # Match all-caps headings (often chapter titles)
        if line.isupper() and len(line) > 5:
            return line

        # Match Title Case headings (3+ words, each capitalized)
        if (
            re.match(r"^([A-Z][a-z]*\s+)+[A-Z][a-z]*", line)
            and len(line.split()) >= 2
            and len(line) < 80
        ):
            return line

    return None


def load_and_chunk_pdf(
    pdf_path: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> tuple[List, int]:
    """
    Load PDF and chunk content with metadata.

    Args:
        pdf_path: Path to PDF file
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks

    Returns:
        Tuple of (documents_with_metadata, num_pages)

    Raises:
        FileNotFoundError: If PDF doesn't exist
        ValueError: If PDF cannot be loaded
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Load PDF
    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
    except Exception as e:
        raise ValueError(f"Failed to load PDF: {e}")

    if not pages:
        raise ValueError(f"No pages found in PDF: {pdf_path}")

    num_pages = len(pages)

    # Add enhanced metadata to each page
    filename = pdf_file.name
    for page_idx, page in enumerate(pages):
        page.metadata.update({
            "filename": filename,
            "source": str(pdf_path),
            "page_number": page_idx + 1,
            "total_pages": num_pages,
        })

        # Attempt to extract heading
        heading = detect_heading_level(page.page_content, page_idx)
        if heading:
            page.metadata["heading"] = heading

    # Chunk text
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(pages)

    # Ensure each chunk has complete metadata
    for chunk_idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = chunk_idx

    return chunks, num_pages


def ingest_pdf_to_pinecone(
    pdf_path: str,
    index_name: str,
    namespace: str = "",
    embedding_provider: Optional[str] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    verbose: bool = True,
) -> dict:
    """
    Full ingestion pipeline: load PDF, chunk, embed, and upsert to Pinecone.

    Args:
        pdf_path: Path to PDF file
        index_name: Pinecone index name
        namespace: Pinecone namespace (optional)
        embedding_provider: "openai" or "local" (default: env var or "openai")
        chunk_size: Chunk size for splitting
        chunk_overlap: Overlap between chunks
        verbose: Print progress messages

    Returns:
        Summary dict with statistics

    Raises:
        FileNotFoundError: If PDF doesn't exist
        ValueError: If ingestion fails
    """
    if verbose:
        click.echo(f"📖 Loading PDF: {pdf_path}")

    # Load and chunk PDF
    chunks, num_pages = load_and_chunk_pdf(pdf_path, chunk_size, chunk_overlap)
    num_chunks = len(chunks)

    if verbose:
        click.echo(f"   ✓ Pages: {num_pages}")
        click.echo(f"   ✓ Chunks: {num_chunks}")

    # Initialize embeddings
    if verbose:
        click.echo("🔧 Initializing embeddings...")
    embeddings = get_embeddings(provider=embedding_provider)

    # Initialize Pinecone index
    if verbose:
        click.echo(f"📌 Ensuring Pinecone index exists: {index_name}")
    try:
        # Determine dimension from embeddings
        test_embedding = embeddings.embed_query("test")
        dimension = len(test_embedding)
        init_pinecone_index(index_name, dimension=dimension)
    except Exception as e:
        if verbose:
            click.echo(f"   ℹ️  Index check: {e}")
        # Continue anyway - index might already exist

    # Get vectorstore
    if verbose:
        click.echo("🔗 Connecting to vectorstore...")
    vectorstore = get_vectorstore(index_name, embeddings, namespace=namespace)

    # Upsert chunks
    if verbose:
        click.echo(f"⬆️  Upserting {num_chunks} chunks...")

    try:
        # Prepare texts and metadatas
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        # Generate IDs based on source, page, and chunk index
        ids = []
        for chunk in chunks:
            page_num = chunk.metadata.get("page_number", 0)
            chunk_idx = chunk.metadata.get("chunk_index", 0)
            doc_id = f"{chunk.metadata['filename']}_p{page_num}_c{chunk_idx}"
            ids.append(doc_id)

        # Upsert to vectorstore
        upserted_ids = vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        upsert_count = len(upserted_ids) if upserted_ids else len(ids)

        if verbose:
            click.echo(f"   ✓ Successfully upserted {upsert_count} chunks")

    except Exception as e:
        raise ValueError(f"Failed to upsert to Pinecone: {e}")

    # Summary
    summary = {
        "pdf_path": str(pdf_path),
        "num_pages": num_pages,
        "num_chunks": num_chunks,
        "upsert_count": upsert_count,
        "index_name": index_name,
        "namespace": namespace,
    }

    if verbose:
        click.echo("\n" + "=" * 50)
        click.echo("✅ Ingestion Complete!")
        click.echo("=" * 50)
        click.echo(f"PDF:            {Path(pdf_path).name}")
        click.echo(f"Pages:          {num_pages}")
        click.echo(f"Chunks:         {num_chunks}")
        click.echo(f"Upserted:       {upsert_count}")
        click.echo(f"Index:          {index_name}")
        if namespace:
            click.echo(f"Namespace:      {namespace}")
        click.echo("=" * 50)

    return summary


@click.command()
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True),
    required=True,
    help="Path to PDF file to ingest",
)
@click.option(
    "--index",
    "-i",
    type=str,
    default="textbook-qa",
    help="Pinecone index name (default: textbook-qa)",
)
@click.option(
    "--namespace",
    "-n",
    type=str,
    default="",
    help="Pinecone namespace (optional)",
)
@click.option(
    "--embedding-provider",
    "-e",
    type=click.Choice(["openai", "local"]),
    default=None,
    help="Embedding provider (default: EMBEDDING_PROVIDER env var or openai)",
)
@click.option(
    "--chunk-size",
    type=int,
    default=800,
    help="Chunk size in characters (default: 800)",
)
@click.option(
    "--chunk-overlap",
    type=int,
    default=100,
    help="Chunk overlap in characters (default: 100)",
)
def main(
    file: str,
    index: str,
    namespace: str,
    embedding_provider: Optional[str],
    chunk_size: int,
    chunk_overlap: int,
):
    """Ingest PDF into Pinecone vector store for Q&A RAG."""
    try:
        ingest_pdf_to_pinecone(
            pdf_path=file,
            index_name=index,
            namespace=namespace,
            embedding_provider=embedding_provider,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            verbose=True,
        )
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
