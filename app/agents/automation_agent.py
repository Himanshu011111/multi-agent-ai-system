import datetime
from app.services.report_service import report_service
from app.utils.logger import logger

class AutomationAgent:
    def __init__(self):
        self.name = "Task Automation Agent"
        self.role = "Artifact Export (PDF/DOCX), Execution Logging & Human-in-the-Loop Gatekeeper"

    def requires_human_approval(self, user_instruction: str) -> bool:
        sensitive_keywords = ["send email", "delete", "publish", "execute script", "deploy", "payment", "transfer"]
        lower_instr = user_instruction.lower()
        return any(kw in lower_instr for kw in sensitive_keywords)

    def execute_automation(self, task_id: int, title: str, final_report: str, user_instruction: str, human_approved: bool = False) -> dict:
        logger.info(f"[{self.name}] Executing automation pipeline for Task #{task_id}")
        
        # Check Human-in-the-Loop requirement for sensitive actions
        if self.requires_human_approval(user_instruction) and not human_approved:
            logger.warning(f"[{self.name}] Sensitive action detected. Halting for Human-in-the-Loop approval.")
            return {
                "status": "needs_approval",
                "message": "Sensitive action detected in instruction. Please review the generated report and approve execution.",
                "pdf_path": None,
                "docx_path": None
            }
            
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_filename = f"task_{task_id}_report_{timestamp}"
        
        pdf_path = report_service.generate_pdf_report(title=title, content=final_report, filename=base_filename)
        docx_path = report_service.generate_docx_report(title=title, content=final_report, filename=base_filename)
        
        logger.info(f"[{self.name}] Generated downloadable reports: PDF={pdf_path}, DOCX={docx_path}")
        return {
            "status": "completed",
            "message": "Reports generated and workflow automation completed successfully.",
            "pdf_path": pdf_path,
            "docx_path": docx_path
        }

automation_agent = AutomationAgent()