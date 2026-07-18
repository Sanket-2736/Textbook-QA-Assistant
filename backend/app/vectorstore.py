import os
from typing import Optional

from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

load_dotenv()


def init_pinecone_index(
    index_name: str,
    dimension: int = 1536,
    metric: str = "cosine",
    cloud: str = "aws",
    region: str = "us-east-1",
) -> None:
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable is required")

    # Initialize Pinecone client
    pc = Pinecone(api_key=api_key)

    # Check if index already exists
    existing_indexes = [idx.name for idx in pc.list_indexes()]

    if index_name not in existing_indexes:
        # Create serverless index with spec
        spec = ServerlessSpec(
            cloud=cloud,
            region=region,
        )

        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=spec,
        )
        print(f"Created Pinecone index: {index_name}")
    else:
        print(f"Pinecone index already exists: {index_name}")


def get_vectorstore(
    index_name: str,
    embeddings,
    namespace: Optional[str] = None,
) -> PineconeVectorStore:
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable is required")

    return PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
        namespace=namespace or "",
    )


def delete_pinecone_index(index_name: str) -> None:
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable is required")

    pc = Pinecone(api_key=api_key)
    pc.delete_index(index_name)
    print(f"Deleted Pinecone index: {index_name}")


if __name__ == "__main__":
    import time

    from app.embeddings import get_embeddings

    TEST_INDEX = "test-textbook-qa"
    TEST_NAMESPACE = "test"

    try:
        # Initialize embeddings (using OpenAI by default)
        print("Initializing embeddings...")
        embeddings = get_embeddings()

        # Get embedding dimension
        test_embedding = embeddings.embed_query("test")
        dimension = len(test_embedding)
        print(f"Embedding dimension: {dimension}")

        # Create index
        print(f"\nCreating Pinecone index: {TEST_INDEX}")
        init_pinecone_index(TEST_INDEX, dimension=dimension)

        # Wait for index to be ready
        print("Waiting for index to be ready...")
        time.sleep(2)

        # Get vectorstore
        print("Getting vectorstore...")
        vectorstore = get_vectorstore(TEST_INDEX, embeddings, namespace=TEST_NAMESPACE)

        # Upsert a test vector
        print("Upserting test document...")
        test_texts = ["This is a test document about machine learning"]
        test_ids = ["test-doc-1"]

        vectorstore.add_texts(texts=test_texts, ids=test_ids)
        print(f"Successfully upserted {len(test_texts)} document(s)")

        # Query
        print("\nQuerying vectorstore...")
        query = "machine learning"
        results = vectorstore.similarity_search(query, k=1)

        print(f"Query: '{query}'")
        print(f"Results ({len(results)}):")
        for i, result in enumerate(results):
            print(f"  {i+1}. {result.page_content}")
            print(f"     Metadata: {result.metadata}")

        # Delete index
        print(f"\nDeleting test index: {TEST_INDEX}")
        delete_pinecone_index(TEST_INDEX)
        print("Test completed successfully!")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()