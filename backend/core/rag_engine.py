import os
import uuid
import logging
from typing import Optional
from pathlib import Path

import chromadb
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

CHROMA_PATH       = os.getenv("CHROMA_PATH", "./data/chroma")
CHUNK_SIZE        = 800    
CHUNK_OVERLAP     = 150    
MAX_RETRIEVAL_K   = 5      
MAX_TOKENS_BUDGET = 3000   

# ──────────────────────────────────────────────
# Embeddings — API-Based (RAM Friendly)
# ──────────────────────────────────────────────

_embeddings = None

def get_embeddings_singleton():
    """استخدام Google API للـ Embeddings لتوفير رامات السيرفر."""
    global _embeddings
    if _embeddings is None:
        logger.info("Loading Google Generative AI Embeddings...")
        _embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    return _embeddings

# ──────────────────────────────────────────────
# Document Loaders & Raw Text
# ──────────────────────────────────────────────

def load_document(file_path: str) -> list[Document]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    ext = path.suffix.lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext in (".txt", ".md"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    docs = loader.load()
    for doc in docs:
        doc.metadata["source_file"] = path.name
        doc.metadata["source_type"] = ext.strip(".")
    return docs

def load_raw_text(text: str, source_label: str = "manual_input") -> list[Document]:
    """مهمة إدخال النص المباشر (موجودة ولم تُحذف)."""
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
    """تقسيم النصوص الذكي (Recursive Splitting)."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)

# ──────────────────────────────────────────────
# Vector Store — Per-User Isolation
# ──────────────────────────────────────────────

def get_user_collection_name(user_id: str) -> str:
    safe_id = "".join(c if c.isalnum() else "_" for c in user_id)
    return f"agent_{safe_id}"

def get_vector_store(user_id: str) -> Chroma:
    return Chroma(
        collection_name=get_user_collection_name(user_id),
        embedding_function=get_embeddings_singleton(),
        persist_directory=CHROMA_PATH,
    )

# ──────────────────────────────────────────────
# Ingestion Pipelines (Files & Raw Text)
# ──────────────────────────────────────────────

def ingest_file(user_id: str, file_path: str, doc_type: str = "general") -> dict:
    try:
        docs = load_document(file_path)
        for doc in docs:
            doc.metadata.update({"doc_type": doc_type, "user_id": user_id, "chunk_id": str(uuid.uuid4())})
        
        chunks = split_documents(docs)
        vector_store = get_vector_store(user_id)
        vector_store.add_documents(chunks)
        
        logger.info(f"✅ Ingested {len(chunks)} chunks for user {user_id}")
        return {"status": "success", "chunks_added": len(chunks), "file": Path(file_path).name}
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return {"status": "error", "message": str(e)}

def ingest_text(user_id: str, text: str, doc_type: str = "bio") -> dict:
    """إدخال النص اليدوي (كاملة كما في ملفك الأصلي)."""
    try:
        docs = load_raw_text(text, source_label=doc_type)
        for doc in docs:
            doc.metadata.update({"doc_type": doc_type, "user_id": user_id, "chunk_id": str(uuid.uuid4())})
        
        chunks = split_documents(docs)
        vector_store = get_vector_store(user_id)
        vector_store.add_documents(chunks)
        return {"status": "success", "chunks_added": len(chunks)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ──────────────────────────────────────────────
# Retrieval & Context Management
# ──────────────────────────────────────────────

def retrieve_context(user_id: str, query: str, k: int = MAX_RETRIEVAL_K, doc_type_filter: Optional[str] = None) -> str:
    try:
        vector_store = get_vector_store(user_id)
        search_kwargs = {"k": k}
        if doc_type_filter:
            search_kwargs["filter"] = {"doc_type": doc_type_filter}
        
        retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
        docs = retriever.invoke(query)

        # Fallback إذا لم نجد نتائج بالفلتر
        if not docs and doc_type_filter:
            docs = vector_store.as_retriever(search_kwargs={"k": k}).invoke(query)

        context_parts = []
        total_chars = 0
        for doc in docs:
            content = doc.page_content.strip()
            if total_chars + len(content) > MAX_TOKENS_BUDGET * 4: break
            context_parts.append(f"[{doc.metadata.get('doc_type', 'general').upper()}]\n{content}")
            total_chars += len(content)

        return "\n\n---\n\n".join(context_parts)
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        return ""

# ──────────────────────────────────────────────
# User Management (Deletion & Stats)
# ──────────────────────────────────────────────

def delete_user_knowledge(user_id: str) -> dict:
    """حذف بيانات المستخدم (كاملة كما في ملفك الأصلي)."""
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection_name = get_user_collection_name(user_id)
        client.delete_collection(collection_name)
        return {"status": "success", "message": "Knowledge base deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_user_knowledge_stats(user_id: str) -> dict:
    """إحصائيات بيانات المستخدم (كاملة كما في ملفك الأصلي)."""
    try:
        vector_store = get_vector_store(user_id)
        count = vector_store._collection.count()
        return {"status": "success", "total_chunks": count}
    except Exception:
        return {"status": "success", "total_chunks": 0}
