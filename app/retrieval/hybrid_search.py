import os

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from app.ingestion.embeddings import generate_embedding


load_dotenv()


SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")


search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_API_KEY)
)


def hybrid_search(
    query: str,
    top_k: int = 5,
    current_only: bool = False
):

    # 1. Generate embedding for vector search
    query_vector = generate_embedding(query)

    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=10,
        fields="content_vector"
    )

    # 2. Optional metadata filter
    search_filter = None

    if current_only:
        search_filter = "is_current eq true"

    # 3. Hybrid search + semantic reranking
    results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        filter=search_filter,

        query_type="semantic",
        semantic_configuration_name="rag-semantic-config",
        query_caption="extractive",

        select=[
            "chunk_id",
            "document_name",
            "department",
            "section",
            "content",
            "effective_year",
            "is_current"
        ],

        top=top_k
    )

    return list(results)


def multi_query_search(
        queries: list[str],
        top_k_per_query: int = 3,
        current_only: bool = False
):

    combined_results = {}

    for query in queries:

        results = hybrid_search(
            query=query,
            top_k=top_k_per_query,
            current_only=current_only
        )

        for result in results:

            chunk_id = result["chunk_id"]

            if chunk_id not in combined_results:

                combined_results[chunk_id] = result

    return list(combined_results.values())

if __name__ == "__main__":

    query = "What is the client meal reimbursement limit?"

    results = hybrid_search(
        query=query,
        top_k=5
    )

    print("\nQUESTION:")
    print(query)

    for rank, result in enumerate(results, start=1):

        print("\n" + "=" * 60)

        print("RANK:", rank)

        print(
            "HYBRID SCORE:",
            result.get("@search.score")
        )

        print(
            "RERANKER SCORE:",
            result.get("@search.reranker_score")
        )

        print(
            "DOCUMENT:",
            result["document_name"]
        )

        print(
            "SECTION:",
            result["section"]
        )

        print("\nCONTENT:")
        print(result["content"])