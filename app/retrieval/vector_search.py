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


def vector_search(
    query: str,
    top_k: int = 5,
    current_only: bool = False
):

    query_vector = generate_embedding(query)

    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top_k,
        fields="content_vector"
    )

    search_filter = None

    if current_only:
        search_filter = "is_current eq true"

    results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        filter=search_filter,
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


if __name__ == "__main__":

    # query = "What is the client meal reimbursement limit?"
    query = "What is the current OrbitSuite pricing?"

    results = vector_search(
        query=query,
        top_k=5,
        current_only=True
    )

    print("\nQUESTION:")
    print(query)

    for rank, result in enumerate(results, start=1):

        print("\n" + "=" * 60)
        print("RANK:", rank)
        print("SCORE:", result["@search.score"])
        print("DOCUMENT:", result["document_name"])
        print("DEPARTMENT:", result["department"])
        print("SECTION:", result["section"])

        print("\nCONTENT:")
        print(result["content"])