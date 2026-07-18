import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings import get_embeddings
from app.llm import invoke_llm
from app.models import ChatMessage, ChatSession
from app.vectorstore import get_vectorstore

load_dotenv()


def format_docs(docs: list) -> str:
    if not docs:
        return "No relevant excerpts found in the textbook."

    formatted = []
    for i, doc in enumerate(docs, 1):
        page_num = doc.metadata.get("page_number", "Unknown")
        section = doc.metadata.get("heading", "")
        content = doc.page_content

        header = f"Excerpt {i} (Page {page_num}"
        if section:
            header += f", Section: {section}"
        header += "):"

        formatted.append(f"{header}\n{content}")

    return "\n\n---\n\n".join(formatted)


async def get_session_history(
    db: AsyncSession,
    session_id: int,
    num_turns: int = 6,
) -> list[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(num_turns)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()
    # Reverse to get chronological order
    return list(reversed(messages))


def format_conversation_context(messages: list[ChatMessage]) -> str:
    if not messages:
        return "[No prior conversation]"

    formatted = []
    for msg in messages[-4:]:  # Last 2 turns = 4 messages (2 user, 2 assistant)
        role_label = "You" if msg.role == "user" else "Assistant"
        formatted.append(f"{role_label}: {msg.content[:200]}")  # Truncate for brevity

    return "\n".join(formatted)


async def condense_question(
    question: str,
    session_history: list[ChatMessage],
) -> str:
    if not session_history:
        # First turn: no condensation needed
        return question

    # Format history for condensation prompt
    history_text = "\n".join(
        [f"{msg.role}: {msg.content}" for msg in session_history[-4:]]
    )

    # Build condensation prompt manually
    condensation_prompt = """Given the following conversation history and a follow-up question, 
rewrite the follow-up question as a standalone, self-contained question that 
captures all the context needed to find relevant textbook excerpts.

Keep the rewritten question concise and focused on what was asked.

Conversation history:
{history}

Follow-up question: {question}

Rewritten standalone question:"""

    prompt = condensation_prompt.format(
        history=history_text,
        question=question,
    )

    # Call Cerebras LLM directly
    standalone_question = invoke_llm(
        prompt=prompt,
        model="gpt-oss-120b",
        temperature=0.1,  # Lower temp for consistent condensation
    )

    print(f"\n[Query Condensation]")
    print(f"Original question: {question}")
    print(f"Standalone question: {standalone_question}")
    print()

    return standalone_question


async def ask_question(
    question: str,
    session_id: int,
    textbook_id: int,
    db: AsyncSession,
    index_name: str = "textbook-qa",
    embedding_provider: Optional[str] = None,
    top_k: int = 4,
    namespace: str = "",
    verbose: bool = False,
) -> dict:
    if verbose:
        print(f"Session ID: {session_id}, Textbook ID: {textbook_id}")
        print(f"Retrieving chat history...")

    # Fetch prior messages in this session
    try:
        session_history = await get_session_history(db, session_id, num_turns=6)
    except Exception as e:
        if verbose:
            print(f"Warning: Could not fetch session history: {e}")
        session_history = []

    # Step 1: Condense the question using chat history
    if verbose:
        print("Condensing question...")

    standalone_question = await condense_question(question, session_history)

    # Step 2: Set up retriever for the specified index
    if verbose:
        print(f"Setting up retriever for index: {index_name}")

    embeddings = get_embeddings(provider=embedding_provider)
    vectorstore = get_vectorstore(
        index_name=index_name,
        embeddings=embeddings,
        namespace=namespace,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    try:
        retrieved_docs = retriever.invoke(standalone_question)
        unique_docs = []
        seen = set()

        for doc in retrieved_docs:
            key = (
                doc.metadata.get("page_number"),
                doc.page_content[:100]
            )

            if key not in seen:
                seen.add(key)
                unique_docs.append(doc)

        retrieved_docs = unique_docs
    except Exception as e:
        raise ValueError(f"Failed to retrieve documents: {e}")

    if verbose:
        print(f"Retrieved {len(retrieved_docs)} documents")

    # Step 3: Format conversation context (last 2 turns for tone/continuity)
    conversation_context = format_conversation_context(session_history)

    # Step 4: Generate answer using retrieved docs and conversation context
    try:
        # Format the retrieved documents
        formatted_docs = format_docs(retrieved_docs)

        # Build the complete prompt manually
        rag_prompt = """
        You are an intelligent AI tutor helping users understand textbook content.

        Your primary responsibility is to answer using the provided textbook excerpts.

        Instructions:

        1. Use the textbook excerpts as the PRIMARY source of information.

        2. If the textbook contains enough information, answer clearly in your own words instead of copying sentences verbatim.

        3. If the textbook explanation is brief or incomplete, you MAY add a small amount of accurate background knowledge based on your general understanding to improve clarity.

        4. Any additional knowledge must:
           - support the textbook,
           - never contradict the textbook,
           - never introduce speculative or false information.

        5. If the textbook contains no relevant information, respond:
           "I cannot find sufficient information in the provided textbook excerpts."
           Then, optionally provide a brief general explanation and clearly state that it is based on general knowledge rather than the textbook.

        6. Write naturally, as if teaching a student.

        7. Prefer explanations over definitions.

        8. Use examples whenever they improve understanding.

        9. Do NOT mention "According to the excerpts" or "Based on the provided context" repeatedly. Write naturally.

        10. Keep answers concise but sufficiently descriptive (150–300 words unless the question requires otherwise).

        11. At the end, provide textbook citations.

        Citation format:
        (Page X)
        or
        (Page X, Section: Y)

        Conversation Context:
        {conversation_context}

        Relevant Textbook Excerpts:
        {formatted_docs}

        Question:
        {question}

        Answer:
        """

        prompt = rag_prompt.format(
            conversation_context=conversation_context,
            formatted_docs=formatted_docs,
            question=question,
        )

        # Call Cerebras LLM directly
        answer = invoke_llm(
            prompt=prompt,
            model="gpt-oss-120b",
            temperature=0.3,
        )

    except Exception as e:
        raise ValueError(f"Failed to generate answer: {e}")

    # Format sources
    sources = []
    for doc in retrieved_docs:
        page = doc.metadata.get("page_number", "Unknown")
        section = doc.metadata.get("heading", "")
        text = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content

        source_entry = {
            "page": page,
            "text": text,
        }
        if section:
            source_entry["section"] = section

        sources.append(source_entry)

    result = {
        "answer": answer,
        "sources": sources,
        "standalone_question": standalone_question,
        "num_sources": len(sources),
        "question": question,
        "session_id": session_id,
    }

    if verbose:
        print(f"\nAnswer:\n{answer}\n")
        print(f"Sources ({len(sources)}):")
        for i, source in enumerate(sources, 1):
            print(f"  {i}. Page {source['page']}")
            if "section" in source:
                print(f"     Section: {source['section']}")
            print(f"     Text: {source['text']}\n")

    return result


if __name__ == "__main__":
    import asyncio

    print("=" * 60)
    print("RAG Chain Test (Conversational)")
    print("=" * 60)
    print("\nNote: This test requires a running database and ingested textbook.")
    print("Use the main.py endpoints for end-to-end testing with auth.")
