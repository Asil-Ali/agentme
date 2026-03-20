const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export const AgentAPI = {

  async chat(userMessage: string, history: {role: string, content: string}[]) {
    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "default_user",
        agent_name: "Alex",
        agent_specialty: "AI Engineering and RAG Systems",
        user_message: userMessage,
        conversation_history: history,
      }),
    });
    const data = await res.json();
    return data.response;
  },

  async generateProposal(jobDescription: string) {
    const res = await fetch(`${BACKEND_URL}/generate/proposal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "default_user",
        agent_name: "Alex",
        job_description: jobDescription,
      }),
    });
    const data = await res.json();
    return data.proposal;
  },

};