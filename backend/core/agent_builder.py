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

import anthropic

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
# Claude Client
# ──────────────────────────────────────────────

claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CLAUDE_MODEL   = "claude-sonnet-4-5"
MAX_TOKENS     = 1024
HISTORY_LIMIT  = 10  # Keep last N messages to avoid token overflow


# ──────────────────────────────────────────────
# Intent Detection
# ──────────────────────────────────────────────

def detect_intent(user_message: str) -> dict:
    """
    Classify user intent before responding.
    This lets us pick the right prompt and RAG filter.

    Returns dict with: intent, confidence, suggested_tone, key_topics
    Falls back to 'general' on any error.
    """
    try:
        prompt = detect_intent_prompt(user_message)

        response = claude.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()

        # Strip markdown code fences if present
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
    """
    Format conversation history for injection into prompt.
    Limits to last N turns to manage token budget.
    """
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

    Flow:
    1. Detect intent
    2. Retrieve relevant context from RAG
    3. Build appropriate prompt
    4. Call Claude
    5. Return response + metadata

    Args:
        user_id:              The profile owner (whose knowledge base to use)
        agent_name:           Display name of the agent (e.g. "Alex")
        agent_specialty:      e.g. "AI Engineering and RAG Systems"
        user_message:         What the visitor typed
        conversation_history: List of {"role": "user"/"assistant", "content": "..."}

    Returns:
        {
            "response": "...",
            "intent": "...",
            "sources_used": int,
            "error": None or "..."
        }
    """
    try:
        # Step 1 — Detect intent
        intent_data = detect_intent(user_message)
        intent = intent_data.get("intent", "other")

        logger.info(f"Intent detected: {intent} (confidence: {intent_data.get('confidence')})")

        # Step 2 — Smart retrieval based on intent
        # Different intents prioritize different doc types
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

        # Step 4 — Call Claude
        response = claude.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": full_prompt}],
        )

        answer = response.content[0].text.strip()

        return {
            "response": answer,
            "intent": intent,
            "intent_confidence": intent_data.get("confidence"),
            "sources_used": len(context.split("---")) if context else 0,
            "error": None,
        }

    except anthropic.AuthenticationError:
        logger.error("Claude API authentication failed")
        return {
            "response": "I'm having trouble connecting right now. Please try again shortly.",
            "intent": "error",
            "sources_used": 0,
            "error": "auth_error",
        }

    except anthropic.RateLimitError:
        logger.warning("Claude API rate limit hit")
        return {
            "response": "I'm receiving a lot of messages right now. Please try again in a moment.",
            "intent": "error",
            "sources_used": 0,
            "error": "rate_limit",
        }

    except Exception as e:
        logger.error(f"Agent chat failed: {e}")
        return {
            "response": "Something went wrong on my end. Please try again.",
            "intent": "error",
            "sources_used": 0,
            "error": str(e),
        }


# ──────────────────────────────────────────────
# Proposal Generation
# ──────────────────────────────────────────────

def generate_proposal(
    user_id: str,
    agent_name: str,
    job_description: str,
) -> dict:
    """
    Generate a tailored project proposal.
    Retrieves profile context then writes a compelling proposal.
    """
    try:
        # Get broad profile context for proposal
        context = retrieve_context(user_id=user_id, query=job_description, k=6)

        prompt = build_proposal_prompt(
            name=agent_name,
            profile_context=context,
            job_description=job_description,
        )

        response = claude.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "proposal": response.content[0].text.strip(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Proposal generation failed: {e}")
        return {"proposal": "", "status": "error", "message": str(e)}


# ──────────────────────────────────────────────
# Job Analysis
# ──────────────────────────────────────────────

def analyze_job(user_id: str, job_description: str) -> dict:
    """
    Analyze a job posting against the user's profile.
    Returns match score, gaps, and recommendations.
    """
    try:
        context = retrieve_context(user_id=user_id, query=job_description, k=6)

        prompt = build_job_analysis_prompt(
            profile_context=context,
            job_description=job_description,
        )

        response = claude.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        return {
            "analysis": json.loads(raw),
            "status": "success",
        }

    except json.JSONDecodeError:
        return {"analysis": {}, "status": "error", "message": "Failed to parse analysis"}
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
    """
    Generate a personalized LinkedIn outreach message.
    """
    try:
        context = retrieve_context(
            user_id=user_id,
            query=f"services skills experience {purpose}",
            k=4,
        )

        prompt = build_linkedin_message_prompt(
            name=agent_name,
            profile_context=context,
            target_info=target_info,
            purpose=purpose,
            message_type=message_type,
            language=language,
        )

        response = claude.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "message": response.content[0].text.strip(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"LinkedIn message generation failed: {e}")
        return {"message": "", "status": "error", "message": str(e)}
