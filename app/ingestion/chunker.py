import re
from typing import List, Dict


def clean_text(text: str) -> str:
    """
    Basic cleanup of text extracted from PDF/DOCX.
    """

    # Remove control characters except newline/tab
    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
        "",
        text
    )

    # Normalize Windows/newline variations
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_into_sections(text: str) -> List[Dict]:

    text = clean_text(text)

    lines = text.splitlines()

    sections = []

    current_heading = "Document Introduction"
    current_content = []

    heading_pattern = re.compile(
        r"^\d+(?:\.\d+)*\.?\s+[A-Za-z].+"
    )

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if heading_pattern.match(line):

            if current_content:

                sections.append(
                    {
                        "section": current_heading,
                        "content": "\n".join(
                            current_content
                        ).strip()
                    }
                )

            current_heading = line
            current_content = []

        else:

            current_content.append(line)

    if current_content:

        sections.append(
            {
                "section": current_heading,
                "content": "\n".join(
                    current_content
                ).strip()
            }
        )

    return sections


def chunk_section(
    content: str,
    chunk_size: int = 1200,
    overlap: int = 200
) -> List[str]:

    chunks = []

    start = 0

    while start < len(content):

        end = start + chunk_size

        chunk = content[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(content):
            break

        start = end - overlap

    return chunks


import re
from typing import List, Dict


def get_version_metadata(document_name: str):

    if document_name == "Pricing2025.pdf":
        return {
            "effective_year": 2025,
            "is_current": False
        }

    if document_name == "Pricing2026.pdf":
        return {
            "effective_year": 2026,
            "is_current": True
        }

    return {
        "effective_year": None,
        "is_current": True
    }


def chunk_document(
    document: Dict,
    chunk_size: int = 1200,
    overlap: int = 200
) -> List[Dict]:

    sections = split_into_sections(
        document["text"]
    )

    chunks = []

    chunk_number = 0

    safe_document_name = re.sub(
        r"[^A-Za-z0-9_-]",
        "_",
        document["document_name"]
    )

    # Get version information once for this document
    version_metadata = get_version_metadata(
        document["document_name"]
    )

    for section in sections:

        section_chunks = chunk_section(
            section["content"],
            chunk_size=chunk_size,
            overlap=overlap
        )

        for text_chunk in section_chunks:

            chunk_number += 1

            chunks.append(
                {
                    "chunk_id": f"{safe_document_name}_{chunk_number}",

                    "document_name": document["document_name"],

                    "department": document["department"],

                    "file_type": document["file_type"],

                    "source_path": document["source_path"],

                    "section": section["section"],

                    "content": text_chunk,

                    "effective_year": version_metadata["effective_year"],

                    "is_current": version_metadata["is_current"]
                }
            )

    return chunks


if __name__ == "__main__":

    from loader import load_knowledge_base

    documents = load_knowledge_base(
        "../../data/KnowledgeBase"
    )

    all_chunks = []

    for document in documents:

        chunks = chunk_document(document)

        all_chunks.extend(chunks)

        print(
            document["document_name"],
            "->",
            len(chunks),
            "chunks"
        )

    print("\nTotal chunks:", len(all_chunks))

    print("\nExample chunk:")

    print(all_chunks[0])