"""
AgentMe — FastAPI Backend
==========================
REST API exposing all agent capabilities.
"""

import os
import shutil
import tempfile
import logging
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# استيراد الدوال من الملفات اللي عدلناها
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

# CORS — السماح للفرونت إيند بالوصول للباك إيند
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
    doc_type: str = "bio"

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
# Endpoints
# ──────────────────────────────────────────────

@app.get("/")
def health_check():
    return {"status": "AgentMe API is running 🚀", "version": "1.0.0"}

@app.post("/ingest/file")
async def ingest_file_endpoint(
    user_id: str,
    doc_type: str = "general",
    file: UploadFile = File(...),
):
    allowed_extensions = {".pdf", ".txt", ".md"}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file: {file_ext}")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        return ingest_file(user_id=user_id, file_path=tmp_path, doc_type=doc_type)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.post("/ingest/text")
def ingest_text_endpoint(request: IngestTextRequest):
    return ingest_text(user_id=request.user_id, text=request.text, doc_type=request.doc_type)

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    # الـ chat_with_agent الآن بتستخدم جيمناي داخلياً
    return chat_with_agent(
        user_id=request.user_id,
        agent_name=request.agent_name,
        agent_specialty=request.agent_specialty,
        user_message=request.user_message,
        conversation_history=request.conversation_history,
    )

@app.post("/generate/proposal")
def proposal_endpoint(request: ProposalRequest):
    return generate_proposal(request.user_id, request.agent_name, request.job_description)

@app.post("/analyze/job")
def job_analysis_endpoint(request: JobAnalysisRequest):
    return analyze_job(request.user_id, request.job_description)

@app.post("/generate/linkedin")
def linkedin_message_endpoint(request: LinkedInRequest):
    return generate_linkedin_message(
        request.user_id, request.agent_name, request.target_info, 
        request.purpose, request.message_type, request.language
    )

@app.get("/stats/{user_id}")
def stats_endpoint(user_id: str):
    return get_user_knowledge_stats(user_id)

@app.delete("/user/{user_id}")
def delete_user_endpoint(user_id: str):
    return delete_user_knowledge(user_id)
