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

2. Only return:
   "I could not find sufficient information in the knowledge base."
   when the retrieved context genuinely does not contain enough evidence to answer.

3. Absence of information is not evidence that something is false.
   If the context merely does not mention something, do not conclude that it does not exist or is not provided.

4. Only answer "No" when the retrieved context explicitly supports that conclusion,
   for example when the context clearly states that something is prohibited,
   unavailable, excluded, or non-reimbursable.

5. If the retrieved context clearly contains the answer, answer it directly.

6. Cite supporting sources using [SOURCE_1], [SOURCE_2], etc.

7. Cite only sources that directly support the specific claim being made.

8. Do not add extra citations merely because a source is related to the topic.

9. Do not invent citations.

10. Keep the answer concise, factual, and focused only on what the user asked.

11. Do not add unrelated details from retrieved context unless they are necessary
    to answer the question correctly.

12. Do not refuse merely because the user's original question is a conversational follow-up.
    Use the resolved question and retrieved context as the authoritative basis for answering.

13. When the evidence is incomplete or only indirectly related, do not make assumptions.
    Return the insufficient-information response instead.
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