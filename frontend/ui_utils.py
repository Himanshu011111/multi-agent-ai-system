import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


def apply_saas_styling():
    st.markdown(
        """
        <style>
        /* Main Container & Typography */
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2.5rem;
        }
        /* Metric & Feature Cards */
        .saas-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 1rem;
        }
        .saas-card-dark {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f8fafc;
            border-radius: 14px;
            padding: 1.6rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
        }
        .metric-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #0f172a;
            margin-top: 0.25rem;
        }
        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 9999px;
            text-transform: uppercase;
        }
        .badge-completed, .badge-success, .badge-healthy {
            background-color: #dcfce7;
            color: #166534;
        }
        .badge-running {
            background-color: #dbeafe;
            color: #1e40af;
        }
        .badge-pending, .badge-idle {
            background-color: #f1f5f9;
            color: #475569;
        }
        .badge-needs_approval {
            background-color: #fef9c3;
            color: #854d0e;
        }
        .badge-failed, .badge-error, .badge-cancelled {
            background-color: #fee2e2;
            color: #991b1b;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### 🤖 Multi-Agent AI Hub")
        st.caption("Autonomous Research, RAG & Task Automation Platform")
        st.divider()


def status_badge(status: str) -> str:
    clean = (status or "pending").lower()
    return f'<span class="badge badge-{clean}">{clean.replace("_", " ")}</span>'

@st.cache_data(ttl=20, show_spinner=False)
def api_get(endpoint: str, timeout: int = 90):
    try:
        resp = requests.get(f"{BACKEND_URL}{endpoint}", timeout=timeout)
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"API Error ({resp.status_code}): {resp.text}"
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to FastAPI Backend at http://127.0.0.1:8000. Ensure Uvicorn is running."
    except Exception as e:
        return None, str(e)


def api_post(endpoint: str, json_data: dict = None, files: dict = None, timeout: int = 180):
    try:
        resp = requests.post(
            f"{BACKEND_URL}{endpoint}",
            json=json_data,
            files=files,
            timeout=timeout,
        )
        if resp.status_code in (200, 201):
            return resp.json(), None
        return None, f"API Error ({resp.status_code}): {resp.text}"
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to FastAPI Backend at http://127.0.0.1:8000. Ensure Uvicorn is running."
    except Exception as e:
        return None, str(e)


def fetch_file_bytes(endpoint: str) -> bytes | None:
    try:
        resp = requests.get(f"{BACKEND_URL}{endpoint}", timeout=90)
        if resp.status_code == 200:
            return resp.content
        return None
    except Exception:
        return None