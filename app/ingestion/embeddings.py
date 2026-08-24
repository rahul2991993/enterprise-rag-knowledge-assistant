import os

from dotenv import load_dotenv
from openai import AzureOpenAI


load_dotenv()


client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-01"
)


def generate_embedding(text: str):

    response = client.embeddings.create(
        model=os.getenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        ),
        input=text
    )

    return response.data[0].embedding


if __name__ == "__main__":

    text = (
        "Employees are entitled to annual leave "
        "according to company policy."
    )

    embedding = generate_embedding(text)

    print("Embedding length:", len(embedding))

    print("First 10 values:")
    print(embedding[:10])