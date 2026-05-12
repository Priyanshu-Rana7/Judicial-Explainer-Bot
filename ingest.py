"""
ingest.py – Document ingestion and FAISS index management.
Supports both built-in knowledge base (data/*.txt) and user-uploaded PDFs.
Uses local HuggingFace all-MiniLM-L6-v2 embeddings — no API key needed.
"""

import os
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_community.vectorstores import FAISS

# ── Constants ─────────────────────────────────────────────────────────────────
CHUNK_SIZE      = 1000
CHUNK_OVERLAP   = 200
INDEX_PATH      = "faiss_index"
DATA_DIR        = "data"          # Built-in knowledge base directory


def get_embeddings() -> HuggingFaceInferenceAPIEmbeddings:
    """Return a Cloud-based embedding model to save RAM on Render."""
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        print("[WARN] HUGGINGFACE_API_KEY missing. Falling back to local (might crash).")
        from langchain_community.embeddings import FastEmbedEmbeddings
        return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5", threads=1)
    
    return HuggingFaceInferenceAPIEmbeddings(
        api_key=api_key,
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def _split_documents(docs: list) -> list:
    """Split a list of Document objects into chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(docs)


def load_builtin_knowledge() -> list:
    """
    Load all .txt files from the data/ directory as the built-in knowledge base.
    Returns a list of chunked Document objects with source/page metadata.
    """
    data_path = Path(DATA_DIR)
    if not data_path.exists():
        return []

    all_chunks = []
    txt_files  = sorted(data_path.glob("*.txt"))

    for txt_file in txt_files:
        try:
            loader = TextLoader(str(txt_file), encoding="utf-8")
            docs   = loader.load()
            # Set clean source name
            for doc in docs:
                doc.metadata["source"] = txt_file.name
                doc.metadata["page"]   = 1  # text files don't have pages
            chunks = _split_documents(docs)
            # Assign sequential fake "page" numbers based on chunk position
            for i, chunk in enumerate(chunks):
                chunk.metadata["source"] = txt_file.name
                chunk.metadata["page"]   = i + 1
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[WARN] Could not load {txt_file.name}: {e}")

    return all_chunks


def load_and_split_pdf(file_path: str, display_name: str = None) -> list:
    """
    Load a PDF and split it into chunks.
    Each chunk retains metadata: source (filename) and page number (1-indexed).
    """
    loader = PyPDFLoader(file_path)
    pages  = loader.load()

    # Page numbers from PyPDFLoader are 0-indexed; convert to 1-indexed
    for doc in pages:
        if "page" in doc.metadata:
            doc.metadata["page"] = doc.metadata["page"] + 1
        if display_name:
            doc.metadata["source"] = display_name
        else:
            doc.metadata["source"] = os.path.basename(
                doc.metadata.get("source", file_path)
            )

    return _split_documents(pages)


def build_or_update_index(docs: list, index_path: str = INDEX_PATH) -> FAISS:
    """
    Create a new FAISS index or merge new docs into an existing one.
    Saves the index to disk at `index_path`.
    """
    embeddings = get_embeddings()

    if os.path.exists(index_path):
        vector_store = FAISS.load_local(
            index_path, embeddings, allow_dangerous_deserialization=True
        )
        vector_store.add_documents(docs)
    else:
        vector_store = FAISS.from_documents(docs, embeddings)

    vector_store.save_local(index_path)
    return vector_store


def load_vector_store(index_path: str = INDEX_PATH) -> FAISS | None:
    """Load FAISS index from disk. Returns None if index doesn't exist."""
    if not os.path.exists(index_path):
        return None
    embeddings = get_embeddings()
    return FAISS.load_local(
        index_path, embeddings, allow_dangerous_deserialization=True
    )


def seed_builtin_index() -> FAISS | None:
    """
    Load the FAISS index if it exists on disk.
    If not, attempt to build it from the data/ directory (Memory intensive).
    """
    if os.path.exists(INDEX_PATH):
        print(f"[INFO] Loading existing FAISS index from '{INDEX_PATH}'...")
        return load_vector_store(INDEX_PATH)

    print("[INFO] No index found. Checking for built-in knowledge in 'data/'...")
    chunks = load_builtin_knowledge()
    if not chunks:
        print(f"[WARN] No knowledge base found to index.")
        return None

    print(f"[INFO] Indexing {len(chunks)} chunks... (WARNING: This may exceed memory on free-tier cloud)")
    vector_store = build_or_update_index(chunks, INDEX_PATH)
    return vector_store
