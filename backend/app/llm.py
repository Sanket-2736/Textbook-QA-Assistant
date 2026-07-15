"""LLM provider configuration using Cerebras."""

import os
from typing import Optional

from dotenv import load_dotenv
from langchain_cerebras.chat_models import ChatCerebras

load_dotenv()


def get_llm(model: str = "llama-3.1-70b", temperature: float = 0.7) -> ChatCerebras:
    """
    Initialize and return a ChatCerebras LLM instance.

    Args:
        model: Model name to use. Default is "llama-3.1-70b"
        temperature: Temperature for model response. Default is 0.7

    Returns:
        ChatCerebras: Configured chat model instance

    Raises:
        ValueError: If CEREBRAS_API_KEY is not set
    """
    api_key: Optional[str] = os.getenv("CEREBRAS_API_KEY")

    if not api_key:
        raise ValueError("CEREBRAS_API_KEY environment variable is required")

    return ChatCerebras(
        api_key=api_key,
        model=model,
        temperature=temperature,
    )


if __name__ == "__main__":
    # Test block: instantiate LLM and send a test message
    llm = get_llm()
    message = "Say hello in 5 words"
    print(f"Query: {message}")
    response = llm.invoke(message)
    print(f"Response: {response.content}")
