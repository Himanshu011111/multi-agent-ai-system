from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import TaskModel, ResearchSourceModel
from app.api.schemas import (
    TaskCreateRequest,
    TaskExecuteRequest,
    TaskResponse,
    ResearchSourceResponse,
)
from app.orchestration.workflow import workflow_manager
from app.utils.logger import logger

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.get("/summary/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(TaskModel).count()
    completed = db.query(TaskModel).filter(TaskModel.status == "completed").count()
    running = db.query(TaskModel).filter(TaskModel.status == "running").count()
    failed = db.query(TaskModel).filter(TaskModel.status == "failed").count()
    needs_approval = db.query(TaskModel).filter(TaskModel.status == "needs_approval").count()

    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "running_tasks": running,
        "failed_tasks": failed,
        "needs_approval_tasks": needs_approval,
    }


@router.post("/create", response_model=TaskResponse)
def create_task(payload: TaskCreateRequest, db: Session = Depends(get_db)):
    try:
        new_task = TaskModel(
            title=payload.title.strip(),
            description=payload.description.strip(),
            task_type=payload.task_type,
            status="pending",
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        logger.info(f"Created new Task #{new_task.id}: {new_task.title}")
        return new_task
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create task in database.")


@router.post("/{task_id}/execute", response_model=TaskResponse)
async def execute_task_workflow(
    task_id: int,
    payload: TaskExecuteRequest = TaskExecuteRequest(),
    db: Session = Depends(get_db),
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task #{task_id} not found.")

    state_result = await workflow_manager.execute_task(
        task_id=task_id,
        human_approved=payload.human_approved,
        csv_file_path=payload.csv_file_path,
    )

    db.refresh(task)
    response_obj = TaskResponse.model_validate(task)
    response_obj.orchestration_details = state_result
    return response_obj


@router.post("/{task_id}/approve", response_model=TaskResponse)
async def approve_sensitive_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task #{task_id} not found.")

    state_result = await workflow_manager.execute_task(
        task_id=task_id,
        human_approved=True,
    )

    db.refresh(task)
    response_obj = TaskResponse.model_validate(task)
    response_obj.orchestration_details = state_result
    return response_obj


@router.post("/{task_id}/cancel")
def cancel_running_task(task_id: int):
    cancelled = workflow_manager.cancel_task(task_id)
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Task could not be cancelled (already completed or does not exist).",
        )
    return {"task_id": task_id, "status": "cancelled", "message": "Task cancelled successfully."}


@router.get("/", response_model=List[TaskResponse])
def list_all_tasks(db: Session = Depends(get_db)):
    tasks = db.query(TaskModel).order_by(TaskModel.created_at.desc()).all()
    results = []
    for t in tasks:
        item = TaskResponse.model_validate(t)
        item.orchestration_details = workflow_manager.get_task_details(t.id)
        results.append(item)
    return results


@router.get("/sources/all", response_model=List[ResearchSourceResponse])
def list_all_research_sources(db: Session = Depends(get_db)):
    return (
        db.query(ResearchSourceModel)
        .order_by(ResearchSourceModel.created_at.desc())
        .all()
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_by_id(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task #{task_id} not found.")

    response_obj = TaskResponse.model_validate(task)
    response_obj.orchestration_details = workflow_manager.get_task_details(task_id)
    return response_obj