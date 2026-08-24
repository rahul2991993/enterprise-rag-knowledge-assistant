from app.retrieval.hybrid_search import hybrid_search, multi_query_search
from app.retrieval.query_intent import detect_current_intent, is_ambiguous_query
from app.retrieval.query_decomposition import decompose_query
from app.retrieval.query_rewriter import rewrite_query
from app.generation.generator import generate_answer


def ask(
    question: str,
    history: list | None = None
):

    history = history or []

    # 1. Rewrite conversational follow-up into standalone query
    standalone_question = rewrite_query(
        current_question=question,
        history=history
    )

    print(
        "\nSTANDALONE QUESTION:",
        standalone_question
    )

    # 2. Check ambiguity AFTER rewriting
    if is_ambiguous_query(standalone_question):

        return {
            "question": question,
            "rewritten_question": standalone_question,
            "answer": (
                "Could you clarify which limit you mean? "
                "For example, expense, travel, pricing, "
                "discount, or contractual limit?"
            ),
            "sources": []
        }

    # 3. Detect current/latest intent
    # Use standalone question, not original question
    current_only = detect_current_intent(
        standalone_question
    )

    # 4. Decompose the standalone retrieval query
    search_queries = decompose_query(
        standalone_question
    )

    print(
        "\nSEARCH QUERIES:",
        search_queries
    )

    # 5. Retrieve relevant chunks
    if len(search_queries) == 1:

        retrieved_chunks = hybrid_search(
            query=search_queries[0],
            top_k=5,
            current_only=current_only
        )

    else:

        retrieved_chunks = multi_query_search(
            queries=search_queries,
            top_k_per_query=3,
            current_only=current_only
        )

    # Keep ORIGINAL question here because this is
    # what the user actually asked.
    generation_result = generate_answer(
    question=standalone_question,
    retrieved_chunks=retrieved_chunks
    )

    answer = generation_result["answer"]

    return {
        "question": question,
        "rewritten_question": standalone_question,
        "answer": answer,
        "sources": retrieved_chunks,
        "usage": generation_result["usage"]
    }


if __name__ == "__main__":

    history = [
        {
            "role": "user",
            "content":
                "What is the Enterprise OrbitSuite pricing?"
        },
        {
            "role": "assistant",
            "content":
                "The Enterprise plan costs $109 per seat per month."
        }
    ]

    question = "What about Starter?"

    result = ask(
        question=question,
        history=history
    )

    print("\nORIGINAL QUESTION:")
    print(result["question"])

    print("\nREWRITTEN QUESTION:")
    print(result["rewritten_question"])

    print("\nANSWER:")
    print(result["answer"])