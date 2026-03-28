const BACKEND_URL = "https://agentme.onrender.com";

export const AgentAPI = {
  async chat(userMessage: string, history: {role: string, content: string}[]) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 90000);
    
    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          user_id: "default_user",
          agent_name: "Aseel",
          agent_specialty: "AI Engineering and RAG Systems",
          user_message: userMessage,
          conversation_history: history,
        }),
      });
      const data = await res.json();
      return data.response || "Sorry, no response received.";
    } catch (e) {
      throw e;
    } finally {
      clearTimeout(timeout);
    }
  },

  async generateProposal(jobDescription: string) {
    const res = await fetch(`${BACKEND_URL}/generate/proposal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "default_user",
        agent_name: "Aseel",
        job_description: jobDescription,
      }),
    });
    const data = await res.json();
    return data.proposal;
  },
};
