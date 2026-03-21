"""
AgentMe — FastAPI Backend
==========================
REST API exposing all agent capabilities.

Endpoints:
  POST /ingest/file          Upload a document to knowledge base
  POST /ingest/text          Add raw text to knowledge base
  POST /chat                 Chat with the agent
  POST /generate/proposal    Generate a project proposal
  POST /analyze/job          Analyze a job posting
  POST /generate/linkedin    Generate LinkedIn message
  GET  /stats/{user_id}      Knowledge base stats
  DELETE /user/{user_id}     Delete user's knowledge base
"""

import os
import shutil
import tempfile
import logging
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.rag_engine import (
    ingest_file,
    ingest_text,
    get_user_knowledge_stats,
    delete_user_knowledge,
)
from core.agent_builder import (
    chat_with_agent,
    generate_proposal,
    analyze_job,
    generate_linkedin_message,
)

# ──────────────────────────────────────────────
# App Setup
# ──────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AgentMe API",
    description="Personal AI Agent Platform — RAG + Agentic AI",
    version="1.0.0",
)

# CORS — allow frontend (Next.js) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Request / Response Models
# ──────────────────────────────────────────────

class IngestTextRequest(BaseModel):
    user_id: str
    text: str
    doc_type: str = "bio"  # bio | skills | services | portfolio | other


class ChatRequest(BaseModel):
    user_id: str
    agent_name: str
    agent_specialty: str
    user_message: str
    conversation_history: list[dict] = []


class ProposalRequest(BaseModel):
    user_id: str
    agent_name: str
    job_description: str


class JobAnalysisRequest(BaseModel):
    user_id: str
    job_description: str


class LinkedInRequest(BaseModel):
    user_id: str
    agent_name: str
    target_info: str
    purpose: str
    message_type: str = "connection_request"
    language: str = "English"


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────

@app.get("/")
def health_check():
    return {"status": "AgentMe API is running 🚀", "version": "1.0.0"}


# ──────────────────────────────────────────────
# Ingestion Endpoints
# ──────────────────────────────────────────────

@app.post("/ingest/file")
async def ingest_file_endpoint(
    user_id: str,
    doc_type: str = "general",
    file: UploadFile = File(...),
):
    """
    Upload a file (PDF, TXT, MD) to the user's knowledge base.
    doc_type: cv | portfolio | skills | services | bio | general
    """

    # Validate file type
    allowed_extensions = {".pdf", ".txt", ".md"}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' not supported. Use: PDF, TXT, or MD"
        )

    # Save to temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        result = ingest_file(
            user_id=user_id,
            file_path=tmp_path,
            doc_type=doc_type,
        )

        return result

    finally:
        # Always clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/ingest/text")
def ingest_text_endpoint(request: IngestTextRequest):
    """Add raw text to user's knowledge base."""

    if len(request.text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Text too short (minimum 10 characters)")

    return ingest_text(
        user_id=request.user_id,
        text=request.text,
        doc_type=request.doc_type,
    )


# ──────────────────────────────────────────────
# Agent Endpoints
# ──────────────────────────────────────────────

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    """
    Chat with a user's AI Agent.
    This is the main endpoint used by the chat widget.
    """
    if not request.user_message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return chat_with_agent(
        user_id=request.user_id,
        agent_name=request.agent_name,
        agent_specialty=request.agent_specialty,
        user_message=request.user_message,
        conversation_history=request.conversation_history,
    )


@app.post("/generate/proposal")
def proposal_endpoint(request: ProposalRequest):
    """Generate a tailored project proposal."""

    if len(request.job_description.strip()) < 20:
        raise HTTPException(status_code=400, detail="Job description too short")

    return generate_proposal(
        user_id=request.user_id,
        agent_name=request.agent_name,
        job_description=request.job_description,
    )


@app.post("/analyze/job")
def job_analysis_endpoint(request: JobAnalysisRequest):
    """Analyze a job posting against user's profile."""

    return analyze_job(
        user_id=request.user_id,
        job_description=request.job_description,
    )


@app.post("/generate/linkedin")
def linkedin_message_endpoint(request: LinkedInRequest):
    """Generate a LinkedIn outreach message."""

    return generate_linkedin_message(
        user_id=request.user_id,
        agent_name=request.agent_name,
        target_info=request.target_info,
        purpose=request.purpose,
        message_type=request.message_type,
        language=request.language,
    )


# ──────────────────────────────────────────────
# User Management
# ──────────────────────────────────────────────

@app.get("/stats/{user_id}")
def stats_endpoint(user_id: str):
    """Get knowledge base stats for a user."""
    return get_user_knowledge_stats(user_id)


@app.delete("/user/{user_id}")
def delete_user_endpoint(user_id: str):
    """Delete user's entire knowledge base (GDPR compliance)."""
    return delete_user_knowledge(user_id)
