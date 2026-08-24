from pathlib import Path

import pandas as pd
from docx import Document
from pypdf import PdfReader


def load_pdf(file_path: Path) -> str:
    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


def load_docx(file_path: Path) -> str:
    document = Document(file_path)

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs)


def load_excel(file_path: Path) -> str:
    excel_file = pd.ExcelFile(file_path)

    content = []

    for sheet_name in excel_file.sheet_names:

        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name
        )

        content.append(
            f"Sheet: {sheet_name}\n{df.to_string(index=False)}"
        )

    return "\n\n".join(content)


def load_document(file_path: Path) -> str:

    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return load_pdf(file_path)

    elif extension == ".docx":
        return load_docx(file_path)

    elif extension == ".xlsx":
        return load_excel(file_path)

    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )


def load_knowledge_base(base_path: str):

    base_path = Path(base_path)

    documents = []

    supported_extensions = {
        ".pdf",
        ".docx",
        ".xlsx"
    }

    for file_path in base_path.rglob("*"):

        if (
            file_path.is_file()
            and file_path.suffix.lower()
            in supported_extensions
        ):

            print(f"Loading: {file_path}")

            text = load_document(file_path)

            department = file_path.parent.name

            documents.append(
                {
                    "document_name": file_path.name,
                    "department": department,
                    "file_type": file_path.suffix.lower(),
                    "source_path": str(file_path),
                    "text": text
                }
            )

    return documents


if __name__ == "__main__":

    documents = load_knowledge_base(
        "../../data/KnowledgeBase"
    )

    print("\nTotal documents:", len(documents))

    for document in documents:

        print("\n---------------------------")
        print("Document:", document["document_name"])
        print("Department:", document["department"])
        print("Characters:", len(document["text"]))

        print("\nPreview:")
        print(document["text"][:500])