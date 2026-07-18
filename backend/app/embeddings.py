import os
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()


def get_embeddings(provider: Optional[str] = None):
    
    embedding_provider = provider or os.getenv("EMBEDDING_PROVIDER", "local").lower()

    if embedding_provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI embeddings")

        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key,
        )

    elif embedding_provider == "local":
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
            )
        except ImportError:
            raise ImportError(
                "langchain-huggingface and sentence-transformers are required for local embeddings. "
                "Install with: pip install langchain-huggingface sentence-transformers"
            )

    else:
        raise ValueError(
            f"Unknown embedding provider: {embedding_provider}. "
            "Supported providers: 'openai', 'local'"
        )


if __name__ == "__main__":
    try:
        embeddings = get_embeddings("openai")
        result = embeddings.embed_query("Hello, world!")
        print(f"Successfully embedded query. Embedding dimension: {len(result)}")
    except ValueError as e:
        print(f"OpenAI embedding test skipped: {e}")
        print("To test OpenAI embeddings, set OPENAI_API_KEY environment variable")

    try:
        embeddings_local = get_embeddings("local")
        result_local = embeddings_local.embed_query("Hello, world!")
        print(f"Successfully embedded query with local model. Embedding dimension: {len(result_local)}")
    except ImportError as e:
        print(f"Local embedding test skipped: {e}")
