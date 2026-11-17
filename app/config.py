import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    gemini_api_key: str = ""
    tavily_api_key: str = ""
    
    database_url: str = "sqlite:///./data/multi_agent_system.db"
    chroma_db_dir: str = "./data/chroma_db"
    
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    uploads_dir: Path = data_dir / "uploads"
    reports_dir: Path = base_dir / "reports"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure required directories exist
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)
Path(settings.chroma_db_dir).mkdir(parents=True, exist_ok=True)