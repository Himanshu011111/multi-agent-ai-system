import streamlit as st
from frontend.ui_utils import apply_saas_styling, api_get, api_post

st.set_page_config(page_title="Research Workspace", page_icon="🔬", layout="wide")
apply_saas_styling()

st.title("🔬 AI Research & Citation Workspace")
st.caption("Launch deep-dive web and RAG research investigations, inspect verified source URLs, and review synthesized key findings.")

with st.form("quick_research_form"):
    topic = st.text_input(
        "Research Topic / Question",
        placeholder="e.g., Retrieval-Augmented Generation (RAG) vs Long-Context LLMs in Enterprise Systems",
    )
    focus_notes = st.text_area(
        "Specific Research Focus & Key Questions",
        placeholder="Specify subtopics, metrics, or literature areas to focus on...",
        height=90,
    )
    run_research = st.form_submit_button("🔍 Conduct Multi-Agent Research", type="primary")

if run_research:
    if len(topic.strip()) < 3:
        st.warning("Please enter a valid research topic.")
    else:
        instruction = f"Research Topic: {topic}. Specific Focus: {focus_notes or 'Provide comprehensive factual findings, analysis, and source citations.'}"
        with st.spinner("Research Agent & Orchestrator gathering sources and synthesizing findings..."):
            created, err = api_post(
                "/api/tasks/create",
                json_data={"title": f"Research: {topic[:80]}", "description": instruction, "task_type": "research"},
            )
            if err:
                st.error(err)
            else:
                res, exec_err = api_post(f"/api/tasks/{created['id']}/execute", json_data={"human_approved": False})
                if exec_err:
                    st.error(exec_err)
                else:
                    st.success(f"Research Task #{created['id']} completed!")
                    st.session_state["selected_research_task"] = res

st.divider()

col_left, col_right = st.columns([1.3, 1])

with col_left:
    st.subheader("📑 Research Summaries & Key Findings")
    tasks, _ = api_get("/api/tasks/")
    research_tasks = [t for t in (tasks or []) if t.get("status") == "completed"]
    if not research_tasks:
        st.info("No completed research tasks yet. Run a topic above to view synthesized findings and citations.")
    else:
        options = {f"#{t['id']} — {t['title']}": t for t in research_tasks}
        chosen = st.selectbox("Select Research Investigation:", list(options.keys()))
        task_obj = options[chosen]
        details = task_obj.get("orchestration_details") or {}

        if details.get("research_notes"):
            st.markdown("#### Synthesized Research Notes")
            st.markdown(details["research_notes"])
        if details.get("final_report"):
            with st.expander("📄 View Full Reviewed Research Report", expanded=True):
                st.markdown(details["final_report"])

with col_right:
    st.subheader("🔗 Collected Source URLs & References")
    sources, _ = api_get("/api/tasks/sources/all")
    if not sources:
        st.info("No source citations stored yet.")
    else:
        for src in sources[:20]:
            st.markdown(
                f"""
                <div class="saas-card" style="padding:0.9rem;">
                    <b>📌 {src['title']}</b><br/>
                    <a href="{src['url']}" target="_blank" style="font-size:0.85rem; word-break:break-all;">{src['url']}</a>
                    <p style="font-size:0.84rem; color:#475569; margin:0.35rem 0 0 0;">
                        {(src.get('snippet') or '')[:180]}
                    </p>
                    <small style="color:#94a3b8;">Task #{src['task_id']}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )