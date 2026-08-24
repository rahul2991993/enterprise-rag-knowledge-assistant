import json

from app.retrieval.vector_search import vector_search
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.query_intent import detect_current_intent
from app.retrieval.query_rewriter import rewrite_query


DATASET_PATH = "evaluation/dataset.json"


def load_dataset():

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def evaluate_retrieval(search_type="improved"):

    dataset = load_dataset()

    evaluated = 0

    hit_1 = 0
    hit_3 = 0
    hit_5 = 0

    reciprocal_rank_sum = 0

    section_hits = 0
    section_evaluated = 0

    for item in dataset:

        expected_document = item.get(
            "expected_document"
        )

        if expected_document is None:
            continue

        question = item["question"]

        # Follow-up questions should use history
        history = item.get("history", [])

        retrieval_query = rewrite_query(
            current_question=question,
            history=history
        )

        current_only = detect_current_intent(
            retrieval_query
        )

        if search_type == "baseline":

            results = vector_search(
                query=retrieval_query,
                top_k=5,
                current_only=False
            )

        else:

            results = hybrid_search(
                query=retrieval_query,
                top_k=5,
                current_only=current_only
            )

        retrieved_documents = [
            result["document_name"]
            for result in results
        ]

        retrieved_sections = [
            result["section"]
            for result in results
        ]

        evaluated += 1

        # -------------------
        # Hit@1
        # -------------------

        if (
            len(retrieved_documents) >= 1
            and retrieved_documents[0]
            == expected_document
        ):
            hit_1 += 1

        # -------------------
        # Hit@3
        # -------------------

        if expected_document in retrieved_documents[:3]:
            hit_3 += 1

        # -------------------
        # Hit@5
        # -------------------

        if expected_document in retrieved_documents[:5]:
            hit_5 += 1

        # -------------------
        # MRR
        # -------------------

        reciprocal_rank = 0

        for rank, document in enumerate(
            retrieved_documents,
            start=1
        ):

            if document == expected_document:

                reciprocal_rank = 1 / rank
                break

        reciprocal_rank_sum += reciprocal_rank

        # -------------------
        # Section accuracy
        # -------------------

        expected_section = item.get(
            "expected_section"
        )

        section_hit = None

        if expected_section:

            section_evaluated += 1

            section_hit = (
                expected_section
                in retrieved_sections
            )

            if section_hit:
                section_hits += 1

        print("\n" + "=" * 70)

        print(
            item["id"],
            question
        )

        if retrieval_query != question:

            print(
                "Rewritten:",
                retrieval_query
            )

        print(
            "Expected document:",
            expected_document
        )

        print(
            "Retrieved:",
            retrieved_documents
        )

        print(
            "Expected section:",
            expected_section
        )

        print(
            "Sections:",
            retrieved_sections
        )

        print(
            "Reciprocal Rank:",
            round(reciprocal_rank, 3)
        )

        if section_hit is not None:

            print(
                "Section:",
                "HIT" if section_hit else "MISS"
            )

    print("\n" + "=" * 70)

    print(
        f"Hit@1: {hit_1 / evaluated:.2%}"
    )

    print(
        f"Hit@3: {hit_3 / evaluated:.2%}"
    )

    print(
        f"Hit@5: {hit_5 / evaluated:.2%}"
    )

    print(
        f"MRR: {reciprocal_rank_sum / evaluated:.3f}"
    )

    if section_evaluated:

        print(
            "Expected Section Hit@5:",
            f"{section_hits / section_evaluated:.2%}"
        )


if __name__ == "__main__":

    print("\n\nBASELINE RETRIEVAL")
    evaluate_retrieval(
        search_type="baseline"
    )

    print("\n\nIMPROVED RETRIEVAL")
    evaluate_retrieval(
        search_type="improved"
    )