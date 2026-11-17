import sys
from pathlib import Path

# Project root ko Python path mein add karein taaki 'frontend.ui_utils' mil sake
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Main dashboard code run karein
dashboard_path = ROOT_DIR / "frontend" / "dashboard.py"
exec(compile(dashboard_path.read_text(encoding="utf-8"), str(dashboard_path), "exec"))