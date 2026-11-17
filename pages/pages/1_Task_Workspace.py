import streamlit as st
from frontend.ui_utils import (
    apply_saas_styling,
    api_get,
    api_post,
    fetch_file_bytes,
    status_badge,
)

st.set_page_config(page_title="AI Task Workspace", page_icon="⚡", layout="wide")
apply_saas_styling()

st.title("⚡ AI Task Workspace")
st.caption("Submit complex natural-language instructions, inspect multi-agent execution plans, and download verified outputs.")

# Preset Demonstration Workflow Templates
WORKFLOW_PRESETS = {
    "Custom Instruction (Write your own)": ("", "", "general_research"),
    "Workflow 1: AI Research Automation": (
        "Agentic AI & Multi-Agent Orchestration Architectures in 2026",
        "Conduct comprehensive research on modern Agentic AI and Multi-Agent Systems, compare LangGraph with traditional pipelines, analyze enterprise adoption trends, and produce a cited technical report.",
        "research",
    ),
    "Workflow 2: Document Intelligence (RAG)": (
        "Uploaded Document Deep-Dive Analysis",
        "Analyze the uploaded documents in the vector store, extract the core methodology, key findings, and limitations, and provide an executive summary with document citations.",
        "document_qa",
    ),
    "Workflow 3: Data Analysis (CSV EDA)": (
        "Exploratory Data Analysis & Trend Forecasting",
        "Perform statistical exploratory data analysis on the uploaded CSV dataset, summarize descriptive statistics, identify key patterns or anomalies, and generate visual charts and recommendations.",
        "data_analysis",
    ),
    "Workflow 4: Automated Report Generation": (
        "Enterprise Cloud Security & Zero-Trust Executive Report",
        "Plan, research, analyze, write, and review a formal executive report on Zero-Trust Architecture in Cloud Computing, formatted with an Executive Summary, Risk Matrix, and Implementation Roadmap.",
        "research",
    ),
    "Workflow 5: Complex Task Automation (with Human Approval Gate)": (
        "Automated Security Audit & Deployment Notification",
        "Decompose a multi-step security compliance audit workflow, compile remediation steps, and send email notification to the engineering team upon completion.",
        "complex_automation",
    ),
}

preset_choice = st.selectbox("🎯 Select a Demonstration Workflow Preset (or write custom):", list(WORKFLOW_PRESETS.keys()))
default_title, default_desc, default_type = WORKFLOW_PRESETS[preset_choice]

# Optional CSV selector if user uploaded CSVs
docs, _ = api_get("/api/documents/")
csv_docs = [d for d in (docs or []) if d.get("file_type") == "csv"]
selected_csv_path = None

with st.form("task_submission_form"):
    col_a, col_b = st.columns([2, 1])
    with col_a:
        title_input = st.text_input("Task Title", value=default_title, placeholder="e.g., Quantum Computing Market Research")
    with col_b:
        task_type_input = st.selectbox(
            "Initial Task Category",
            ["research", "document_qa", "data_analysis", "complex_automation", "general_research"],
            index=["research", "document_qa", "data_analysis", "complex_automation", "general_research"].index(default_type),
        )

    description_input = st.text_area(
        "Natural-Language Instruction",
        value=default_desc,
        height=120,
        placeholder="Describe your research topic, analysis requirements, or multi-step automation workflow...",
    )

    if csv_docs:
        csv_options = {"Auto-detect latest CSV": None}
        for cd in csv_docs:
            csv_options[f"{cd['filename']} ({cd['file_path']})"] = cd["file_path"]
        chosen_csv_label = st.selectbox("📊 Optional CSV Dataset for Data Analyst Agent:", list(csv_options.keys()))
        selected_csv_path = csv_options[chosen_csv_label]

    submitted = st.form_submit_button("🚀 Submit & Execute Multi-Agent Workflow", type="primary", use_container_width=True)

if submitted:
    if len(title_input.strip()) < 3 or len(description_input.strip()) < 5:
        st.warning("Please enter a valid Task Title (min 3 chars) and Instruction (min 5 chars).")
    else:
        with st.status("🤖 Running 7-Agent LangGraph Orchestration Pipeline...", expanded=True) as status_box:
            st.write("1️⃣ Creating task record in database...")
            created_task, err = api_post(
                "/api/tasks/create",
                json_data={
                    "title": title_input,
                    "description": description_input,
                    "task_type": task_type_input,
                },
            )
            if err:
                status_box.update(label="Task Creation Failed", state="error")
                st.error(err)
                st.stop()

            task_id = created_task["id"]
            st.session_state["active_task_id"] = task_id
            st.write(f"2️⃣ Task #{task_id} registered. Dispatching Supervisor, Planner, Research, Analyst, Writer, Reviewer & Automation Agents...")

            exec_result, exec_err = api_post(
                f"/api/tasks/{task_id}/execute",
                json_data={
                    "human_approved": False,
                    "csv_file_path": selected_csv_path,
                },
                timeout=240,
            )
            if exec_err:
                status_box.update(label="Workflow Execution Failed", state="error")
                st.error(exec_err)
            else:
                final_status = exec_result.get("status", "completed")
                status_box.update(
                    label=f"Workflow Finished with Status: {final_status.upper()} (Duration: {exec_result.get('execution_duration', 0)}s)",
                    state="complete",
                )
                st.session_state["latest_task_result"] = exec_result

st.divider()

# Task Inspector Section
tasks_list, _ = api_get("/api/tasks/")
if tasks_list:
    task_map = {f"#{t['id']} — {t['title']} [{t['status'].upper()}]": t["id"] for t in tasks_list}
    selected_label = st.selectbox("🔍 Inspect Executed Task:", list(task_map.keys()))
    inspect_id = task_map[selected_label]

    task_data, err = api_get(f"/api/tasks/{inspect_id}")
    if task_data:
        details = task_data.get("orchestration_details") or {}
        st.markdown(
            f"""
            <div class="saas-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">Task #{task_data['id']}: {task_data['title']}</h3>
                    {status_badge(task_data['status'])}
                </div>
                <p style="margin:0.5rem 0; color:#334155;"><b>Instruction:</b> {task_data['description']}</p>
                <small style="color:#64748b;">
                    Classified Type: <code>{task_data.get('task_type')}</code> • 
                    Execution Duration: <b>{task_data.get('execution_duration', 0)}s</b> • 
                    QA Quality Score: <b>{task_data.get('quality_score') or 'N/A'}/100</b>
                </small>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Action Controls: Human-in-the-Loop Approval & Task Cancellation
        ctrl_col1, ctrl_col2 = st.columns(2)
        if task_data["status"] == "needs_approval":
            with ctrl_col1:
                st.warning("🛡️ **Human-in-the-Loop Gate Triggered:** This task contains sensitive automation keywords and requires human approval before final execution and artifact export.")
                if st.button("✅ Approve & Complete Automation", key=f"approve_{inspect_id}", type="primary"):
                    with st.spinner("Executing approved automation workflow..."):
                        approved_res, app_err = api_post(f"/api/tasks/{inspect_id}/approve")
                        if app_err:
                            st.error(app_err)
                        else:
                            st.success("Task approved and completed!")
                            st.rerun()

        if task_data["status"] in ("running", "pending", "needs_approval"):
            with ctrl_col2:
                if st.button("🛑 Cancel Task", key=f"cancel_{inspect_id}"):
                    _, cancel_err = api_post(f"/api/tasks/{inspect_id}/cancel")
                    if cancel_err:
                        st.error(cancel_err)
                    else:
                        st.info("Task cancelled.")
                        st.rerun()

        # Tabs for Execution Plan, Agent Logs, Analysis & Final Report
        tab1, tab2, tab3, tab4 = st.tabs([
            "📄 Final Report & QA Score",
            "🗺️ Planner Roadmap & Agent Assignment",
            "📊 Data Analysis & Sources",
            "📜 Agent Execution Logs",
        ])

        with tab1:
            if task_data.get("quality_score") is not None:
                st.info(
                    f"🏅 **Reviewer / QA Agent Score: {task_data['quality_score']}/100**\n\n"
                    f"**Explanation:** {task_data.get('quality_explanation', '')}"
                )

            final_report_md = details.get("final_report") or details.get("draft_report")
            if final_report_md:
                st.markdown(final_report_md)
            else:
                st.caption("Final Markdown report is stored in downloadable PDF/DOCX artifacts below.")

            # Download buttons for generated reports
            reports = task_data.get("reports", [])
            if reports:
                st.subheader("📥 Download Generated Reports")
                dl_cols = st.columns(len(reports))
                for idx, rep in enumerate(reports):
                    file_bytes = fetch_file_bytes(f"/api/reports/download/{rep['id']}")
                    if file_bytes:
                        with dl_cols[idx]:
                            st.download_button(
                                label=f"⬇️ Download {rep['format'].upper()} Report",
                                data=file_bytes,
                                file_name=f"task_{inspect_id}_report.{rep['format']}",
                                mime="application/pdf" if rep["format"] == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True,
                            )

        with tab2:
            plan = details.get("execution_plan", {})
            if plan:
                st.markdown(f"**Plan Summary:** {plan.get('plan_summary', '')}")
                subtasks = plan.get("subtasks", [])
                if subtasks:
                    st.dataframe(subtasks, use_container_width=True)
            else:
                st.info("Execution roadmap details are recorded in the Agent Execution Logs tab.")

        with tab3:
            if details.get("stats_summary"):
                st.subheader("📈 Dataset Statistical Summary")
                st.code(details["stats_summary"])

            chart_bytes = fetch_file_bytes(f"/api/reports/chart/{inspect_id}")
            if chart_bytes:
                st.subheader("📊 Generated Visualization Chart")
                st.image(chart_bytes, caption=f"Task #{inspect_id} Data Analysis Chart")

            if details.get("analysis_insights"):
                st.subheader("🔍 Data Analyst Agent Insights")
                st.markdown(details["analysis_insights"])

            sources = task_data.get("sources", [])
            if sources:
                st.subheader("🌐 Collected Research Sources & Citations")
                for s in sources:
                    st.markdown(f"- **{s['title']}** — [{s['url']}]({s['url']})\n  _{s.get('snippet', '')}_")

        with tab4:
            logs = task_data.get("logs", [])
            if logs:
                for lg in logs:
                    st.markdown(
                        f"- `{lg['timestamp'][:19]}` | **{lg['agent_name']}** — _{lg['action']}_ ({lg['status']}): {lg.get('details', '')}"
                    )
            else:
                st.info("No execution logs found for this task.")