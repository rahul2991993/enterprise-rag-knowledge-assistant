import os

from dotenv import load_dotenv
from openai import AzureOpenAI


load_dotenv()


client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-01"
)


def needs_decomposition(question: str) -> bool:

    query = question.lower()

    decomposition_terms = [
        "compare",
        "difference",
        "differences",
        "versus",
        " vs ",
        "both",
        "and"
    ]

    return any(
        term in query
        for term in decomposition_terms
    )


def decompose_query(question: str) -> list[str]:

    system_prompt = """
You are a search-query decomposition component.

Your job is ONLY to convert the user's question into one or more
independent retrieval queries.

You must NOT answer the question.

Rules:
1. Split only when multiple entities, items, sections, or subtopics
   genuinely need separate retrieval.

2. Preserve the exact meaning, entities, scope, and intent
   of the original question.

3. Do NOT introduce new topics, attributes, requirements,
   assumptions, interpretations, or substitute questions.

4. Do NOT replace the user's requested entity or attribute
   with a different one.

5. Preserve temporal intent such as:
   current, latest, active, 2025, 2026, historical, or previous.

6. Never answer the user's question.

7. Never refuse the user's question.

8. Never provide safety advice, explanations, commentary,
   warnings, or recommendations.

9. Output retrieval queries ONLY.

10. Return a maximum of 3 queries.

11. Return one query per line.

12. Do not number the queries.

13. Do not use bullets or prefixes.

14. If decomposition is unnecessary,
    return only the original question or a concise retrieval-oriented
    rewrite that preserves exactly the same intent.

15. For comparison questions, create separate queries only when
    retrieving the compared entities separately would improve retrieval.

16. Do not infer facts that are not present in the user's question.
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
        line.strip().lstrip("-•0123456789. ").strip()
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