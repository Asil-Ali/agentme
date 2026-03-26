"""
AgentMe — RAG Core Engine
=========================
The heart of the system. Handles:
- Document ingestion (PDF, TXT, DOCX, raw text)
- Per-user isolated Vector Store (ChromaDB)
- Intelligent retrieval with metadata filtering
- Context window management
- Graceful error handling
"""

import os
import uuid
import logging
from typing import Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain.schema import Document

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

CHROMA_PATH       = os.getenv("CHROMA_PATH", "./data/chroma")
EMBED_MODEL       = "sentence-transformers/all-MiniLM-L6-v2"  # Free, fast, multilingual
CHUNK_SIZE        = 800    # Sweet spot: enough context, not too much noise
CHUNK_OVERLAP     = 150    # Overlap prevents losing context at chunk boundaries
MAX_RETRIEVAL_K   = 5      # Top-K docs to retrieve per query
MAX_TOKENS_BUDGET = 3000   # Approx token budget for RAG context in prompt


# ──────────────────────────────────────────────
# Embeddings — loaded once, reused everywhere
# ──────────────────────────────────────────────

def get_embeddings():
    """
    Load embedding model once.
    all-MiniLM-L6-v2:
      - Free & local (no API cost)
      - 384 dimensions (fast)
      - Solid multilingual support
    """
    return DefaultEmbeddingFunction()


_embeddings = None

def get_embeddings_singleton():
    """Singleton — load model only once per process."""
    global _embeddings
    if _embeddings is None:
        logger.info("Loading embedding model (first time)...")
        _embeddings = get_embeddings()
    return _embeddings


# ──────────────────────────────────────────────
# Document Loaders
# ──────────────────────────────────────────────

def load_document(file_path: str) -> list[Document]:
    """
    Load a document from disk.
    Supports: PDF, TXT, MD
    Each doc tagged with source metadata for filtering later.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext in (".txt", ".md"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: PDF, TXT, MD")

    docs = loader.load()

    # Tag each doc with source type for metadata filtering
    for doc in docs:
        doc.metadata["source_file"] = path.name
        doc.metadata["source_type"] = ext.strip(".")

    logger.info(f"Loaded {len(docs)} pages from {path.name}")
    return docs


def load_raw_text(text: str, source_label: str = "manual_input") -> list[Document]:
    """
    Accept raw text directly (e.g. skills description, bio typed by user).
    """
    if not text.strip():
        raise ValueError("Cannot ingest empty text.")

    return [Document(
        page_content=text,
        metadata={"source_file": source_label, "source_type": "text"}
    )]


# ──────────────────────────────────────────────
# Text Splitter
# ──────────────────────────────────────────────

def split_documents(docs: list[Document]) -> list[Document]:
    """
    Split documents into chunks.

    Why RecursiveCharacterTextSplitter?
    - Tries to split on paragraphs → sentences → words (in order)
    - Preserves semantic meaning better than fixed splits
    - Overlap prevents losing context at boundaries
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    logger.info(f"Split into {len(chunks)} chunks")
    return chunks


# ──────────────────────────────────────────────
# Vector Store — Per-User Isolation
# ──────────────────────────────────────────────

def get_user_collection_name(user_id: str) -> str:
    """
    Each user gets their own ChromaDB collection.
    This is the security boundary — User A never sees User B's data.
    Format: 'agent_{user_id}' (ChromaDB requires alphanumeric + underscores)
    """
    # Sanitize user_id to be safe for collection names
    safe_id = "".join(c if c.isalnum() else "_" for c in user_id)
    return f"agent_{safe_id}"


def get_vector_store(user_id: str) -> Chroma:
    """
    Get (or create) the vector store for a specific user.
    Uses persistent ChromaDB — survives server restarts.
    """
    collection_name = get_user_collection_name(user_id)

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings_singleton(),
        persist_directory=CHROMA_PATH,
    )
    return vector_store


# ──────────────────────────────────────────────
# Ingestion Pipeline
# ──────────────────────────────────────────────

def ingest_file(user_id: str, file_path: str, doc_type: str = "general") -> dict:
    """
    Full pipeline: Load → Split → Embed → Store

    Args:
        user_id:   The user who owns this document
        file_path: Path to the file on disk
        doc_type:  Label like 'cv', 'portfolio', 'skills', 'bio'

    Returns:
        Summary dict with chunk count and status
    """
    try:
        # 1. Load
        docs = load_document(file_path)

        # 2. Tag with doc_type for smart retrieval later
        for doc in docs:
            doc.metadata["doc_type"] = doc_type
            doc.metadata["user_id"] = user_id
            doc.metadata["chunk_id"] = str(uuid.uuid4())

        # 3. Split
        chunks = split_documents(docs)

        # 4. Store in user's isolated vector store
        vector_store = get_vector_store(user_id)
        vector_store.add_documents(chunks)

        logger.info(f"✅ Ingested {len(chunks)} chunks for user {user_id} | type: {doc_type}")

        return {
            "status": "success",
            "chunks_added": len(chunks),
            "doc_type": doc_type,
            "file": Path(file_path).name,
        }

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return {"status": "error", "message": str(e)}

    except Exception as e:
        logger.error(f"Ingestion failed for user {user_id}: {e}")
        return {"status": "error", "message": f"Ingestion failed: {str(e)}"}


def ingest_text(user_id: str, text: str, doc_type: str = "bio") -> dict:
    """
    Ingest raw text (typed by user, not a file).
    Same pipeline, different entry point.
    """
    try:
        docs = load_raw_text(text, source_label=doc_type)

        for doc in docs:
            doc.metadata["doc_type"] = doc_type
            doc.metadata["user_id"] = user_id
            doc.metadata["chunk_id"] = str(uuid.uuid4())

        chunks = split_documents(docs)
        vector_store = get_vector_store(user_id)
        vector_store.add_documents(chunks)

        return {
            "status": "success",
            "chunks_added": len(chunks),
            "doc_type": doc_type,
        }

    except Exception as e:
        logger.error(f"Text ingestion failed: {e}")
        return {"status": "error", "message": str(e)}


# ──────────────────────────────────────────────
# Retrieval
# ──────────────────────────────────────────────

def retrieve_context(
    user_id: str,
    query: str,
    k: int = MAX_RETRIEVAL_K,
    doc_type_filter: Optional[str] = None,
) -> str:
    """
    Retrieve the most relevant chunks for a query.

    Args:
        user_id:         The user whose knowledge base to search
        query:           The user's question or task
        k:               How many chunks to retrieve
        doc_type_filter: Optional — only search in 'cv', 'portfolio', etc.

    Returns:
        Formatted context string ready to inject into prompt
    """
    try:
        vector_store = get_vector_store(user_id)

        # Optional metadata filter
        search_kwargs = {"k": k}
        if doc_type_filter:
            search_kwargs["filter"] = {"doc_type": doc_type_filter}

        retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
        docs = retriever.invoke(query)

        if not docs:
            return ""

        # Format context with source labels — helps LLM understand structure
        context_parts = []
        total_chars = 0

        for doc in docs:
            doc_type = doc.metadata.get("doc_type", "general")
            content = doc.page_content.strip()

            # Token budget guard — prevent context overflow
            if total_chars + len(content) > MAX_TOKENS_BUDGET * 4:
                logger.warning("Token budget reached, truncating context")
                break

            context_parts.append(f"[{doc_type.upper()}]\n{content}")
            total_chars += len(content)

        return "\n\n---\n\n".join(context_parts)

    except Exception as e:
        logger.error(f"Retrieval failed for user {user_id}: {e}")
        return ""  # Graceful degradation — don't crash the chat


# ──────────────────────────────────────────────
# User Management
# ──────────────────────────────────────────────

def delete_user_knowledge(user_id: str) -> dict:
    """
    Completely wipe a user's vector store.
    GDPR compliance / user account deletion.
    """
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection_name = get_user_collection_name(user_id)
        client.delete_collection(collection_name)
        logger.info(f"Deleted knowledge base for user {user_id}")
        return {"status": "success", "message": "Knowledge base deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_user_knowledge_stats(user_id: str) -> dict:
    """
    How many chunks does this user have?
    Useful for dashboard display.
    """
    try:
        vector_store = get_vector_store(user_id)
        count = vector_store._collection.count()
        return {"status": "success", "total_chunks": count}
    except Exception:
        return {"status": "success", "total_chunks": 0}
