import os
import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import GeneratedReportModel, TaskModel
from app.api.schemas import GeneratedReportResponse, DirectReportRequest
from app.services.report_service import report_service
from app.orchestration.workflow import workflow_manager
from app.utils.logger import logger

router = APIRouter(prefix="/api/reports", tags=["Reports & Analytics"])


@router.get("/", response_model=List[GeneratedReportResponse])
def list_generated_reports(db: Session = Depends(get_db)):
    return (
        db.query(GeneratedReportModel)
        .order_by(GeneratedReportModel.created_at.desc())
        .all()
    )


@router.post("/generate", response_model=GeneratedReportResponse)
def generate_custom_report(payload: DirectReportRequest, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task #{payload.task_id} not found.")

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"custom_task_{payload.task_id}_{timestamp}"

    try:
        if payload.format == "pdf":
            file_path = report_service.generate_pdf_report(
                title=payload.title,
                content=payload.content,
                filename=filename,
            )
        else:
            file_path = report_service.generate_docx_report(
                title=payload.title,
                content=payload.content,
                filename=filename,
            )

        report_record = GeneratedReportModel(
            task_id=payload.task_id,
            report_title=f"{payload.title} ({payload.format.upper()})",
            file_path=file_path,
            format=payload.format,
        )
        db.add(report_record)
        db.commit()
        db.refresh(report_record)
        return report_record
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating custom report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/download/{report_id}")
def download_report(report_id: int, db: Session = Depends(get_db)):
    report = (
        db.query(GeneratedReportModel)
        .filter(GeneratedReportModel.id == report_id)
        .first()
    )
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk.")

    media_type = (
        "application/pdf"
        if report.format == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return FileResponse(
        path=report.file_path,
        filename=os.path.basename(report.file_path),
        media_type=media_type,
    )


@router.get("/chart/{task_id}")
def get_task_analysis_chart(task_id: int):
    details = workflow_manager.get_task_details(task_id)
    chart_path = details.get("chart_path")
    if not chart_path or not os.path.exists(chart_path):
        raise HTTPException(status_code=404, detail="No chart generated for this task.")
    return FileResponse(path=chart_path, media_type="image/png")