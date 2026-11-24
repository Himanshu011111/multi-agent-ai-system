import os
import requests
from requests.adapters import HTTPAdapter
import streamlit as st


def _resolve_backend_url() -> str:
    url = os.getenv("BACKEND_URL")
    if not url:
        try:
            url = st.secrets.get("BACKEND_URL")
        except Exception:
            url = None
    return (url or "http://127.0.0.1:8000").rstrip("/")


BACKEND_URL = _resolve_backend_url()


@st.cache_resource
def _get_http_session() -> requests.Session:
    """Persistent Keep-Alive + GZip HTTP session to eliminate SSL handshake lag."""
    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"Accept-Encoding": "gzip, deflate"})
    return session


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


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_json_cached(endpoint: str, timeout: int):
    session = _get_http_session()
    resp = session.get(f"{BACKEND_URL}{endpoint}", timeout=timeout)
    if resp.status_code == 200:
        return resp.json()
    raise RuntimeError(f"API Error ({resp.status_code}): {resp.text}")


def api_get(endpoint: str, timeout: int = 90):
    """Fast pooled GET with 30s caching (errors are never cached; live status stays fresh)."""
    try:
        if "/status" in endpoint:
            session = _get_http_session()
            resp = session.get(f"{BACKEND_URL}{endpoint}", timeout=timeout)
            if resp.status_code == 200:
                return resp.json(), None
            return None, f"API Error ({resp.status_code}): {resp.text}"

        return _fetch_json_cached(endpoint, timeout), None
    except requests.exceptions.ConnectionError:
        return None, f"Cannot connect to FastAPI Backend at {BACKEND_URL}. Ensure the server is running."
    except Exception as e:
        return None, str(e)


api_get.clear = _fetch_json_cached.clear


def api_post(endpoint: str, json_data: dict = None, files: dict = None, timeout: int = 180):
    """Fast pooled POST that auto-refreshes cached GET data on success."""
    try:
        session = _get_http_session()
        resp = session.post(
            f"{BACKEND_URL}{endpoint}",
            json=json_data,
            files=files,
            timeout=timeout,
        )
        if resp.status_code in (200, 201):
            _fetch_json_cached.clear()
            return resp.json(), None
        return None, f"API Error ({resp.status_code}): {resp.text}"
    except requests.exceptions.ConnectionError:
        return None, f"Cannot connect to FastAPI Backend at {BACKEND_URL}. Ensure the server is running."
    except Exception as e:
        return None, str(e)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_file_bytes(endpoint: str) -> bytes | None:
    """Cached binary fetcher so PDF/DOCX downloads don't slow down page reruns."""
    try:
        session = _get_http_session()
        resp = session.get(f"{BACKEND_URL}{endpoint}", timeout=90)
        if resp.status_code == 200:
            return resp.content
        return None
    except Exception:
        return None