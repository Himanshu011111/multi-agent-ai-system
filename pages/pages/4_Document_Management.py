import streamlit as st
from frontend.ui_utils import (
    apply_saas_styling,
    api_get,
    api_post,
    fetch_file_bytes,
)

st.set_page_config(page_title="Document Management & RAG", page_icon="📂", layout="wide")
apply_saas_styling()

st.title("📂 Document Management & RAG Intelligence")
st.caption("Upload PDF, DOCX, CSV, or TXT files for automatic text extraction, ChromaDB vector indexing, and semantic question answering.")

up_col, qa_col = st.columns([1, 1.2])

with up_col:
    st.subheader("📤 Upload Document (PDF / DOCX / CSV / TXT)")
    uploaded_file = st.file_uploader(
        "Choose a document (Max 15 MB)",
        type=["pdf", "docx", "csv", "txt"],
    )
    if uploaded_file is not None:
        if st.button("⚡ Upload & Index into Vector Store", type="primary", use_container_width=True):
            with st.spinner(f"Processing and indexing '{uploaded_file.name}' into ChromaDB..."):
                files_payload = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                res, err = api_post("/api/documents/upload", files=files_payload)
                if err:
                    st.error(err)
                else:
                    st.success(f"Successfully uploaded & indexed **{res['filename']}** ({res['file_size']} bytes)!")

    st.divider()
    st.subheader("📚 Uploaded Documents Registry")
    docs, _ = api_get("/api/documents/")
    if not docs:
        st.info("No documents uploaded yet.")
    else:
        st.dataframe(
            [
                {
                    "ID": d["id"],
                    "Filename": d["filename"],
                    "Format": d["file_type"].upper(),
                    "Size (KB)": round(d["file_size"] / 1024, 1),
                    "Uploaded At": d["uploaded_at"][:19],
                }
                for d in docs
            ],
            use_container_width=True,
        )

with qa_col:
    st.subheader("🧠 Semantic RAG Document Query")
    rag_question = st.text_area(
        "Ask a question across your uploaded documents:",
        placeholder="e.g., What are the main conclusions, methodology, or key metrics mentioned in the uploaded PDF?",
        height=100,
    )
    if st.button("🔎 Search Vector Store & Generate Cited Answer", type="primary", use_container_width=True):
        if len(rag_question.strip()) < 3:
            st.warning("Please enter a question (at least 3 characters).")
        else:
            with st.spinner("Retrieving relevant chunks from ChromaDB and synthesizing answer with Gemini..."):
                ans_data, err = api_post("/api/documents/query", json_data={"query": rag_question})
                if err:
                    st.error(err)
                else:
                    st.markdown(
                        f"""
                        <div class="saas-card">
                            <h4 style="margin-top:0;">💡 RAG Answer</h4>
                            <p style="color:#1e293b; white-space:pre-wrap;">{ans_data.get('answer')}</p>
                            <hr/>
                            <small style="color:#475569;">
                                <b>Cited Document Sources:</b> {', '.join(ans_data.get('sources', [])) or 'None'}
                            </small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    st.divider()
    st.subheader("📥 Download Generated Reports")
    reports, _ = api_get("/api/reports/")
    if not reports:
        st.info("No reports generated yet.")
    else:
        for rep in reports[:6]:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{rep['report_title']}** (`Task #{rep['task_id']}`)")
            with c2:
                fbytes = fetch_file_bytes(f"/api/reports/download/{rep['id']}")
                if fbytes:
                    st.download_button(
                        label=f"⬇️ {rep['format'].upper()}",
                        data=fbytes,
                        file_name=f"report_{rep['id']}.{rep['format']}",
                        key=f"doc_dl_{rep['id']}",
                    )