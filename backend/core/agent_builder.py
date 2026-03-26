"""
AgentMe — Agent Builder
========================
This is where RAG + Prompts + Claude API come together.

Responsibilities:
- Build and run the chat agent for a specific user
- Detect intent before responding
- Select the right prompt based on intent
- Call Claude API with full context
- Manage conversation history
- Handle all failure modes gracefully
"""

import json
import logging
import os
from typing import Optional

# استبدال مكتبة anthropic بمكتبة Google GenAI المتوافقة مع LangChain
from langchain_google_genai import ChatGoogleGenerativeAI
from core.rag_engine import retrieve_context
from core.prompts import (
    build_chat_prompt,
    build_proposal_prompt,
    build_job_analysis_prompt,
    build_linkedin_message_prompt,
    detect_intent_prompt,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Google Gemini Client (Free Tier Friendly)
# ──────────────────────────────────────────────

# نستخدم Gemini 1.5 Pro للمهام التي تتطلب ذكاءً عالياً والـ Flash للسرعة
llm_pro = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro", 
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7
)

llm_fast = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", 
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.1 # حرارة منخفضة لثبات النتائج في تصنيف النية
)

MAX_TOKENS     = 1024
HISTORY_LIMIT  = 10 

# ──────────────────────────────────────────────
# Intent Detection
# ──────────────────────────────────────────────

def detect_intent(user_message: str) -> dict:
    """
    Classify user intent before responding.
    Returns dict with: intent, confidence, suggested_tone, key_topics
    """
    try:
        prompt = detect_intent_prompt(user_message)

        # استدعاء Gemini Flash بدلاً من Claude
        response = llm_fast.invoke(prompt)
        raw = response.content.strip()

        # تنظيف الـ JSON من أي Markdown
        raw = raw.replace("```json", "").replace("```", "").strip()

        return json.loads(raw)

    except Exception as e:
        logger.warning(f"Intent detection failed: {e} — falling back to 'other'")
        return {
            "intent": "other",
            "confidence": 0.5,
            "suggested_tone": "friendly",
            "key_topics": [],
        }

# ──────────────────────────────────────────────
# Format Conversation History
# ──────────────────────────────────────────────

def format_history(messages: list[dict]) -> str:
    recent = messages[-HISTORY_LIMIT:]
    lines = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Agent"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)

# ──────────────────────────────────────────────
# Main Chat Function
# ──────────────────────────────────────────────

def chat_with_agent(
    user_id: str,
    agent_name: str,
    agent_specialty: str,
    user_message: str,
    conversation_history: list[dict],
) -> dict:
    """
    Main entry point for chat.
    Flow: Intent -> RAG (with Filter) -> Prompt -> Gemini
    """
    try:
        # Step 1 — Detect intent
        intent_data = detect_intent(user_message)
        intent = intent_data.get("intent", "other")

        logger.info(f"Intent detected: {intent}")

        # Step 2 — Smart retrieval based on intent (نفس منطقك الأصلي)
        doc_type_filter = None
        if intent == "hiring":
            doc_type_filter = "cv"
        elif intent == "technical":
            doc_type_filter = "portfolio"
        elif intent == "pricing":
            doc_type_filter = "services"

        context = retrieve_context(
            user_id=user_id,
            query=user_message,
            k=5,
            doc_type_filter=doc_type_filter,
        )

        # Fallback — if filtered search returns nothing, search all
        if not context and doc_type_filter:
            context = retrieve_context(user_id=user_id, query=user_message, k=5)

        # Step 3 — Build prompt
        history_str = format_history(conversation_history)

        full_prompt = build_chat_prompt(
            name=agent_name,
            specialty=agent_specialty,
            context=context,
            history=history_str,
            user_message=user_message,
        )

        # Step 4 — Call Gemini Pro
        response = llm_pro.invoke(full_prompt)
        answer = response.content.strip()

        return {
            "response": answer,
            "intent": intent,
            "intent_confidence": intent_data.get("confidence"),
            "sources_used": len(context.split("---")) if context else 0,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Agent chat failed: {e}")
        return {
            "response": "I'm having trouble processing that right now. Please try again.",
            "intent": "error",
            "sources_used": 0,
            "error": str(e),
        }

# ──────────────────────────────────────────────
# Proposal Generation
# ──────────────────────────────────────────────

def generate_proposal(user_id: str, agent_name: str, job_description: str) -> dict:
    try:
        context = retrieve_context(user_id=user_id, query=job_description, k=6)
        prompt = build_proposal_prompt(
            name=agent_name,
            profile_context=context,
            job_description=job_description,
        )

        response = llm_pro.invoke(prompt)

        return {
            "proposal": response.content.strip(),
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Proposal generation failed: {e}")
        return {"proposal": "", "status": "error", "message": str(e)}

# ──────────────────────────────────────────────
# Job Analysis
# ──────────────────────────────────────────────

def analyze_job(user_id: str, job_description: str) -> dict:
    try:
        context = retrieve_context(user_id=user_id, query=job_description, k=6)
        prompt = build_job_analysis_prompt(
            profile_context=context,
            job_description=job_description,
        )

        response = llm_pro.invoke(prompt)
        raw = response.content.strip().replace("```json", "").replace("```", "").strip()

        return {
            "analysis": json.loads(raw),
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Job analysis failed: {e}")
        return {"analysis": {}, "status": "error", "message": str(e)}

# ──────────────────────────────────────────────
# LinkedIn Message Generator
# ──────────────────────────────────────────────

def generate_linkedin_message(
    user_id: str,
    agent_name: str,
    target_info: str,
    purpose: str,
    message_type: str = "connection_request",
    language: str = "English",
) -> dict:
    try:
        context = retrieve_context(user_id=user_id, query=f"services skills {purpose}", k=4)
        prompt = build_linkedin_message_prompt(
            name=agent_name,
            profile_context=context,
            target_info=target_info,
            purpose=purpose,
            message_type=message_type,
            language=language,
        )

        response = llm_pro.invoke(prompt)

        return {
            "message": response.content.strip(),
            "status": "success",
        }
    except Exception as e:
        logger.error(f"LinkedIn message failed: {e}")
        return {"message": "", "status": "error", "message": str(e)}
