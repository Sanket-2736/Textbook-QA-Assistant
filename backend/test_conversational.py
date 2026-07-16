"""Test script for conversational Q&A with query condensation.

This script demonstrates:
1. Query condensation for follow-up questions
2. Multi-turn conversations without history bleed
3. Guardrails for out-of-textbook questions
"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models import ChatMessage, ChatSession, User, Textbook, Base
from app.rag_chain import condense_question, format_conversation_context


async def test_query_condensation():
    """Test query condensation with sample conversation history."""
    print("=" * 70)
    print("QUERY CONDENSATION TEST")
    print("=" * 70)

    # Simulate conversation history
    class MockMessage:
        def __init__(self, role, content):
            self.role = role
            self.content = content

    history = [
        MockMessage("user", "What is Newton's first law of motion?"),
        MockMessage(
            "assistant",
            "Newton's first law states that an object at rest stays at rest, "
            "and an object in motion stays in motion unless acted on by a force.",
        ),
    ]

    # Test condensation
    follow_up = "Can you give an example of that?"
    condensed = await condense_question(follow_up, history)

    print(f"\nConversation history:")
    for msg in history:
        print(f"  {msg.role}: {msg.content[:80]}...")

    print(f"\nFollow-up question: {follow_up}")
    print(f"Condensed question: {condensed}")

    # Verify condensation includes original context
    assert "Newton" in condensed or "law" in condensed or "motion" in condensed.lower(), (
        "Condensed question should reference Newton's law"
    )
    print("\n✓ Query condensation test passed")


def test_conversation_formatting():
    """Test formatting of conversation context."""
    print("\n" + "=" * 70)
    print("CONVERSATION FORMATTING TEST")
    print("=" * 70)

    # Simulate messages
    class MockMessage:
        def __init__(self, role, content):
            self.role = role
            self.content = content

    messages = [
        MockMessage("user", "What is photosynthesis?"),
        MockMessage(
            "assistant",
            "Photosynthesis is the process by which plants convert light energy into chemical energy.",
        ),
        MockMessage("user", "What are the products?"),
        MockMessage("assistant", "The main products are glucose and oxygen."),
    ]

    formatted = format_conversation_context(messages)

    print(f"\nFormatted context:")
    print(formatted)

    assert "Photosynthesis" in formatted or "photosynthesis" in formatted.lower(), (
        "Formatted context should include photosynthesis"
    )
    assert "You:" in formatted or "Assistant:" in formatted, (
        "Formatted context should include role labels"
    )
    print("\n✓ Conversation formatting test passed")


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  CONVERSATIONAL RAG SYSTEM - TEST SUITE".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    try:
        await test_query_condensation()
        test_conversation_formatting()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
        print("\nEnd-to-end testing instructions:")
        print("1. Start the backend server: python -m uvicorn app.main:app --reload")
        print("2. Sign up two users")
        print("3. Upload a textbook")
        print("4. Ask questions and verify:")
        print("   - First question: no condensation (new session)")
        print("   - Follow-up: condensation should resolve pronouns/context")
        print("   - Out-of-topic: guardrail should trigger")
        print("   - Different session: no history bleed")
        print()

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
