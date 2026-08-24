import os

from dotenv import load_dotenv
from openai import AzureOpenAI


load_dotenv()


client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-01"
)


def rewrite_query(
    current_question: str,
    history: list
) -> str:

    if not history:
        return current_question

    recent_history = history[-4:]

    history_text = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in recent_history
    )

    system_prompt = """
You rewrite conversational follow-up questions into
standalone search queries for a retrieval system.

Rules:
1. Do not answer the question.
2. Use conversation history only when needed.
3. Preserve the user's exact intent.
4. Do not introduce new topics.
5. Return only the standalone query.
"""

    user_prompt = f"""
Conversation:
{history_text}

Latest user question:
{current_question}

Standalone search query:
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

    return response.choices[0].message.content.strip()