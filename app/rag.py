import time

from app.retrieval.hybrid_search import hybrid_search, multi_query_search
from app.retrieval.query_intent import detect_current_intent, is_ambiguous_query
from app.retrieval.query_decomposition import decompose_query, needs_decomposition
from app.retrieval.query_rewriter import rewrite_query
from app.generation.generator import generate_answer


def ask(
    question: str,
    history: list | None = None
):

    total_start = time.perf_counter()

    history = history or []

    # 1. Query rewriting
    rewrite_start = time.perf_counter()

    standalone_question = rewrite_query(
        current_question=question,
        history=history
    )

    rewrite_latency = (
        time.perf_counter() - rewrite_start
    )

    print(
        "\nSTANDALONE QUESTION:",
        standalone_question
    )

    # 2. Ambiguity handling
    if is_ambiguous_query(standalone_question):

        total_latency = (
            time.perf_counter() - total_start
        )

        return {
            "question": question,
            "rewritten_question": standalone_question,
            "answer": (
                "Could you clarify which limit or policy "
                "you are referring to?"
            ),
            "sources": [],
            "usage": None,
            "timings": {
                "rewrite_seconds": round(
                    rewrite_latency, 3
                ),
                "decomposition_seconds": 0,
                "retrieval_seconds": 0,
                "generation_seconds": 0,
                "total_seconds": round(
                    total_latency, 3
                )
            }
        }

    # 3. Current/latest intent
    current_only = detect_current_intent(
        standalone_question
    )

    # 4. Query decomposition
    decomposition_start = time.perf_counter()

    if needs_decomposition(standalone_question):

        search_queries = decompose_query(
            standalone_question
        )

    else:

        search_queries = [
            standalone_question
        ]

    decomposition_latency = (
        time.perf_counter()
        - decomposition_start
    )

    print(
        "\nSEARCH QUERIES:",
        search_queries
    )

    # 5. Retrieval
    retrieval_start = time.perf_counter()

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

    retrieval_latency = (
        time.perf_counter()
        - retrieval_start
    )

    # 6. Generation
    generation_start = time.perf_counter()

    generation_result = generate_answer(
        question=standalone_question,
        retrieved_chunks=retrieved_chunks
    )

    generation_latency = (
        time.perf_counter()
        - generation_start
    )

    answer = generation_result["answer"]

    total_latency = (
        time.perf_counter()
        - total_start
    )

    timings = {
        "rewrite_seconds": round(
            rewrite_latency, 3
        ),
        "decomposition_seconds": round(
            decomposition_latency, 3
        ),
        "retrieval_seconds": round(
            retrieval_latency, 3
        ),
        "generation_seconds": round(
            generation_latency, 3
        ),
        "total_seconds": round(
            total_latency, 3
        )
    }

    print(
        "\nTIMINGS:",
        timings
    )

    return {
        "question": question,
        "rewritten_question": standalone_question,
        "answer": answer,
        "sources": retrieved_chunks,
        "usage": generation_result["usage"],
        "timings": timings
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