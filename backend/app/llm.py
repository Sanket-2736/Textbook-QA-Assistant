import os
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras

load_dotenv()


def get_llm():
    api_key = os.getenv("CEREBRAS_API_KEY")

    if not api_key:
        raise ValueError("CEREBRAS_API_KEY environment variable is required")

    return Cerebras(api_key=api_key)


def invoke_llm(
    prompt: str,
    model: str = "gpt-oss-120b",
    temperature: float = 0.7,
):
    client = get_llm()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=temperature,
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    print(invoke_llm("Say hello in 5 words"))