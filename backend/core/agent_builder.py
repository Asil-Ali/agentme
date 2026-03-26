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
from langchain_google_genai import ChatGoogleGenerativeAI
from core.rag_engine import retrieve_context
from core.prompts import (
    build_chat_prompt, build_proposal_prompt,
    build_job_analysis_prompt, build_linkedin_message_prompt,
    detect_intent_prompt,
)

logger = logging.getLogger(__name__)

# المحركات (استخدام Gemini Pro للمهام المعقدة و Flash للسرعة)
llm_fast = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
llm_pro = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=os.getenv("GOOGLE_API_KEY"))

def detect_intent(user_message: str) -> dict:
    try:
        prompt = detect_intent_prompt(user_message)
        response = llm_fast.invoke(prompt)
        raw = response.content.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Intent detection failed: {e}")
        return {"intent": "other", "confidence": 0.5}

def chat_with_agent(user_id, agent_name, agent_specialty, user_message, conversation_history) -> dict:
    try:
        intent_data = detect_intent(user_message)
        intent = intent_data.get("intent", "other")
        
        # الذكاء في اختيار الفلتر
        doc_filter = {"hiring": "cv", "technical": "portfolio", "pricing": "services"}.get(intent)
        
        context = retrieve_context(user_id=user_id, query=user_message, doc_type_filter=doc_filter)
        
        full_prompt = build_chat_prompt(
            name=agent_name, specialty=agent_specialty,
            context=context, history="", user_message=user_message
        )
        
        response = llm_pro.invoke(full_prompt)
        
        return {
            "response": response.content.strip(),
            "intent": intent,
            "sources_used": len(context.split("---")) if context else 0,
            "error": None
        }
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        return {"response": "Something went wrong on my end.", "error": str(e)}

def generate_proposal(user_id, agent_name, job_description) -> dict:
    try:
        context = retrieve_context(user_id=user_id, query=job_description, k=6)
        prompt = build_proposal_prompt(name=agent_name, profile_context=context, job_description=job_description)
        response = llm_pro.invoke(prompt)
        return {"proposal": response.content.strip(), "status": "success"}
    except Exception as e:
        return {"proposal": "", "status": "error", "message": str(e)}

def analyze_job(user_id, job_description) -> dict:
    try:
        context = retrieve_context(user_id=user_id, query=job_description, k=6)
        prompt = build_job_analysis_prompt(profile_context=context, job_description=job_description)
        response = llm_pro.invoke(prompt)
        raw = response.content.strip().replace("```json", "").replace("```", "").strip()
        return {"analysis": json.loads(raw), "status": "success"}
    except Exception as e:
        return {"analysis": {}, "status": "error", "message": str(e)}

