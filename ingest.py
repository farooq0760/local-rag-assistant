"""
ingest.py — Load, chunk, embed, and store your documents locally.
Run this once, then re-run whenever you add/update documents.

Usage:
    python ingest.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

load_dotenv()

DOCS_FOLDER = os.getenv("DOCS_FOLDER", "./docs")
CHROMA_DB_FOLDER = os.getenv("CHROMA_DB_FOLDER", "./chroma_db")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

SUPPORTED_EXTENSIONS = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".md": TextLoader,
    ".docx": Docx2txtLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls": UnstructuredExcelLoader,
}


def load_documents(folder: str) -> list:
    docs_path = Path(folder)
    if not docs_path.exists():
        docs_path.mkdir(parents=True)
        print(f"📁 Created docs folder at: {docs_path.resolve()}")
        print("   → Drop your documents in there, then re-run this script.")
        sys.exit(0)

    all_docs = []
    files = list(docs_path.rglob("*"))
    found = [f for f in files if f.suffix.lower() in SUPPORTED_EXTENSIONS]

    if not found:
        print(f"⚠️  No supported documents found in '{folder}'.")
        print(f"   Supported: {', '.join(SUPPORTED_EXTENSIONS.keys())}")
        sys.exit(0)

    print(f"📄 Found {len(found)} document(s)...")
    for file in found:
        ext = file.suffix.lower()
        loader_cls = SUPPORTED_EXTENSIONS[ext]
        try:
            loader = loader_cls(str(file))
            docs = loader.load()
            # Tag each chunk with its source filename
            for doc in docs:
                doc.metadata["source"] = file.name
            all_docs.extend(docs)
            print(f"   ✅ Loaded: {file.name} ({len(docs)} page/section(s))")
        except Exception as e:
            print(f"   ❌ Failed to load {file.name}: {e}")

    return all_docs


def split_documents(docs: list) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"\n✂️  Split into {len(chunks)} chunks.")
    return chunks


def embed_and_store(chunks: list):
    print(f"\n🧠 Embedding with '{EMBED_MODEL}' (this may take a few minutes)...")
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_FOLDER,
    )
    print(f"✅ Stored {len(chunks)} chunks in ChromaDB at '{CHROMA_DB_FOLDER}'")
    return vectorstore


def main():
    print("=" * 55)
    print("  🔒 Local RAG — Document Ingestion")
    print("=" * 55)
    print(f"  Docs folder : {Path(DOCS_FOLDER).resolve()}")
    print(f"  Vector DB   : {Path(CHROMA_DB_FOLDER).resolve()}")
    print(f"  Embed model : {EMBED_MODEL}")
    print("=" * 55 + "\n")

    docs = load_documents(DOCS_FOLDER)
    chunks = split_documents(docs)
    embed_and_store(chunks)

    print("\n🎉 Ingestion complete! Run 'streamlit run app.py' to start chatting.")


if __name__ == "__main__":
    main()
