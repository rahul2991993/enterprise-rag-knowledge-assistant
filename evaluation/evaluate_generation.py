import json
import time
import os

from dotenv import load_dotenv
from openai import AzureOpenAI

from app.rag import ask


load_dotenv()


DATASET_PATH = "evaluation/dataset.json"


client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-01"
)


def load_dataset():

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# Answer correctness judge

def judge_answer(
    question,
    expected_answer,
    actual_answer
):

    prompt = f"""
You are evaluating a RAG system.

Question:
{question}

Expected answer:
{expected_answer}

Actual answer:
{actual_answer}

Score answer correctness:

2 = correct and contains the important expected facts
1 = partially correct
0 = incorrect or unsupported

Return ONLY one integer:
0, 1, or 2.
"""

    response = client.chat.completions.create(
        model=os.getenv(
            "AZURE_OPENAI_CHAT_DEPLOYMENT"
        ),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return int(
        response.choices[0].message.content.strip()
    )


# Grounding + citation correctness judge

def judge_grounding_and_citations(
    question,
    actual_answer,
    sources
):

    source_text = "\n\n".join(
        f"""
[SOURCE_{i}]
Document: {source["document_name"]}
Section: {source["section"]}

Content:
{source["content"]}
"""
        for i, source in enumerate(
            sources,
            start=1
        )
    )

    prompt = f"""
You are evaluating a RAG answer.

Question:
{question}

Retrieved sources:
{source_text}

Actual answer:
{actual_answer}

Evaluate two things.

GROUNDING:
2 = all important factual claims are supported by the retrieved sources
1 = mostly supported, but one or more claims are weakly supported
0 = important claims are unsupported or hallucinated

CITATION CORRECTNESS:
2 = citations point to sources that actually support the associated claims
1 = some citations are correct but others are weak or incomplete
0 = citations are wrong, misleading, or unsupported

Return exactly:

GROUNDING=<0|1|2>
CITATION=<0|1|2>
"""

    response = client.chat.completions.create(
        model=os.getenv(
            "AZURE_OPENAI_CHAT_DEPLOYMENT"
        ),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    text = response.choices[0].message.content.strip()

    grounding = None
    citation = None

    for line in text.splitlines():

        line = line.strip()

        if line.startswith("GROUNDING="):
            grounding = int(
                line.split("=")[1]
            )

        if line.startswith("CITATION="):
            citation = int(
                line.split("=")[1]
            )

    return grounding, citation


# Evaluation

def evaluate():

    dataset = load_dataset()

    correctness_scores = []
    grounding_scores = []
    citation_scores = []

    no_answer_correct = 0
    no_answer_total = 0

    hallucinations = 0

    ambiguous_correct = 0
    ambiguous_total = 0

    latencies = []

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    for item in dataset:

        question = item["question"]

        history = item.get(
            "history",
            []
        )

        start = time.perf_counter()

        result = ask(
            question=question,
            history=history
        )

        usage = result.get("usage")

        if usage:

            prompt_tokens = usage["prompt_tokens"]
            completion_tokens = usage["completion_tokens"]
            query_total_tokens = usage["total_tokens"]

            total_prompt_tokens += prompt_tokens
            total_completion_tokens += completion_tokens
            total_tokens += query_total_tokens

        latency = (
            time.perf_counter()
            - start
        )

        latencies.append(latency)

        actual_answer = result["answer"]

        expected_answer = item.get(
            "expected_answer"
        )

        print("\n" + "=" * 70)

        print(
            item["id"],
            question
        )

        print("Answer:", actual_answer)

        print(
            "Latency:",
            round(latency, 2),
            "sec"
        )

        # NO-ANSWER QUESTIONS

        if item["type"] == "no_answer":

            no_answer_total += 1

            refusal_text = (
                "could not find sufficient information"
            )

            correct_refusal = (
                refusal_text
                in actual_answer.lower()
            )

            if correct_refusal:

                no_answer_correct += 1

            else:

                # System answered something even though
                # answer should not exist.
                hallucinations += 1

            print(
                "No-answer behavior:",
                "PASS"
                if correct_refusal
                else "FAIL"
            )

            continue

        # AMBIGUOUS QUESTIONS

        if item["type"] == "ambiguous":

            ambiguous_total += 1

            clarification = ("clarify" in actual_answer.lower())

            if clarification:   
                ambiguous_correct += 1

            print(
                "Clarification:",
                "PASS"
                if clarification
                else "FAIL"
            )

            continue

        # ANSWER CORRECTNESS

        correctness = judge_answer(
            question=question,
            expected_answer=expected_answer,
            actual_answer=actual_answer
        )

        correctness_scores.append(
            correctness
        )

        print(
            "Correctness:",
            correctness,
            "/ 2"
        )

        # GROUNDEDNESS + CITATION CORRECTNESS

        grounding, citation = (
            judge_grounding_and_citations(
                question=question,
                actual_answer=actual_answer,
                sources=result["sources"]
            )
        )

        if grounding is not None:
            grounding_scores.append(
                grounding
            )

        if citation is not None:
            citation_scores.append(
                citation
            )

        print(
            "Grounding:",
            grounding,
            "/ 2"
        )

        print(
            "Citation correctness:",
            citation,
            "/ 2"
        )

    # FINAL METRICS

    print("\n" + "=" * 70)
    print("FINAL EVALUATION RESULTS")

    if correctness_scores:

        avg_correctness = (
            sum(correctness_scores)
            /
            len(correctness_scores)
        )

        print(
            "Average correctness:",
            f"{avg_correctness:.2f}/2"
        )

    if grounding_scores:

        avg_grounding = (
            sum(grounding_scores)
            /
            len(grounding_scores)
        )

        print(
            "Average groundedness:",
            f"{avg_grounding:.2f}/2"
        )

    if citation_scores:

        avg_citation = (
            sum(citation_scores)
            /
            len(citation_scores)
        )

        print(
            "Average citation correctness:",
            f"{avg_citation:.2f}/2"
        )

    if no_answer_total:

        no_answer_accuracy = (
            no_answer_correct
            /
            no_answer_total
        )

        print(
            "No-answer accuracy:",
            f"{no_answer_accuracy:.2%}"
        )

        hallucination_rate = (
            hallucinations
            /
            no_answer_total
        )

        print(
            "Hallucination rate:",
            f"{hallucination_rate:.2%}"
        )

    if ambiguous_total:

        ambiguity_accuracy = (
            ambiguous_correct
            /
            ambiguous_total
        )

        print(
            "Ambiguous-query handling:",
            f"{ambiguity_accuracy:.2%}"
        )

    if latencies:

        average_latency = (
            sum(latencies)
            /
            len(latencies)
        )

        print(
            "Average latency:",
            f"{average_latency:.2f} sec"
        )

    if total_tokens > 0:

        print(
            "Total prompt tokens:",
            total_prompt_tokens
        )

        print(
            "Total completion tokens:",
            total_completion_tokens
        )

        print(
            "Total tokens:",
            total_tokens
        )

        print(
            "Average tokens/query:",
            round(
                total_tokens / len(dataset),
                2
            )
        )


if __name__ == "__main__":

    evaluate()