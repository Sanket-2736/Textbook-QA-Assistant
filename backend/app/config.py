import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # API Configuration
    api_title: str = os.getenv("API_TITLE", "Textbook Q&A RAG")
    api_version: str = os.getenv("API_VERSION", "0.1.0")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Pinecone Configuration
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "textbook-qa")

    # OpenAI Configuration
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")

    def __init__(self):
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")


settings = Settings()
