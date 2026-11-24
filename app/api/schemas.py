import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Short title for the task")
    description: str = Field(..., min_length=5, description="Detailed natural-language instruction")
    task_type: str = Field(default="general_research", description="Initial task category")


class TaskExecuteRequest(BaseModel):
    human_approved: bool = Field(default=False, description="Flag confirming human approval for sensitive tasks")
    csv_file_path: Optional[str] = Field(default=None, description="Optional path to uploaded CSV file for analysis")


class AgentLogResponse(BaseModel):
    id: int
    task_id: int
    agent_name: str
    action: str
    status: str
    details: Optional[str] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


class ResearchSourceResponse(BaseModel):
    id: int
    task_id: int
    title: str
    url: str
    snippet: Optional[str] = None
    relevance_score: float
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class GeneratedReportResponse(BaseModel):
    id: int
    task_id: int
    report_title: str
    file_path: str
    format: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    task_type: str
    status: str
    quality_score: Optional[float] = None
    quality_explanation: Optional[str] = None
    execution_duration: float
    created_at: datetime.datetime
    updated_at: datetime.datetime
    logs: List[AgentLogResponse] = []
    sources: List[ResearchSourceResponse] = []
    reports: List[GeneratedReportResponse] = []
    orchestration_details: Dict[str, Any] = {}
    quality_review: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_type: str
    file_size: int
    uploaded_at: datetime.datetime

    class Config:
        from_attributes = True


class DocumentQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Question to ask across uploaded documents")


class DocumentQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[str]


class DirectReportRequest(BaseModel):
    task_id: int
    title: str = Field(..., min_length=3, max_length=255)
    content: str = Field(..., min_length=10)
    format: str = Field(default="pdf", pattern="^(pdf|docx)$")