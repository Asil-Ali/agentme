"use client";
import { AgentAPI } from "./api-client";
import { useState, useEffect, useRef } from "react";

const QUESTIONS = [
  "Can you build a RAG system for us?",
  "What AI services do you offer?",
  "Are you available for projects?",
  "Tell me about your experience.",
  "How much does it cost?",
];

const DEMO_RESPONSES = {
  rag: "Absolutely. I build production-grade RAG systems using LangChain, ChromaDB, and Claude API. Each system is custom-built for your data — documents, databases, or web content. Want to discuss your use case?",
  services: "My core services: RAG Systems, AI Agents, Workflow Automation, Custom Chatbots, and API Integration. Every project is delivered with clean, documented, production-ready code.",
  available: "Yes, I'm currently open to new projects. The best way to start is to describe what you need — I'll review it and send a tailored proposal within 24 hours.",
  cost: "Pricing depends on scope and complexity. I work on fixed-price milestones for well-defined projects. Reach out with your requirements and I'll give you a transparent quote.",
  default: "I specialize in building AI systems that solve real business problems — RAG pipelines, autonomous agents, and intelligent automation. What are you looking to build?",
};

function getResponse(msg: string) {
  const m = msg.toLowerCase();
  if (m.includes("rag") || m.includes("system") || m.includes("build")) return DEMO_RESPONSES.rag;
  if (m.includes("service") || m.includes("offer") || m.includes("do")) return DEMO_RESPONSES.services;
  if (m.includes("available") || m.includes("hire") || m.includes("work")) return DEMO_RESPONSES.available;
  if (m.includes("cost") || m.includes("price") || m.includes("rate") || m.includes("much")) return DEMO_RESPONSES.cost;
  return DEMO_RESPONSES.default;
}

function TypingEffect() {
  const [idx, setIdx] = useState(0);
  const [text, setText] = useState("");
  const [del, setDel] = useState(false);
  useEffect(() => {
    const phrase = QUESTIONS[idx];
    let t: ReturnType<typeof setTimeout>;
    if (!del && text.length < phrase.length) t = setTimeout(() => setText(phrase.slice(0, text.length + 1)), 55);
    else if (!del) t = setTimeout(() => setDel(true), 2200);
    else if (del && text.length > 0) t = setTimeout(() => setText(text.slice(0, -1)), 28);
    else { setDel(false); setIdx((i) => (i + 1) % QUESTIONS.length); }
    return () => clearTimeout(t);
  }, [text, del, idx]);
  return <span className="typed">"{text}<span className="cur">|</span>"</span>;
}

function Chat() {
  const [msgs, setMsgs] = useState([
    { r: "agent", t: "Hi! I'm the AI Agent representing this profile. Ask me anything about skills, services, or availability." }
  ]);
  const [val, setVal] = useState("");
  const [loading, setLoading] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  const send = () => {
    if (!val.trim() || loading) return;
    const q = val.trim(); setVal("");
    setMsgs(p => [...p, { r: "user", t: q }]);
    setLoading(true);
    AgentAPI.chat(q, msgs.map(m => ({role: m.r === "agent" ? "assistant" : "user", content: m.t}))).then(response => {
      setMsgs(p => [...p, { r: "agent", t: response }]);
      setLoading(false);
    }).catch(() => {
      setMsgs(p => [...p, { r: "agent", t: "Sorry, I am having trouble connecting. Please try again." }]);
      setLoading(false);
    });
  };
  // removed
    setTimeout(() => {
      setMsgs(p => [...p, { r: "agent", t: getResponse(q) }]);
      setLoading(false);
    }, 1100);
  };

  return (
    <div className="chat">
      <div className="chat-top">
        <div className="av">AI</div>
        <div>
          <div className="av-name">AI Agent · Online</div>
          <div className="av-sub">Responds instantly</div>
        </div>
        <div className="live-dot" />
      </div>
      <div className="chat-body">
        {msgs.map((m, i) => (
          <div key={i} className={`msg ${m.r}`}>
            <div className="bbl">{m.t}</div>
          </div>
        ))}
        {loading && (
          <div className="msg agent">
            <div className="bbl dots"><span /><span /><span /></div>
          </div>
        )}
        <div ref={end} />
      </div>
      <div className="chat-foot">
        <input
          className="ci" value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          placeholder="Ask anything..."
        />
        <button className="sb" onClick={send}>↑</button>
      </div>
    </div>
  );
}

export default function App() {
  const [scrolled, setScrolled] = useState(false);
  const [activeService, setActiveService] = useState(0);
  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 30);
    window.addEventListener("scroll", h);
    return () => window.removeEventListener("scroll", h);
  }, []);

  const services = [
    { n: "RAG Systems", d: "Custom knowledge retrieval pipelines that give AI accurate, source-grounded answers from your documents, databases, or any data source.", t: "LangChain · ChromaDB · Claude API" },
    { n: "AI Agents", d: "Autonomous systems that plan, reason, and execute multi-step tasks. From simple assistants to complex orchestrated pipelines.", t: "LangGraph · Tool Use · Memory" },
    { n: "Automation", d: "End-to-end workflow automation powered by AI. Eliminate repetitive tasks and connect your tools intelligently.", t: "FastAPI · Celery · Webhooks" },
    { n: "Chatbots", d: "Branded conversational AI trained on your business knowledge. Deploy anywhere — web, WhatsApp, Telegram, Slack.", t: "Custom LLMs · Multi-channel" },
  ];

  const works = [
    { n: "Enterprise RAG Assistant", d: "Internal knowledge base for a 200-person company. Reduced support tickets by 60%.", t: "RAG · LangChain · FastAPI" },
    { n: "Personal AI Agent Platform", d: "This very platform — an AI twin that represents professionals on LinkedIn and to potential clients.", t: "Agents · ChromaDB · Next.js" },
    { n: "Document Intelligence API", d: "Automated extraction and analysis of legal contracts using multi-agent pipeline.", t: "Claude API · PDF · Automation" },
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        :root {
          --bg: #F7F3EC;
          --bg2: #EDE8DF;
          --ink: #1C1917;
          --ink2: #57534E;
          --ink3: #A8A29E;
          --acc: #C84B31;
          --acc2: #8B5E3C;
          --border: #DDD8CF;
          --white: #FDFAF5;
        }
        html { scroll-behavior: smooth; }
        body { background: var(--bg); color: var(--ink); font-family: 'DM Sans', sans-serif; overflow-x: hidden; }

        /* NAV */
        .nav {
          position: fixed; top: 0; left: 0; right: 0; z-index: 100;
          display: flex; align-items: center; justify-content: space-between;
          padding: 28px 60px; transition: all 0.4s;
        }
        .nav.scrolled {
          background: rgba(247,243,236,0.92); backdrop-filter: blur(16px);
          border-bottom: 1px solid var(--border); padding: 18px 60px;
        }
        .logo {
          font-family: 'Playfair Display', serif;
          font-size: 22px; font-weight: 700; color: var(--ink);
          letter-spacing: -0.5px;
        }
        .logo span { color: var(--acc); }
        .nav-links { display: flex; gap: 40px; }
        .nav-links a { color: var(--ink2); text-decoration: none; font-size: 14px; font-weight: 500; transition: color 0.2s; }
        .nav-links a:hover { color: var(--ink); }
        .nav-btn {
          background: var(--ink); color: var(--bg); border: none;
          padding: 11px 24px; border-radius: 6px; font-size: 14px;
          font-weight: 500; cursor: pointer; font-family: 'DM Sans', sans-serif;
          transition: all 0.2s; letter-spacing: -0.2px;
        }
        .nav-btn:hover { background: var(--acc); }

        /* HERO */
        .hero {
          min-height: 100vh; display: grid;
          grid-template-columns: 1fr 480px;
          gap: 60px; align-items: center;
          padding: 140px 60px 80px;
          position: relative;
        }
        .hero::before {
          content: ''; position: absolute;
          top: 0; right: 0; width: 50%; height: 100%;
          background: var(--bg2); z-index: 0;
          clip-path: polygon(8% 0, 100% 0, 100% 100%, 0% 100%);
        }
        .hero-left { position: relative; z-index: 1; }
        .hero-right { position: relative; z-index: 1; }

        .tag {
          display: inline-flex; align-items: center; gap: 8px;
          border: 1px solid var(--border); background: var(--white);
          padding: 7px 14px; border-radius: 4px; font-size: 12px;
          font-weight: 500; color: var(--ink2); letter-spacing: 0.3px;
          text-transform: uppercase; margin-bottom: 36px;
          animation: up 0.7s ease both;
        }
        .tag-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--acc); }

        .hero-title {
          font-family: 'Playfair Display', serif;
          font-size: clamp(48px, 6vw, 82px);
          font-weight: 700; line-height: 1.02;
          letter-spacing: -2px; margin-bottom: 28px;
          animation: up 0.7s 0.1s ease both;
        }
        .hero-title em { color: var(--acc); font-style: italic; }

        .hero-typing {
          font-size: 16px; color: var(--ink3); margin-bottom: 36px;
          min-height: 26px; animation: up 0.7s 0.2s ease both;
        }
        .typed { color: var(--acc2); font-style: italic; }
        .cur { animation: blink 1s infinite; }
        @keyframes blink { 0%,100%{opacity:1}50%{opacity:0} }

        .hero-desc {
          font-size: 17px; color: var(--ink2); line-height: 1.75;
          max-width: 480px; margin-bottom: 48px; font-weight: 300;
          animation: up 0.7s 0.3s ease both;
        }
        .hero-actions { display: flex; gap: 14px; flex-wrap: wrap; animation: up 0.7s 0.4s ease both; }

        .btn-p {
          background: var(--ink); color: var(--bg);
          border: none; padding: 15px 30px; border-radius: 6px;
          font-size: 15px; font-weight: 500; cursor: pointer;
          font-family: 'DM Sans', sans-serif; transition: all 0.25s;
          letter-spacing: -0.3px;
        }
        .btn-p:hover { background: var(--acc); transform: translateY(-1px); }
        .btn-s {
          background: transparent; color: var(--ink);
          border: 1px solid var(--border); padding: 15px 30px;
          border-radius: 6px; font-size: 15px; font-weight: 500;
          cursor: pointer; font-family: 'DM Sans', sans-serif;
          transition: all 0.25s;
        }
        .btn-s:hover { border-color: var(--ink2); }

        @keyframes up { from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)} }

        /* CHAT */
        .chat {
          background: var(--white); border: 1px solid var(--border);
          border-radius: 16px; overflow: hidden;
          box-shadow: 0 20px 60px rgba(28,25,23,0.12);
          animation: up 0.8s 0.4s ease both;
        }
        .chat-top {
          display: flex; align-items: center; gap: 12px;
          padding: 18px 20px; border-bottom: 1px solid var(--border);
          background: var(--bg); position: relative;
        }
        .av {
          width: 38px; height: 38px; border-radius: 8px;
          background: var(--ink); color: var(--bg);
          display: flex; align-items: center; justify-content: center;
          font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
        }
        .av-name { font-size: 14px; font-weight: 600; color: var(--ink); }
        .av-sub { font-size: 11px; color: var(--ink3); }
        .live-dot {
          width: 8px; height: 8px; border-radius: 50%; background: #22C55E;
          margin-left: auto; animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.6;transform:scale(1.3)} }

        .chat-body { padding: 18px; height: 300px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .chat-body::-webkit-scrollbar { width: 3px; }
        .chat-body::-webkit-scrollbar-thumb { background: var(--border); }
        .msg { display: flex; }
        .msg.user { justify-content: flex-end; }
        .bbl {
          max-width: 82%; padding: 11px 15px; border-radius: 12px;
          font-size: 14px; line-height: 1.55;
        }
        .msg.agent .bbl { background: var(--bg2); border-bottom-left-radius: 3px; color: var(--ink); }
        .msg.user .bbl { background: var(--ink); color: var(--bg); border-bottom-right-radius: 3px; }
        .dots { display: flex; gap: 4px; align-items: center; padding: 14px 16px !important; }
        .dots span { width: 5px; height: 5px; border-radius: 50%; background: var(--ink3); animation: dot 1.2s infinite; }
        .dots span:nth-child(2){animation-delay:0.2s}.dots span:nth-child(3){animation-delay:0.4s}
        @keyframes dot{0%,100%{opacity:0.3;transform:scale(1)}50%{opacity:1;transform:scale(1.2)}}
        .chat-foot { display: flex; gap: 8px; padding: 14px; border-top: 1px solid var(--border); background: var(--bg); }
        .ci {
          flex: 1; background: var(--white); border: 1px solid var(--border);
          border-radius: 8px; padding: 10px 14px; color: var(--ink);
          font-size: 14px; font-family: 'DM Sans', sans-serif; outline: none;
          transition: border-color 0.2s;
        }
        .ci:focus { border-color: var(--ink2); }
        .ci::placeholder { color: var(--ink3); }
        .sb {
          width: 38px; height: 38px; border-radius: 8px;
          background: var(--ink); border: none; color: var(--bg);
          font-size: 16px; cursor: pointer; transition: all 0.2s;
        }
        .sb:hover { background: var(--acc); }

        /* MARQUEE */
        .marquee-wrap {
          border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
          overflow: hidden; padding: 18px 0; background: var(--white);
        }
        .marquee { display: flex; gap: 60px; animation: scroll 20s linear infinite; white-space: nowrap; }
        @keyframes scroll { from{transform:translateX(0)}to{transform:translateX(-50%)} }
        .marquee-item { font-family: 'Playfair Display', serif; font-size: 15px; color: var(--ink3); font-style: italic; }
        .marquee-dot { color: var(--acc); }

        /* ABOUT */
        .about {
          display: grid; grid-template-columns: 1fr 1fr;
          gap: 80px; padding: 100px 60px; align-items: center;
        }
        .about-label { font-size: 12px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: var(--acc); margin-bottom: 16px; }
        .about-title { font-family: 'Playfair Display', serif; font-size: clamp(32px, 3.5vw, 48px); font-weight: 700; letter-spacing: -1px; line-height: 1.1; margin-bottom: 24px; }
        .about-text { color: var(--ink2); font-size: 16px; line-height: 1.8; font-weight: 300; margin-bottom: 16px; }
        .about-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 40px; }
        .astat { border-top: 2px solid var(--ink); padding-top: 16px; }
        .astat-n { font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 700; color: var(--acc); letter-spacing: -1px; }
        .astat-l { font-size: 13px; color: var(--ink3); margin-top: 4px; }
        .about-img {
          background: var(--bg2); border-radius: 12px;
          aspect-ratio: 4/5; display: flex; flex-direction: column;
          align-items: center; justify-content: center; gap: 16px;
          border: 1px solid var(--border); position: relative; overflow: hidden;
        }
        .about-img::before {
          content: ''; position: absolute; top: -30%; right: -20%;
          width: 200px; height: 200px; border-radius: 50%;
          background: radial-gradient(circle, rgba(200,75,49,0.1) 0%, transparent 70%);
        }
        .about-avatar {
          width: 80px; height: 80px; border-radius: 50%;
          background: var(--ink); display: flex; align-items: center;
          justify-content: center; font-family: 'Playfair Display', serif;
          font-size: 28px; color: var(--bg); font-weight: 700;
        }
        .about-name { font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; }
        .about-role { font-size: 13px; color: var(--ink3); }

        /* SERVICES */
        .services-sec { padding: 100px 60px; background: var(--bg2); }
        .sec-label { font-size: 12px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: var(--acc); margin-bottom: 16px; }
        .sec-title { font-family: 'Playfair Display', serif; font-size: clamp(32px, 4vw, 52px); font-weight: 700; letter-spacing: -1.5px; margin-bottom: 60px; max-width: 500px; }
        .services-layout { display: grid; grid-template-columns: 280px 1fr; gap: 60px; }
        .service-tabs { display: flex; flex-direction: column; gap: 4px; }
        .stab {
          padding: 16px 20px; border-radius: 8px; cursor: pointer;
          font-size: 15px; font-weight: 500; color: var(--ink2);
          transition: all 0.2s; border: 1px solid transparent;
          text-align: left; background: transparent; font-family: 'DM Sans', sans-serif;
        }
        .stab.active { background: var(--white); color: var(--ink); border-color: var(--border); box-shadow: 0 2px 12px rgba(28,25,23,0.06); }
        .stab:hover:not(.active) { color: var(--ink); }
        .service-detail { padding: 40px; background: var(--white); border-radius: 12px; border: 1px solid var(--border); }
        .sd-title { font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 700; margin-bottom: 16px; letter-spacing: -0.5px; }
        .sd-desc { color: var(--ink2); font-size: 16px; line-height: 1.8; font-weight: 300; margin-bottom: 32px; }
        .sd-tech { display: flex; flex-wrap: wrap; gap: 8px; }
        .tech-tag {
          background: var(--bg2); border: 1px solid var(--border);
          padding: 6px 14px; border-radius: 100px;
          font-size: 13px; color: var(--ink2);
        }
        .sd-arrow { margin-top: 40px; }
        .sd-link { color: var(--acc); font-size: 14px; font-weight: 500; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; }

        /* WORK */
        .work-sec { padding: 100px 60px; }
        .work-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
        .work-card {
          background: var(--white); border: 1px solid var(--border);
          border-radius: 12px; padding: 32px; transition: all 0.3s;
          cursor: pointer;
        }
        .work-card:hover { transform: translateY(-4px); box-shadow: 0 16px 40px rgba(28,25,23,0.1); border-color: var(--ink2); }
        .work-num { font-family: 'Playfair Display', serif; font-size: 13px; color: var(--ink3); margin-bottom: 24px; }
        .work-name { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; margin-bottom: 12px; letter-spacing: -0.5px; line-height: 1.2; }
        .work-desc { color: var(--ink2); font-size: 14px; line-height: 1.6; margin-bottom: 24px; }
        .work-tech { font-size: 12px; color: var(--ink3); font-style: italic; }
        .work-arrow { color: var(--acc); font-size: 20px; float: right; }

        /* CTA */
        .cta-sec {
          padding: 120px 60px; background: var(--ink);
          text-align: center; position: relative; overflow: hidden;
        }
        .cta-sec::before {
          content: ''; position: absolute; top: -50%; left: 50%; transform: translateX(-50%);
          width: 600px; height: 600px; border-radius: 50%;
          background: radial-gradient(circle, rgba(200,75,49,0.15) 0%, transparent 70%);
          pointer-events: none;
        }
        .cta-label { font-size: 12px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: var(--acc); margin-bottom: 20px; }
        .cta-title { font-family: 'Playfair Display', serif; font-size: clamp(36px, 5vw, 64px); font-weight: 700; color: var(--bg); letter-spacing: -2px; margin-bottom: 20px; line-height: 1.05; }
        .cta-title em { color: var(--acc); font-style: italic; }
        .cta-sub { color: #A8A29E; font-size: 17px; margin-bottom: 48px; font-weight: 300; max-width: 480px; margin-left: auto; margin-right: auto; line-height: 1.7; }
        .cta-btns { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }
        .btn-light { background: var(--bg); color: var(--ink); border: none; padding: 16px 32px; border-radius: 6px; font-size: 15px; font-weight: 600; cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.2s; }
        .btn-light:hover { background: var(--acc); color: #fff; }
        .btn-outline-light { background: transparent; color: var(--bg); border: 1px solid rgba(247,243,236,0.2); padding: 16px 32px; border-radius: 6px; font-size: 15px; font-weight: 500; cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.2s; }
        .btn-outline-light:hover { border-color: var(--bg); }

        /* FOOTER */
        .footer { padding: 40px 60px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .footer-logo { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; }
        .footer-logo span { color: var(--acc); }
        .footer-text { font-size: 13px; color: var(--ink3); }

        @media (max-width: 900px) {
          .nav { padding: 18px 24px; } .nav.scrolled { padding: 14px 24px; }
          .nav-links { display: none; }
          .hero { grid-template-columns: 1fr; padding: 100px 24px 60px; }
          .hero::before { display: none; }
          .about { grid-template-columns: 1fr; padding: 60px 24px; gap: 40px; }
          .about-img { display: none; }
          .services-sec, .work-sec, .cta-sec { padding: 60px 24px; }
          .services-layout { grid-template-columns: 1fr; }
          .service-tabs { flex-direction: row; flex-wrap: wrap; }
          .work-grid { grid-template-columns: 1fr; }
          .footer { padding: 32px 24px; flex-direction: column; gap: 12px; text-align: center; }
        }
      `}</style>

      {/* NAV */}
      <nav className={`nav ${scrolled ? "scrolled" : ""}`}>
        <div className="logo">Agent<span>Me</span></div>
        <div className="nav-links">
          <a href="#about">About</a>
          <a href="#services">Services</a>
          <a href="#work">Work</a>
          <a href="#contact">Contact</a>
        </div>
        <button className="nav-btn">Talk to My Agent →</button>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-left">
          <div className="tag"><span className="tag-dot" />AI Engineer · Available for Projects</div>
          <h1 className="hero-title">
            Your AI Agent,<br />
            <em>Always On.</em>
          </h1>
          <p className="hero-typing">
            People are asking: <TypingEffect />
          </p>
          <p className="hero-desc">
            I build production-grade AI systems — RAG pipelines, autonomous agents, and intelligent automation.
            My AI Agent represents me 24/7, answering your questions before we even meet.
          </p>
          <div className="hero-actions">
            <button className="btn-p">Start a Project →</button>
            <button className="btn-s">See My Work</button>
          </div>
        </div>
        <div className="hero-right">
          <Chat />
        </div>
      </section>

      {/* MARQUEE */}
      <div className="marquee-wrap">
        <div className="marquee">
          {[...Array(2)].map((_, i) =>
            ["RAG Systems", "AI Agents", "LangChain", "FastAPI", "Claude API", "ChromaDB", "Workflow Automation", "Python", "Next.js", "Custom Chatbots"].map((item, j) => (
              <span key={`${i}-${j}`} className="marquee-item">{item} <span className="marquee-dot">·</span></span>
            ))
          )}
        </div>
      </div>

      {/* ABOUT */}
      <section className="about" id="about">
        <div>
          <div className="about-label">About</div>
          <h2 className="about-title">Building AI that works in the real world.</h2>
          <p className="about-text">I'm an AI Engineer specializing in RAG systems and autonomous agents. I don't build demos — I build production systems that solve real business problems.</p>
          <p className="about-text">Every project is delivered with clean, documented code and a focus on long-term maintainability. No black boxes.</p>
          <div className="about-stats">
            <div className="astat"><div className="astat-n">15+</div><div className="astat-l">AI Projects Delivered</div></div>
            <div className="astat"><div className="astat-n">24h</div><div className="astat-l">Average Response Time</div></div>
            <div className="astat"><div className="astat-n">100%</div><div className="astat-l">Production-Ready Code</div></div>
            <div className="astat"><div className="astat-n">∞</div><div className="astat-l">Languages Supported</div></div>
          </div>
        </div>
        <div className="about-img">
          <div className="about-avatar">A</div>
          <div className="about-name">Alex</div>
          <div className="about-role">AI Engineer & RAG Specialist</div>
        </div>
      </section>

      {/* SERVICES */}
      <section className="services-sec" id="services">
        <div className="sec-label">Services</div>
        <h2 className="sec-title">What I build for you.</h2>
        <div className="services-layout">
          <div className="service-tabs">
            {services.map((s, i) => (
              <button key={i} className={`stab ${activeService === i ? "active" : ""}`} onClick={() => setActiveService(i)}>{s.n}</button>
            ))}
          </div>
          <div className="service-detail">
            <div className="sd-title">{services[activeService].n}</div>
            <div className="sd-desc">{services[activeService].d}</div>
            <div className="sd-tech">
              {services[activeService].t.split(" · ").map(t => <span key={t} className="tech-tag">{t}</span>)}
            </div>
            <div className="sd-arrow"><a className="sd-link">Discuss this service →</a></div>
          </div>
        </div>
      </section>

      {/* WORK */}
      <section className="work-sec" id="work">
        <div className="sec-label">Portfolio</div>
        <h2 className="sec-title">Selected work.</h2>
        <div className="work-grid">
          {works.map((w, i) => (
            <div key={i} className="work-card">
              <div className="work-num">0{i + 1}</div>
              <div className="work-name">{w.n} <span className="work-arrow">↗</span></div>
              <div className="work-desc">{w.d}</div>
              <div className="work-tech">{w.t}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="cta-sec" id="contact">
        <div className="cta-label">Let's Work Together</div>
        <h2 className="cta-title">Ready to build something<br /><em>intelligent?</em></h2>
        <p className="cta-sub">Whether you need a RAG system, an AI agent, or full workflow automation — let's talk about what's possible for your business.</p>
        <div className="cta-btns">
          <button className="btn-light">Start a Project →</button>
          <button className="btn-outline-light">Connect on LinkedIn</button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="footer">
        <div className="footer-logo">Agent<span>Me</span></div>
        <div className="footer-text">Built with RAG + Claude API · 2026</div>
        <div className="footer-text">Your AI Twin on LinkedIn</div>
      </footer>
    </>
  );
}