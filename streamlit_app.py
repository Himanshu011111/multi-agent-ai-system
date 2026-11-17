import sys
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

pages_dir = ROOT_DIR / "frontend" / "pages"
page_files = sorted(pages_dir.glob("*.py")) if pages_dir.exists() else []

if page_files:
    nav_pages = [st.Page(str(ROOT_DIR / "frontend" / "dashboard.py"), title="Dashboard", icon="🏠", default=True)]
    for pf in page_files:
        clean_title = pf.stem.split("_", 1)[-1].replace("_", " ") if "_" in pf.stem else pf.stem
        nav_pages.append(st.Page(str(pf), title=clean_title))
    pg = st.navigation(nav_pages)
    pg.run()
else:
    dashboard_path = ROOT_DIR / "frontend" / "dashboard.py"
    exec(compile(dashboard_path.read_text(encoding="utf-8"), str(dashboard_path), "exec"))