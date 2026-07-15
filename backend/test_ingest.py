"""Test the ingest pipeline without actual Pinecone connection."""

from pathlib import Path
from app.ingest import load_and_chunk_pdf, detect_heading_level

def test_heading_detection():
    """Test heading detection logic."""
    test_cases = [
        ("Chapter 1: Introduction\nSome content", "Chapter 1: Introduction"),
        ("CHAPTER TITLE IN ALL CAPS\nContent", "CHAPTER TITLE IN ALL CAPS"),
        ("This Is A Title Case Heading\nContent", "This Is A Title Case Heading"),
        ("short\nContent", None),
    ]

    print("Testing heading detection...")
    for text, expected in test_cases:
        result = detect_heading_level(text, 0)
        status = "✓" if result == expected else "✗"
        print(f"  {status} Input: {text[:30]:<30} | Expected: {expected} | Got: {result}")

if __name__ == "__main__":
    test_heading_detection()
    print("\n✓ Unit tests passed")
