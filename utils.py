import re
from pathlib import Path
import streamlit as st

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma

from config import DOCS_FOLDER, CHROMA_DB_FOLDER, EMBED_MODEL, CHAT_MODEL

SUPPORTED_EXTENSIONS = {
    ".pdf":  PyPDFLoader,
    ".txt":  TextLoader,
    ".md":   TextLoader,
    ".docx": Docx2txtLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls":  UnstructuredExcelLoader,
}

def list_documents():
    docs_path = Path(DOCS_FOLDER)
    if not docs_path.exists():
        return []
    return sorted(f.name for f in docs_path.rglob("*") if f.suffix.lower() in SUPPORTED_EXTENSIONS)

def ingest_uploaded_file(uploaded_file, vectorstore):
    docs_path = Path(DOCS_FOLDER)
    docs_path.mkdir(parents=True, exist_ok=True)
    save_path = docs_path / uploaded_file.name
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    ext = save_path.suffix.lower()
    loader_cls = SUPPORTED_EXTENSIONS.get(ext)
    if not loader_cls:
        return False, f"Unsupported format: {ext}"
    try:
        docs = loader_cls(str(save_path)).load()
        for doc in docs:
            doc.metadata["source"] = uploaded_file.name
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(docs)
        vectorstore.add_documents(chunks)
        return True, f"✅ **{uploaded_file.name}** added ({len(chunks)} chunks)"
    except Exception as e:
        return False, f"❌ Failed to process {uploaded_file.name}: {e}"

@st.cache_resource(show_spinner=False)
def load_vectorstore_and_llm():
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    vectorstore = Chroma(persist_directory=CHROMA_DB_FOLDER, embedding_function=embeddings)
    llm = ChatOllama(model=CHAT_MODEL, temperature=0.2)
    return vectorstore, llm

def build_source_map(source_docs: list) -> dict:
    sources = {}
    for doc in source_docs:
        name = doc.metadata.get("source", "Unknown")
        if name not in sources:
            snippet = doc.page_content[:280].replace("\n", " ").strip()
            sources[name] = {"num": len(sources) + 1, "name": name, "snippet": snippet}
    return sources

def inject_tooltips(text: str, sources: dict) -> str:
    num_map = {info["num"]: info for info in sources.values()}
    def _replace(match):
        n = int(match.group(1))
        if n not in num_map:
            return match.group(0)
        info = num_map[n]
        name = info["name"].replace('"', "&quot;")
        snippet = info["snippet"].replace('"', "&quot;")
        return f'<span class="ref-num">{n}<span class="ref-tip">📄 <b>{name}</b><br><br>{snippet}…</span></span>'
    return re.sub(r'\[(\d+)\]', _replace, text)

def build_prompt(question: str, source_docs: list, sources: dict) -> str:
    source_list = "\n".join(f"Source [{info['num']}]" for name, info in sources.items())
    context_parts = []
    for doc in source_docs:
        name = doc.metadata.get("source", "Unknown")
        num = sources.get(name, {}).get("num", "?")
        context_parts.append(f"Source [{num}]:\n{doc.page_content}")
    context = "\n\n---\n\n".join(context_parts)

    return f"""You are a brilliant, world-class Professor and Expert Researcher.
You are teaching an advanced student who wants to understand these documents deeply.

Your mandate is to EXPLAIN, not summarize. You must act as a patient, detailed teacher.
1. Break down complex ideas into intuitive, step-by-step lessons.
2. Provide exhaustive, comprehensive explanations of the "why" and "how" behind every mechanism or architecture.
3. A brief, general summary is UNACCEPTABLE. You must provide a long, highly detailed, and insightful response.
4. Use Markdown formatting (bolding, numbered lists, bullet points) to make your lesson highly readable.

Use ONLY the provided context. If the answer is not in the context, say so honestly.

CRITICAL INSTRUCTION FOR CITATIONS:
Since you only know the source numbers (e.g., Source [1]), you MUST use bracketed numbers like [1] or [2] to cite your facts at the end of sentences.
Example format: "The proposed model avoids error accumulation [1]. Instead, it uses a rollout loss trajectory [2]."
FAILURE TO INCLUDE NUMBERED BRACKETS IS A CRITICAL ERROR.

CRITICAL INSTRUCTION FOR YOUR THOUGHT PROCESS:
You MUST structure your internal thoughts into clear paragraphs. 
EVERY SINGLE PARAGRAPH within your thought process MUST begin with a short, bold, descriptive header.
Example format:
**Analyzing the Query:**
I need to compare V-JEPA and VL-JEPA.

**Extracting Evidence:**
Source [1] states that...

AVAILABLE SOURCES:
{source_list}

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
