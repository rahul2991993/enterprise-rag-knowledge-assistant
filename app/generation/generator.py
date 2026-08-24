import os

from dotenv import load_dotenv
from openai import AzureOpenAI


load_dotenv()


client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-01"
)


def generate_answer(
    question: str,
    retrieved_chunks: list
):

    context_parts = []

    for i, chunk in enumerate(
        retrieved_chunks,
        start=1
    ):

        context_parts.append(
            f"""
[SOURCE_{i}]
Document: {chunk["document_name"]}
Section: {chunk["section"]}

{chunk["content"]}
"""
        )

    context = "\n".join(context_parts)

    system_prompt = """
You are an enterprise knowledge assistant.

Answer the user's question using ONLY the provided context.

Rules:
1. Do not use outside knowledge.
2. If the context does not contain enough evidence,
   say:
   "I could not find sufficient information in the knowledge base."
3. Cite supporting sources using [SOURCE_1], [SOURCE_2], etc.
4. Do not invent citations.
5. Keep the answer concise and factual.
"""

    user_prompt = f"""
QUESTION:
{question}

CONTEXT:
{context}
"""

    response = client.chat.completions.create(
        model=os.getenv(
            "AZURE_OPENAI_CHAT_DEPLOYMENT"
        ),
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return {
    "answer": response.choices[0].message.content,
    "usage": {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens
    }
    }