import streamlit as st
from frontend.ui_utils import (
    apply_saas_styling,
    api_get,
    fetch_file_bytes,
    status_badge,
)

st.set_page_config(page_title="Task History", page_icon="🕒", layout="wide")
apply_saas_styling()

st.title("🕒 Task Execution History & Audit Trail")
st.caption("Browse, filter, and download outputs from all previously executed multi-agent workflows.")

tasks, err = api_get("/api/tasks/")
if err:
    st.error(err)
    st.stop()

if not tasks:
    st.info("No task history recorded yet.")
    st.stop()

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    status_filter = st.selectbox(
        "Filter by Status:",
        ["All", "completed", "running", "needs_approval", "failed", "cancelled", "pending"],
    )
with filter_col2:
    search_term = st.text_input("Search by Title or Description:", placeholder="Type keyword...")

filtered = tasks
if status_filter != "All":
    filtered = [t for t in filtered if t.get("status") == status_filter]
if search_term.strip():
    kw = search_term.strip().lower()
    filtered = [
        t
        for t in filtered
        if kw in t.get("title", "").lower() or kw in t.get("description", "").lower()
    ]

st.write(f"Showing **{len(filtered)}** of **{len(tasks)}** total tasks.")

for t in filtered:
    with st.expander(
        f"Task #{t['id']} — {t['title']} | Status: {t['status'].upper()} | Date: {t['created_at'][:19]}"
    ):
        st.markdown(f"**Status:** {status_badge(t['status'])}", unsafe_allow_html=True)
        st.markdown(f"**Instruction:** {t['description']}")
        st.markdown(
            f"**Category:** `{t.get('task_type')}` | **Duration:** `{t.get('execution_duration', 0)}s` | "
            f"**QA Score:** `{t.get('quality_score') or 'N/A'}/100`"
        )
        if t.get("quality_explanation"):
            st.caption(f"QA Notes: {t['quality_explanation']}")

        details = t.get("orchestration_details") or {}
        if details.get("final_report"):
            st.markdown("#### Final Reviewed Report")
            st.markdown(details["final_report"])

        reports = t.get("reports", [])
        if reports:
            st.markdown("#### Downloadable Artifacts")
            cols = st.columns(len(reports))
            for idx, r in enumerate(reports):
                fbytes = fetch_file_bytes(f"/api/reports/download/{r['id']}")
                if fbytes:
                    with cols[idx]:
                        st.download_button(
                            label=f"⬇️ Download {r['format'].upper()}",
                            data=fbytes,
                            file_name=f"task_{t['id']}_report.{r['format']}",
                            key=f"hist_dl_{t['id']}_{r['id']}",
                        )