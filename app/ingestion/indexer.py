import os
import json
from pathlib import Path
import hashlib

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from loader import load_knowledge_base
from chunker import chunk_document
from embeddings import generate_embedding


load_dotenv()


SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")


search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_API_KEY)
)


BASE_DIR = Path(__file__).resolve().parents[2]
CACHE_PATH = BASE_DIR / "data" / "embedding_cache.json"


def load_embedding_cache():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    return {}


def save_embedding_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def prepare_chunks():
    documents = load_knowledge_base(
        "../../data/KnowledgeBase"
    )

    all_chunks = []

    for document in documents:
        chunks = chunk_document(document)
        all_chunks.extend(chunks)

    return all_chunks


def prepare_search_documents(chunks):

    search_documents = []

    embedding_cache = load_embedding_cache()

    for i, chunk in enumerate(chunks, start=1):

        embedding_text = (
            f"Document: {chunk['document_name']}\n"
            f"Department: {chunk['department']}\n"
            f"Section: {chunk['section']}\n\n"
            f"{chunk['content']}"
        )

        # Create cache key from actual text
        cache_key = hashlib.sha256(
            embedding_text.encode("utf-8")
        ).hexdigest()

        if cache_key in embedding_cache:

            print(
                f"Using cached embedding {i}/{len(chunks)} "
                f"for {chunk['document_name']}"
            )

            embedding = embedding_cache[cache_key]

        else:

            print(
                f"Generating embedding {i}/{len(chunks)} "
                f"for {chunk['document_name']}"
            )

            embedding = generate_embedding(
                embedding_text
            )

            embedding_cache[cache_key] = embedding

            save_embedding_cache(
                embedding_cache
            )

        search_document = {
            "chunk_id": chunk["chunk_id"],
            "document_name": chunk["document_name"],
            "department": chunk["department"],
            "file_type": chunk["file_type"],
            "source_path": chunk["source_path"],
            "section": chunk["section"],
            "content": chunk["content"],
            "effective_year": chunk["effective_year"],
            "is_current": chunk["is_current"],
            "content_vector": embedding
        }

        search_documents.append(
            search_document
        )

    return search_documents


def upload_to_search(search_documents):

    results = search_client.upload_documents(
        documents=search_documents
    )

    successful = 0
    failed = 0

    for result in results:

        if result.succeeded:
            successful += 1
        else:
            failed += 1
            print(
                "Failed:",
                result.key,
                result.error_message
            )

    print("\nUpload finished")
    print("Successful:", successful)
    print("Failed:", failed)


if __name__ == "__main__":

    chunks = prepare_chunks()

    print(
        "\nTotal chunks prepared:",
        len(chunks)
    )

    search_documents = (
        prepare_search_documents(chunks)
    )

    print(
        "\nUploading documents "
        "to Azure AI Search..."
    )

    upload_to_search(
        search_documents
    )