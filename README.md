# agentme
🤖 AgentMe — Personal AI Agent Platform
"Your AI Twin on LinkedIn"
A platform that turns any professional into an AI Agent — answering questions, generating proposals, analyzing jobs, and writing LinkedIn messages on their behalf.
🏗️ Architecture
Frontend (Next.js) → FastAPI Backend → LangChain + ChromaDB → Claude API
Per-user isolation: Every user gets their own ChromaDB collection. User A never sees User B's data.
🚀 Quick Start
1. Clone & Setup
git clone https://github.com/yourname/agentme
cd agentme/backend

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
2. Environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
3. Run
uvicorn main:app --reload --port 8000
API docs at: http://localhost:8000/docs
📡 API Endpoints
Ingest Documents
# Upload a PDF
curl -X POST "http://localhost:8000/ingest/file?user_id=alex123&doc_type=cv" \
  -F "file=@my_cv.pdf"

# Add raw text
curl -X POST "http://localhost:8000/ingest/text" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alex123",
    "text": "I specialize in building RAG systems and AI Agents...",
    "doc_type": "bio"
  }'
Chat with Agent
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alex123",
    "agent_name": "Alex",
    "agent_specialty": "AI Engineering and RAG Systems",
    "user_message": "What are your main services?",
    "conversation_history": []
  }'
Generate Proposal
curl -X POST "http://localhost:8000/generate/proposal" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alex123",
    "agent_name": "Alex",
    "job_description": "We need a RAG chatbot for our internal documentation..."
  }'
Analyze a Job
curl -X POST "http://localhost:8000/analyze/job" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alex123",
    "job_description": "Senior AI Engineer — LangChain, RAG, Python required..."
  }'
📁 Project Structure
agentme/
├── backend/
│   ├── main.py              ← FastAPI app & all endpoints
│   ├── requirements.txt
│   ├── .env.example
│   └── core/
│       ├── rag_engine.py    ← Document ingestion & retrieval
│       ├── prompts.py       ← All prompt templates (layered architecture)
│       └── agent_builder.py ← Chat, proposals, job analysis, LinkedIn
└── frontend/                ← Next.js (coming in Phase 2)
🧠 Prompt Architecture
Prompts are layered:
Identity — Who is this agent?
Context — RAG-retrieved knowledge
Intent — What does the user want? (hiring/technical/curious/pricing)
Task — Specific output format
Guardrails — What must never happen
🔒 Security
Each user has an isolated ChromaDB collection: agent_{user_id}
No cross-user data access possible at the retrieval level
Guardrails prevent sharing private info or fabricating credentials
JWT auth (add your own user table in Phase 2)
📈 Roadmap
[x] Phase 1: RAG Core Engine
[x] Phase 1: Prompt Architecture
[x] Phase 1: All Agent Capabilities (chat, proposal, job analysis, LinkedIn)
[ ] Phase 2: Next.js Frontend + Dashboard
[ ] Phase 2: User Auth + Multi-tenant
[ ] Phase 3: LinkedIn Automation (Selenium)
[ ] Phase 4: Analytics Dashboard
[ ] Phase 4: SaaS Monetization
💡 Tech Stack
Layer
Technology
LLM
Claude Sonnet (Anthropic)
RAG
LangChain + ChromaDB
Embeddings
sentence-transformers (free, local)
API
FastAPI
Frontend
Next.js + Tailwind (Phase 2)
Hosting
Railway (back) + Vercel (front)
Built by [Your Name] — AI Agent & RAG Systems Specialist
