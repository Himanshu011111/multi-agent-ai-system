import time
import os
from typing import Optional, Dict, Any, List
from app.orchestration.graph import orchestrator_graph
from app.orchestration.state import AgentState, LIVE_AGENT_STATUS
from app.database.db import SessionLocal
from app.database.models import (
    TaskModel,
    DocumentModel,
    ResearchSourceModel,
    GeneratedReportModel,
)
from app.utils.logger import logger
from app.agents.critic_agent import CriticAgent
from app.services.llm_service import LLMService


class WorkflowManager:
    def __init__(self):
        # Cache latest full execution state per task_id for quick UI inspection
        self.task_results_cache: Dict[int, Dict[str, Any]] = {}
        self.critic_agent = CriticAgent(LLMService())

    async def execute_task(
        self,
        task_id: int,
        human_approved: bool = False,
        csv_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = time.time()
        db = SessionLocal()

        try:
            task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task:
                raise ValueError(f"Task ID {task_id} not found.")

            # Mark task as running
            task.status = "running"
            db.commit()

            # Check if documents or CSV files exist in the database
            uploaded_docs = db.query(DocumentModel).all()
            has_docs = len(uploaded_docs) > 0

            if not csv_file_path:
                csv_doc = (
                    db.query(DocumentModel)
                    .filter(DocumentModel.file_type == "csv")
                    .order_by(DocumentModel.uploaded_at.desc())
                    .first()
                )
                if csv_doc and os.path.exists(csv_doc.file_path):
                    csv_file_path = csv_doc.file_path

            initial_state: AgentState = {
                "task_id": task.id,
                "title": task.title,
                "user_instruction": task.description,
                "has_uploaded_docs": has_docs,
                "csv_file_path": csv_file_path,
                "human_approved": human_approved,
                "revision_count": 0,
            }

            logger.info(f"Starting multi-agent workflow execution for Task #{task_id}...")
            final_state = await orchestrator_graph.ainvoke(initial_state)

            duration = round(time.time() - start_time, 2)
            self.task_results_cache[task_id] = dict(final_state)

            # Refresh task record before updating final fields
            db.refresh(task)

            if task.status == "cancelled":
                task.execution_duration = duration
                db.commit()
                return dict(final_state)

            if final_state.get("error"):
                task.status = "failed"
                task.quality_explanation = final_state.get("error")
                task.execution_duration = duration
                db.commit()
                return dict(final_state)

            # Persist collected research sources
            for src in final_state.get("sources", []):
                db_source = ResearchSourceModel(
                    task_id=task.id,
                    title=src.get("title", "Reference Source")[:250],
                    url=src.get("url", ""),
                    snippet=src.get("snippet", ""),
                )
                db.add(db_source)

            # Persist generated PDF & DOCX reports
            pdf_path = final_state.get("pdf_path")
            if pdf_path and os.path.exists(pdf_path):
                db.add(
                    GeneratedReportModel(
                        task_id=task.id,
                        report_title=f"{task.title} (PDF)",
                        file_path=pdf_path,
                        format="pdf",
                    )
                )

            docx_path = final_state.get("docx_path")
            if docx_path and os.path.exists(docx_path):
                db.add(
                    GeneratedReportModel(
                        task_id=task.id,
                        report_title=f"{task.title} (DOCX)",
                        file_path=docx_path,
                        format="docx",
                    )
                )
            # Run Enterprise Critic Agent Quality Audit + Self-Correction Loop
            report_text = (
                final_state.get("final_report")
                or final_state.get("report")
                or final_state.get("draft_report")
                or final_state.get("summary")
                or ""
            )
            if report_text:
                quality_review = self.critic_agent.evaluate(
                    topic=task.title,
                    draft_report=report_text,
                    threshold=72,
                )

                # Self-Correction: Rewrite once if quality score < 80
                if not quality_review.get("passed", True) and quality_review.get("revision_instructions"):
                    logger.info(
                        f"Task #{task_id} scored {quality_review.get('overall_score')}/100 (<80). Running Critic self-correction..."
                    )
                    refine_prompt = (
                        f"Topic: {task.title}\n\n"
                        f"Critic Revision Instructions: {quality_review['revision_instructions']}\n"
                        f"Missing Gaps to Address: {', '.join(quality_review.get('missing_gaps', []))}\n\n"
                        f"Original Draft:\n{report_text[:6000]}\n\n"
                        "Rewrite and upgrade this report into a comprehensive, well-structured enterprise document addressing all gaps above."
                    )
                    improved_report = self.critic_agent.llm.generate_text(
                        prompt=refine_prompt,
                        system_instruction="You are an Executive Research Editor. Produce a polished, accurate, structured report.",
                        temperature=0.3,
                    )
                    if improved_report and len(improved_report.strip()) > 100:
                        report_text = improved_report.strip()
                        for key in ("final_report", "report", "draft_report", "summary"):
                            if key in final_state:
                                final_state[key] = report_text
                        quality_review = self.critic_agent.evaluate(
                            topic=task.title,
                            draft_report=report_text,
                            threshold=72,
                        )
                        quality_review["self_corrected"] = True

                final_state["quality_review"] = quality_review
                final_state["quality_score"] = float(
                    quality_review.get("overall_score", final_state.get("quality_score", 85.0))
                )
                strengths = ", ".join(quality_review.get("strengths", []))
                if strengths:
                    tag = " [Auto-Refined]" if quality_review.get("self_corrected") else ""
                    final_state["quality_explanation"] = (
                        f"Critic Audit ({quality_review.get('overall_score', 85)}/100){tag}: {strengths}"
                    )
                self.task_results_cache[task_id] = dict(final_state)


            task.task_type = final_state.get("task_type", task.task_type)
            task.quality_score = final_state.get("quality_score", 85.0)
            task.quality_explanation = final_state.get("quality_explanation", "")
            task.execution_duration = duration
            task.status = final_state.get("automation_status", "completed")

            db.commit()
            logger.info(
                f"Task #{task_id} finished with status='{task.status}' in {duration}s (QA Score: {task.quality_score})."
            )
            return dict(final_state)

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            logger.error(f"Workflow execution failed for Task #{task_id}: {str(e)}")
            task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if task:
                task.status = "failed"
                task.quality_explanation = f"Workflow Exception: {str(e)}"
                task.execution_duration = duration
                db.commit()
            return {"task_id": task_id, "error": str(e)}
        finally:
            db.close()

    def cancel_task(self, task_id: int) -> bool:
        db = SessionLocal()
        try:
            task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if task and task.status in ["pending", "running", "needs_approval"]:
                task.status = "cancelled"
                db.commit()
                logger.info(f"Task #{task_id} marked as cancelled.")
                return True
            return False
        finally:
            db.close()

    def get_task_details(self, task_id: int) -> Dict[str, Any]:
        return self.task_results_cache.get(task_id, {})

    def get_live_agents(self) -> List[Dict[str, Any]]:
        return list(LIVE_AGENT_STATUS.values())


workflow_manager = WorkflowManager()