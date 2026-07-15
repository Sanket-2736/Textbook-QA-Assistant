"""RAG chain for Q&A using LCEL (LangChain Expression Language).

Phase 2: Retriever + Prompt + Cerebras LLM chain for question answering.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from app.embeddings import get_embeddings
from app.llm import get_llm
from app.vectorstore import get_vectorstore

load_dotenv()


def format_docs(docs: list) -> str:
    """Format retrieved documents for the prompt.

    Args:
        docs: List of retrieved Document objects

    Returns:
        Formatted string with page numbers and content
    """
    if not docs:
        return "No relevant excerpts found in the textbook."

    formatted = []
    for i, doc in enumerate(docs, 1):
        page_num = doc.metadata.get("page_number", "Unknown")
        section = doc.metadata.get("heading", "")
        content = doc.page_content

        # Build excerpt header
        header = f"Excerpt {i} (Page {page_num}"
        if section:
            header += f", Section: {section}"
        header += "):"

        formatted.append(f"{header}\n{content}")

    return "\n\n---\n\n".join(formatted)


def build_rag_chain(
    index_name: str,
    embedding_provider: Optional[str] = None,
    top_k: int = 4,
    llm_model: str = "llama-3.1-70b",
    llm_temperature: float = 0.3,
    namespace: str = "",
):
    """
    Build LCEL RAG chain with Pinecone retriever and Cerebras LLM.

    Args:
        index_name: Pinecone index name
        embedding_provider: "openai" or "local" (default: env var)
        top_k: Number of documents to retrieve (default: 4)
        llm_model: Cerebras model name
        llm_temperature: LLM temperature (0-1, lower = more deterministic)
        namespace: Pinecone namespace

    Returns:
        Runnable LCEL chain

    Raises:
        ValueError: If required API keys are missing
    """
    # Initialize embeddings
    embeddings = get_embeddings(provider=embedding_provider)

    # Get vectorstore and create retriever
    vectorstore = get_vectorstore(
        index_name=index_name,
        embeddings=embeddings,
        namespace=namespace,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    # Initialize LLM
    llm = get_llm(model=llm_model, temperature=llm_temperature)

    # Define the prompt template
    prompt = ChatPromptTemplate.from_template(
        """You are an expert tutor answering questions about a textbook.

Your instructions:
1. Answer ONLY based on the provided textbook excerpts below.
2. If the excerpts contain relevant information, provide a clear, concise answer.
3. ALWAYS cite the page number and section (if available) for your answer.
   Format citations as: "(Page X, Section: Y)" or "(Page X)"
4. If the excerpts do NOT contain information to answer the question, respond with:
   "I cannot find this information in the provided textbook excerpts."
5. Do not make up information or use knowledge outside the provided excerpts.
6. Be conversational but academic in tone.

TEXTBOOK EXCERPTS:
{context}

QUESTION: {question}

ANSWER:"""
    )

    # Build LCEL chain: retriever -> format docs -> prompt -> llm -> output parser
    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever


def ask_question(
    question: str,
    index_name: str = "textbook-qa",
    embedding_provider: Optional[str] = None,
    top_k: int = 4,
    namespace: str = "",
    verbose: bool = False,
) -> dict:
    """
    Ask a question against the ingested textbook and get answer with sources.

    Args:
        question: The question to ask
        index_name: Pinecone index name (default: "textbook-qa")
        embedding_provider: "openai" or "local" (default: env var)
        top_k: Number of source excerpts to retrieve (default: 4)
        namespace: Pinecone namespace
        verbose: Print debug information

    Returns:
        Dict with keys:
        - "answer": The LLM response
        - "sources": List of source dicts with page and text
        - "num_sources": Number of sources retrieved

    Raises:
        ValueError: If API keys or index are not available
    """
    if verbose:
        print(f"Building RAG chain for index: {index_name}")

    # Build chain
    chain, retriever = build_rag_chain(
        index_name=index_name,
        embedding_provider=embedding_provider,
        top_k=top_k,
        namespace=namespace,
    )

    if verbose:
        print(f"Retrieving top {top_k} documents...")

    # Retrieve source documents
    try:
        retrieved_docs = retriever.invoke(question)
    except Exception as e:
        raise ValueError(f"Failed to retrieve documents: {e}")

    if verbose:
        print(f"Retrieved {len(retrieved_docs)} documents")
        print(f"Asking question: {question}")

    # Get answer from chain
    try:
        answer = chain.invoke(question)
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
        "num_sources": len(sources),
        "question": question,
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
    """Test script: ask a sample question."""
    import json

    # Check if we have an index with data
    index_name = os.getenv("PINECONE_INDEX_NAME", "textbook-qa")

    print("=" * 60)
    print("RAG Chain Test")
    print("=" * 60)
    print(f"Index: {index_name}\n")

    test_questions = [
        "What is the main topic of this textbook?",
        "Explain the key concepts covered in chapter 1.",
        "How does this textbook approach problem-solving?",
    ]

    try:
        for question in test_questions:
            print(f"Q: {question}")
            print("-" * 60)

            try:
                result = ask_question(
                    question=question,
                    index_name=index_name,
                    verbose=False,
                )

                print(f"A: {result['answer']}\n")

                if result["num_sources"] > 0:
                    print(f"Sources ({result['num_sources']}):")
                    for source in result["sources"]:
                        print(f"  - Page {source['page']}: {source['text'][:80]}...")
                else:
                    print("No sources found.")

                print("\n" + "=" * 60 + "\n")

            except ValueError as e:
                print(f"Error: {e}\n")

    except Exception as e:
        print(f"Fatal error: {e}")
        print("\nNote: To test this, first ingest a PDF using:")
        print(f"  python -m app.ingest --file mybook.pdf --index {index_name}")
