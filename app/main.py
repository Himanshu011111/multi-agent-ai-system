from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.config import settings
from app.database.db import init_db
from app.services.llm_service import llm_service
from app.api.routes import tasks, agents, documents, reports
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting CritiMesh — Multi-Agent AI Research & Automation Engine Backend...")
    init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down Multi-Agent AI System Backend...")


app = FastAPI(
    title="CritiMesh AI — Multi-Agent Research & Automation API",
    description=(
        "Enterprise FastAPI backend powering LangGraph multi-agent orchestration, "
        "Google Gemini LLM reasoning, ChromaDB RAG, and automated PDF/DOCX reporting."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Register API Routers
app.include_router(tasks.router)
app.include_router(agents.router)
app.include_router(documents.router)
app.include_router(reports.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "system": "CritiMesh — Critic-Audited Multi-Agent Research & Task Automation Engine",
        "status": "online",
        "docs_url": "/docs",
    }


@app.get("/health", tags=["Health & Settings"])
def health_check():
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "gemini_api_configured": bool(settings.gemini_api_key and settings.gemini_api_key != "your_google_gemini_api_key_here"),
        "tavily_search_configured": bool(settings.tavily_api_key and settings.tavily_api_key != "your_tavily_api_key_here"),
        "llm_model": llm_service.model_name or "auto-detect",
        "embedding_model": "Gemini Cloud API Embeddings (text-embedding-004)",
        "database_url": settings.database_url,
        "vector_store_dir": settings.chroma_db_dir,
    }