from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import AgentLogModel
from app.api.schemas import AgentLogResponse
from app.orchestration.workflow import workflow_manager

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.get("/status")
def get_all_agents_status():
    return {
        "agents": workflow_manager.get_live_agents(),
    }


@router.get("/logs", response_model=List[AgentLogResponse])
def get_agent_execution_logs(
    task_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(AgentLogModel)
    if task_id is not None:
        query = query.filter(AgentLogModel.task_id == task_id)
    return query.order_by(AgentLogModel.timestamp.desc()).limit(limit).all()