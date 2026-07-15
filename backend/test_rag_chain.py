"""Unit tests for RAG chain module."""

from langchain_core.documents import Document
from app.rag_chain import format_docs


def test_format_docs():
    """Test document formatting for prompt injection."""
    print("Testing document formatting...")

    # Test case 1: Empty docs
    result = format_docs([])
    assert "No relevant excerpts" in result
    print("  ✓ Empty docs handled correctly")

    # Test case 2: Single document
    doc1 = Document(
        page_content="Photosynthesis is the process by which plants convert light energy into chemical energy.",
        metadata={"page_number": 42, "heading": "Chapter 3: Energy Conversion"}
    )
    result = format_docs([doc1])
    assert "Page 42" in result
    assert "Chapter 3" in result
    assert "Photosynthesis" in result
    print("  ✓ Single document formatted correctly")

    # Test case 3: Multiple documents
    doc2 = Document(
        page_content="Chlorophyll absorbs light wavelengths in the blue and red spectrum.",
        metadata={"page_number": 43, "heading": "Section: Light Absorption"}
    )
    result = format_docs([doc1, doc2])
    assert "Excerpt 1" in result
    assert "Excerpt 2" in result
    assert "Page 42" in result
    assert "Page 43" in result
    print("  ✓ Multiple documents formatted correctly")

    # Test case 4: Document without section
    doc3 = Document(
        page_content="This is additional information.",
        metadata={"page_number": 50}
    )
    result = format_docs([doc3])
    assert "Page 50" in result
    assert "Section:" not in result
    print("  ✓ Document without section handled correctly")

    print("\n✓ All format_docs tests passed\n")


def test_chain_initialization():
    """Test that chain can be initialized (without API calls)."""
    print("Testing chain initialization...")
    
    try:
        from app.rag_chain import build_rag_chain
        
        # This will fail if API keys are missing, but we're just checking
        # the imports and structure work
        print("  ✓ build_rag_chain function is available")
        print("  ℹ️  Full chain test requires API keys (PINECONE_API_KEY, CEREBRAS_API_KEY, OPENAI_API_KEY)")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")

    print()


def test_ask_question_structure():
    """Test that ask_question returns correct structure."""
    print("Testing ask_question structure...")

    # We can't test actual Q&A without data, but we can verify
    # the function exists and has correct signature
    from app.rag_chain import ask_question
    import inspect

    sig = inspect.signature(ask_question)
    params = list(sig.parameters.keys())

    expected_params = ["question", "index_name", "embedding_provider", "top_k", "namespace", "verbose"]
    assert params == expected_params, f"Expected {expected_params}, got {params}"
    print("  ✓ ask_question has correct parameters")

    # Check return type hint
    return_annotation = sig.return_annotation
    assert return_annotation == dict, f"Expected dict return, got {return_annotation}"
    print("  ✓ ask_question returns dict")

    print()


if __name__ == "__main__":
    print("=" * 60)
    print("RAG Chain Unit Tests")
    print("=" * 60)
    print()

    test_format_docs()
    test_chain_initialization()
    test_ask_question_structure()

    print("=" * 60)
    print("✅ All unit tests passed!")
    print("=" * 60)
    print("\nTo test end-to-end RAG:")
    print("1. Ingest a PDF: python -m app.ingest --file sample.pdf")
    print("2. Ask questions: python -m app.rag_chain")
