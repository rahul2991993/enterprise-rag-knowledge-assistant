import os

from dotenv import load_dotenv
from openai import AzureOpenAI


load_dotenv()


client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-01"
)


def decompose_query(question: str) -> list[str]:

    system_prompt = """
You are a search-query decomposition component.

Your job is ONLY to rewrite a complex question into
independent retrieval queries.

Do NOT answer the question.

Rules:
1. Split only when multiple entities or items must be retrieved separately.
2. Preserve the exact scope of the original question.
3. Do NOT introduce new topics, attributes, requirements, or assumptions.
4. Preserve temporal intent such as current, latest, 2025, or 2026.
5. Return a maximum of 3 queries.
6. Return one query per line.
7. Do not number the queries.
8. If decomposition is unnecessary, return only the original question.
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
                "content": question
            }
        ]
    )

    text = response.choices[0].message.content

    queries = [
        line.strip().lstrip("-").strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return queries[:3]


if __name__ == "__main__":

    question = (
        "Compare the Starter and Enterprise "
        "OrbitSuite plans."
    )

    queries = decompose_query(question)

    print("\nORIGINAL:")
    print(question)

    print("\nDECOMPOSED:")

    for query in queries:
        print("-", query)