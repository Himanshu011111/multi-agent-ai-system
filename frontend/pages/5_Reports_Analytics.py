import pandas as pd
import plotly.express as px
import streamlit as st
from frontend.ui_utils import (
    apply_saas_styling,
    api_get,
    api_post,
    fetch_file_bytes,
)

st.set_page_config(page_title="Reports & Analytics", page_icon="📊", layout="wide")
apply_saas_styling()

st.title("📊 Reports & Execution Analytics")
st.caption("Visualize multi-agent execution performance, QA quality scores, task distributions, and export PDF/DOCX reports.")

tasks, err = api_get("/api/tasks/")
if err:
    st.error(err)
    st.stop()

if not tasks:
    st.info("No tasks available for analytics yet. Run a workflow in **1_Task_Workspace** first.")
else:
    df = pd.DataFrame(
        [
            {
                "Task ID": f"#{t['id']}",
                "Title": t["title"][:35],
                "Type": t.get("task_type", "research"),
                "Status": t.get("status", "pending"),
                "Duration (s)": t.get("execution_duration", 0.0),
                "QA Score": t.get("quality_score") or 0.0,
            }
            for t in tasks
        ]
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("⏱️ Execution Duration & QA Score by Task")
        fig_bar = px.bar(
            df,
            x="Task ID",
            y=["Duration (s)", "QA Score"],
            barmode="group",
            hover_data=["Title", "Type"],
            color_discrete_sequence=["#2563eb", "#16a34a"],
        )
        fig_bar.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        st.subheader("🧩 Task Distribution by Category")
        fig_pie = px.pie(
            df,
            names="Type",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

rep_col, custom_col = st.columns([1.3, 1])

with rep_col:
    st.subheader("🗂️ Generated PDF & DOCX Reports Archive")
    reports, _ = api_get("/api/reports/")
    if not reports:
        st.info("No generated reports found.")
    else:
        for r in reports:
            st.markdown(
                f"""
                <div class="saas-card" style="padding:0.9rem;">
                    <b>📄 {r['report_title']}</b><br/>
                    <small style="color:#64748b;">Task #{r['task_id']} • Format: {r['format'].upper()} • Created: {r['created_at'][:19]}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
            fbytes = fetch_file_bytes(f"/api/reports/download/{r['id']}")
            if fbytes:
                st.download_button(
                    label=f"⬇️ Download {r['report_title']}",
                    data=fbytes,
                    file_name=f"task_{r['task_id']}_report_{r['id']}.{r['format']}",
                    key=f"rep_page_dl_{r['id']}",
                )

with custom_col:
    st.subheader("🛠️ Custom Report Exporter (PDF / DOCX)")
    if tasks:
        with st.form("custom_export_form"):
            task_choices = {f"#{t['id']} — {t['title']}": t["id"] for t in tasks}
            chosen_task = st.selectbox("Associate with Task:", list(task_choices.keys()))
            rep_title = st.text_input("Report Title", value="Executive Summary Report")
            rep_format = st.radio("Export Format", ["pdf", "docx"], horizontal=True)
            rep_content = st.text_area("Report Body Content", height=140, placeholder="Paste or write custom report content...")
            export_btn = st.form_submit_button("📄 Generate Export File", type="primary")

        if export_btn:
            if len(rep_content.strip()) < 10:
                st.warning("Report content must be at least 10 characters.")
            else:
                new_rep, err = api_post(
                    "/api/reports/generate",
                    json_data={
                        "task_id": task_choices[chosen_task],
                        "title": rep_title,
                        "content": rep_content,
                        "format": rep_format,
                    },
                )
                if err:
                    st.error(err)
                else:
                    st.success(f"Generated {rep_format.upper()} report successfully!")
                    st.rerun()