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