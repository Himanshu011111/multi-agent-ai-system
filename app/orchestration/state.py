from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict, total=False):
    # Core Task Metadata
    task_id: int
    title: str
    user_instruction: str
    has_uploaded_docs: bool
    csv_file_path: Optional[str]
    human_approved: bool

    # Supervisor Routing Outputs
    task_type: str
    requires_research: bool
    requires_rag: bool
    requires_analysis: bool
    requires_automation: bool
    supervisor_notes: str

    # Planner Outputs
    execution_plan: Dict[str, Any]

    # Research Outputs
    research_notes: str
    sources: List[Dict[str, Any]]

    # Data Analyst Outputs
    analysis_insights: str
    stats_summary: str
    chart_path: Optional[str]

    # Writer & Reviewer Outputs
    draft_report: str
    quality_score: float
    quality_explanation: str
    revision_needed: bool
    revision_count: int
    final_report: str

    # Automation Outputs
    automation_status: str
    automation_message: str
    pdf_path: Optional[str]
    docx_path: Optional[str]

    # Execution & Error Tracking
    error: Optional[str]


# Live status tracker for the 7 specialised agents (used by Agent Monitoring UI)
LIVE_AGENT_STATUS: Dict[str, Dict[str, Any]] = {
    "Supervisor Agent": {
        "name": "Supervisor Agent",
        "role": "Task Classification, Routing & Workflow Supervision",
        "status": "idle",
        "current_activity": "Waiting for incoming tasks",
        "last_result": "None",
        "error": None,
    },
    "Planner Agent": {
        "name": "Planner Agent",
        "role": "Task Decomposition, Prioritization & Roadmap Generation",
        "status": "idle",
        "current_activity": "Waiting for task assignment",
        "last_result": "None",
        "error": None,
    },
    "Research Agent": {
        "name": "Research Agent",
        "role": "Information Gathering, Web Search, RAG Retrieval & Citation Tracking",
        "status": "idle",
        "current_activity": "Waiting for research query",
        "last_result": "None",
        "error": None,
    },
    "Data Analyst Agent": {
        "name": "Data Analyst Agent",
        "role": "Statistical Analysis, Pattern Recognition & Data Visualization",
        "status": "idle",
        "current_activity": "Waiting for dataset or research findings",
        "last_result": "None",
        "error": None,
    },
    "Writer Agent": {
        "name": "Writer Agent",
        "role": "Structured Report Drafting, Executive Summarization & Documentation",
        "status": "idle",
        "current_activity": "Waiting for analyzed insights",
        "last_result": "None",
        "error": None,
    },
    "Reviewer / QA Agent": {
        "name": "Reviewer / QA Agent",
        "role": "Factual Consistency Verification, Citation Audit & Quality Scoring",
        "status": "idle",
        "current_activity": "Waiting for report draft",
        "last_result": "None",
        "error": None,
    },
    "Task Automation Agent": {
        "name": "Task Automation Agent",
        "role": "Artifact Export (PDF/DOCX), Execution Logging & Human-in-the-Loop Gatekeeper",
        "status": "idle",
        "current_activity": "Waiting for QA-approved report",
        "last_result": "None",
        "error": None,
    },
}


def update_live_agent_status(
    agent_name: str,
    status: str,
    activity: str,
    result: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    if agent_name in LIVE_AGENT_STATUS:
        LIVE_AGENT_STATUS[agent_name]["status"] = status
        LIVE_AGENT_STATUS[agent_name]["current_activity"] = activity
        if result is not None:
            LIVE_AGENT_STATUS[agent_name]["last_result"] = result[:300]
        LIVE_AGENT_STATUS[agent_name]["error"] = error