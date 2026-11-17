import streamlit as st
from frontend.ui_utils import apply_saas_styling, api_get, status_badge

st.set_page_config(page_title="System Settings", page_icon="⚙️", layout="wide")
apply_saas_styling()

st.title("⚙️ System Configuration & Diagnostics")
st.caption("Inspect API key readiness, LLM & Embedding models, database connections, and security guardrails.")

health, err = api_get("/health")
if err:
    st.error(err)
    st.stop()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔑 API & Credentials Status")
    gemini_ok = health.get("gemini_api_configured", False)
    tavily_ok = health.get("tavily_search_configured", False)

    st.markdown(
        f"""
        <div class="saas-card">
            <div style="display:flex; justify-content:space-between;">
                <b>Google Gemini API Key (Mandatory)</b>
                {status_badge('completed' if gemini_ok else 'failed')}
            </div>
            <p style="font-size:0.86rem; color:#475569; margin-top:0.4rem;">
                {'Configured safely via .env file.' if gemini_ok else 'Missing! Add GEMINI_API_KEY to your .env file and restart backend.'}
            </p>
        </div>
        <div class="saas-card">
            <div style="display:flex; justify-content:space-between;">
                <b>Tavily Web Search API Key (Optional)</b>
                {status_badge('completed' if tavily_ok else 'pending')}
            </div>
            <p style="font-size:0.86rem; color:#475569; margin-top:0.4rem;">
                {'Live web search active.' if tavily_ok else 'Using resilient academic/mock fallback search mode.'}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.subheader("🗄️ Database & Vector Store Diagnostics")
    st.markdown(
        f"""
        <div class="saas-card">
            <div style="display:flex; justify-content:space-between;">
                <b>Backend Service Health</b>
                {status_badge(health.get('status', 'healthy'))}
            </div>
            <ul style="font-size:0.88rem; color:#334155; margin-top:0.5rem;">
                <li><b>Environment:</b> <code>{health.get('environment')}</code></li>
                <li><b>Primary LLM Model:</b> <code>{health.get('llm_model')}</code></li>
                <li><b>RAG Embedding Model:</b> <code>{health.get('embedding_model')}</code></li>
                <li><b>Relational Database:</b> <code>{health.get('database_url')}</code></li>
                <li><b>ChromaDB Vector Path:</b> <code>{health.get('vector_store_dir')}</code></li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
st.subheader("🛡️ Active Security & Governance Guardrails")
st.markdown(
    """
    - **API Key Isolation:** Keys are loaded strictly via server-side `.env` variables and never exposed to the browser or logs.
    - **Upload Validation:** File uploads enforce strict extension allowlists (`.pdf`, `.docx`, `.csv`, `.txt`) and a 15 MB size cap.
    - **Prompt-Injection Defense:** Retrieved web snippets and document chunks are isolated as untrusted data blocks during synthesis.
    - **Human-in-the-Loop Gatekeeper:** Sensitive automation instructions automatically pause in `needs_approval` state until explicitly approved by the user.
    """
)