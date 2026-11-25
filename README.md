# 🤖 CritiMesh
**Critic-Audited Multi-Agent Research, RAG & Executive Automation Engine**

CritiMesh is a high-velocity, enterprise-grade multi-agent AI platform built with **FastAPI**, **LangGraph**, **Streamlit**, **Google Gemini**, and **Tavily**. It orchestrates a parallelized 7-agent pipeline with an automated **Critic Agent self-correction loop**, **Human-in-the-Loop (HITL)** governance, live **Graphviz telemetry**, citation-grounded **PDF RAG**, and one-click **PowerPoint (`.pptx`), PDF, and DOCX** executive exports.

### Key Engineering Highlights
- **Sub-20s Execution Pipeline:** Concurrent Planner + Researcher execution via `asyncio.gather()`, deterministic intent routing, smart Gemini Flash-Lite fallback rotation, GZip middleware, and HTTP Keep-Alive connection pooling.
- **Self-Correcting Quality Assurance:** Dedicated Critic Agent audits accuracy, depth, and clarity, automatically triggering targeted rewrites when drafts fall below the quality threshold.
- **Cloud-Optimized RAG:** Memory-safe PDF chunking and Gemini Cloud Embeddings (`text-embedding-004`) engineered to run reliably within 512 MB cloud RAM limits.
- **Executive Deliverables:** Live Graphviz execution flowcharts, multi-metric QA scorecards, and automated `.pptx` / `.pdf` / `.docx` report generation.

---

