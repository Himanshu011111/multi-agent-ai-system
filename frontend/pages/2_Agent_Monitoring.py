import streamlit as st
from frontend.ui_utils import apply_saas_styling, api_get, status_badge

st.set_page_config(page_title="Agent Monitoring", page_icon="📡", layout="wide")
apply_saas_styling()

col_title, col_btn = st.columns([4, 1])
with col_title:
    st.title("📡 Real-Time Multi-Agent Monitoring")
    st.caption("Inspect the live status, role, current activity, execution output, and error state of all 7 specialised AI agents.")
with col_btn:
    if st.button("🔄 Refresh Telemetry", use_container_width=True):
        st.rerun()

data, err = api_get("/api/agents/status")
if err:
    st.error(err)
    st.stop()

agents = data.get("agents", [])
# --- Upgrade #4: Live LangGraph Topology Flowchart & Telemetry ---
st.subheader("🔀 Live LangGraph Agent Execution Topology")
tasks_list, _ = api_get("/api/tasks/")
if tasks_list:
    task_options = {
        f"#{t['id']} — {t.get('title', 'Untitled')[:45]} ({t.get('status', 'pending').upper()})": t
        for t in tasks_list
    }
    selected_label = st.selectbox("Select Execution Run to Inspect", list(task_options.keys()))
    selected_task = task_options[selected_label]
    t_status = selected_task.get("status", "pending")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Run Status", t_status.replace("_", " ").title())
    k2.metric("Total Latency", f"{float(selected_task.get('execution_duration') or 0.0):.2f}s")
    k3.metric("Critic QA Score", f"{float(selected_task.get('quality_score') or 0.0):.0f}/100")
    k4.metric("Workflow Mode", selected_task.get("task_type", "research").replace("_", " ").title())
else:
    t_status = "idle"
    st.caption("Run a task in **1_Task_Workspace** to inspect live run latency and Critic QA metrics.")


def _node_color(done: bool, active: bool = False, failed: bool = False) -> str:
    if failed:
        return "#dc2626"
    if active:
        return "#2563eb"
    return "#16a34a" if done else "#475569"


is_done = t_status == "completed"
is_hitl = t_status == "needs_approval"
is_run = t_status == "running"
is_fail = t_status == "failed"

dot_graph = f"""
digraph AgentPipeline {{
    rankdir=LR;
    bgcolor="transparent";
    node [shape=box, style="rounded,filled", fontname="Helvetica", fontcolor="white", fontsize=11, margin="0.16,0.10"];
    edge [color="#94a3b8", penwidth=1.5];

    Planner [label="1. Planner Agent\\n(Task Breakdown)", fillcolor="{_node_color(is_done or is_hitl or is_run, failed=is_fail)}"];
    HITL [label="2. HITL Gate\\n(Human Approval)", fillcolor="{_node_color(is_done, active=is_hitl)}"];
    Researcher [label="3. Researcher & RAG\\n(Web + Vector Search)", fillcolor="{_node_color(is_done, active=is_run)}"];
    Analyst [label="4. Analyst Agent\\n(Data Synthesis)", fillcolor="{_node_color(is_done)}"];
    Writer [label="5. Writer Agent\\n(Report Drafting)", fillcolor="{_node_color(is_done)}"];
    Critic [label="6. Critic QA Agent\\n(Self-Correction Audit)", fillcolor="{_node_color(is_done)}"];

    Planner -> HITL -> Researcher -> Analyst -> Writer -> Critic;
}}
"""
st.graphviz_chart(dot_graph, use_container_width=True)
st.divider()

# Display Agent Cards in a 2-column responsive grid
cols = st.columns(2)
for idx, agent in enumerate(agents):
    with cols[idx % 2]:
        badge = status_badge(agent.get("status", "idle"))
        err_msg = agent.get("error")
        err_html = (
            f'<div style="margin-top:0.5rem; color:#b91c1c; background:#fef2f2; padding:0.4rem 0.6rem; border-radius:6px; font-size:0.82rem;">'
            f'<b>Error:</b> {err_msg}</div>'
            if err_msg
            else ""
        )
        st.markdown(
            f"""
            <div class="saas-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0;">🤖 {agent.get('name')}</h4>
                    {badge}
                </div>
                <p style="color:#64748b; font-size:0.85rem; margin:0.35rem 0;">
                    <b>Role:</b> {agent.get('role')}
                </p>
                <div style="font-size:0.9rem; color:#0f172a; margin-top:0.5rem;">
                    <b>Current Activity:</b> {agent.get('current_activity')}
                </div>
                <div style="font-size:0.85rem; color:#334155; margin-top:0.4rem; background:#f8fafc; padding:0.5rem; border-radius:6px;">
                    <b>Latest Result:</b> {agent.get('last_result') or 'None'}
                </div>
                {err_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

st.subheader("📜 Complete Agent Execution Audit Log")
logs, _ = api_get("/api/agents/logs?limit=50")
if not logs:
    st.info("No agent execution logs recorded yet.")
else:
    st.dataframe(
        [
            {
                "Log ID": lg["id"],
                "Task ID": f"#{lg['task_id']}",
                "Agent Name": lg["agent_name"],
                "Action": lg["action"],
                "Status": lg["status"].upper(),
                "Details": lg.get("details", ""),
                "Timestamp": lg["timestamp"][:19],
            }
            for lg in logs
        ],
        use_container_width=True,
    )