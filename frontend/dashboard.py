import streamlit as st
from frontend.ui_utils import apply_saas_styling, api_get, status_badge

st.set_page_config(
    page_title="Multi-Agent AI Research & Automation Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_saas_styling()

# Hero Welcome Section
st.markdown(
    """
    <div class="saas-card-dark">
        <h2 style="margin:0; color:#ffffff;">CritiMesh — Multi-Agent AI Research & Automation Engine</h2>
        <p style="margin-top:0.5rem; color:#cbd5e1; font-size:1rem;">
            Enterprise B.Tech CSE Major Project powered by <b>LangGraph Multi-Agent Orchestration</b>, 
            <b>Google Gemini Reasoning</b>, <b>ChromaDB RAG</b>, and <b>FastAPI</b>.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Fetch Dashboard KPI Metrics
stats, err = api_get("/api/tasks/summary/stats")
if err:
    st.error(f"⚠️ Backend Connection Issue: {err}")
    st.stop()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(
        f"""<div class="saas-card"><div class="metric-label">Total Tasks</div>
        <div class="metric-value">{stats.get('total_tasks', 0)}</div></div>""",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""<div class="saas-card"><div class="metric-label">Completed</div>
        <div class="metric-value" style="color:#16a34a;">{stats.get('completed_tasks', 0)}</div></div>""",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""<div class="saas-card"><div class="metric-label">Running</div>
        <div class="metric-value" style="color:#2563eb;">{stats.get('running_tasks', 0)}</div></div>""",
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        f"""<div class="saas-card"><div class="metric-label">Needs Approval</div>
        <div class="metric-value" style="color:#ca8a04;">{stats.get('needs_approval_tasks', 0)}</div></div>""",
        unsafe_allow_html=True,
    )
with col5:
    st.markdown(
        f"""<div class="saas-card"><div class="metric-label">Failed</div>
        <div class="metric-value" style="color:#dc2626;">{stats.get('failed_tasks', 0)}</div></div>""",
        unsafe_allow_html=True,
    )

st.divider()

# Project Overview & Recent Activity
left_col, right_col = st.columns([1.25, 1])

with left_col:
    st.subheader("🚀 Recent Tasks & Workflows")
    tasks, _ = api_get("/api/tasks/")
    if not tasks:
        st.info("No tasks submitted yet. Open **1_Task_Workspace** from the left sidebar to launch your first workflow!")
    else:
        for t in tasks[:6]:
            badge_html = status_badge(t.get("status"))
            score = t.get("quality_score")
            score_str = f"• QA Score: <b>{score:.1f}/100</b>" if score is not None else ""
            st.markdown(
                f"""
                <div class="saas-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b>#{t['id']} — {t['title']}</b>
                        {badge_html}
                    </div>
                    <p style="color:#475569; font-size:0.9rem; margin:0.4rem 0;">{t['description'][:140]}...</p>
                    <small style="color:#64748b;">
                        Type: <code>{t.get('task_type')}</code> • Duration: {t.get('execution_duration', 0)}s {score_str}
                    </small>
                </div>
                """,
                unsafe_allow_html=True,
            )

with right_col:
    st.subheader("📡 Live Agent Execution Feed")
    logs, _ = api_get("/api/agents/logs?limit=8")
    if not logs:
        st.info("No agent logs recorded yet. Agent telemetry will appear here as workflows execute.")
    else:
        for log in logs:
            badge_html = status_badge(log.get("status"))
            st.markdown(
                f"""
                <div class="saas-card" style="padding:0.85rem;">
                    <div style="display:flex; justify-content:space-between;">
                        <b>{log['agent_name']}</b>
                        {badge_html}
                    </div>
                    <div style="font-size:0.88rem; color:#1e293b; margin-top:0.2rem;">
                        Task #{log['task_id']} — {log['action']}
                    </div>
                    <small style="color:#64748b;">{(log.get('details') or '')[:110]}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.subheader("🧩 Core 7-Agent Architecture")
    st.markdown(
        """
        - **Supervisor Agent:** Classifies intent & routes workflows.
        - **Planner Agent:** Decomposes goals into prioritized subtasks.
        - **Research Agent:** Executes web search & local ChromaDB RAG.
        - **Data Analyst Agent:** Runs Pandas EDA & generates charts.
        - **Writer Agent:** Drafts structured reports with citations.
        - **Reviewer / QA Agent:** Verifies facts & scores quality (0–100).
        - **Task Automation Agent:** Exports PDF/DOCX & enforces Human-in-the-Loop approval.
        """
    )