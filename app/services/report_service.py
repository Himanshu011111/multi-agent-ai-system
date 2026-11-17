import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from docx import Document
from app.config import settings
from app.utils.logger import logger

class ReportService:
    def generate_pdf_report(self, title: str, content: str, filename: str) -> str:
        filepath = os.path.join(settings.reports_dir, f"{filename}.pdf")
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=15
            )
            body_style = ParagraphStyle(
                'ReportBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=10,
                leading=14
            )
            
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 10))
            
            for paragraph in content.split("\n\n"):
                if paragraph.strip():
                    story.append(Paragraph(paragraph.replace("\n", "<br/>"), body_style))
                    
            doc.build(story)
            logger.info(f"Successfully generated PDF report: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise e

    def generate_docx_report(self, title: str, content: str, filename: str) -> str:
        filepath = os.path.join(settings.reports_dir, f"{filename}.docx")
        try:
            doc = Document()
            doc.add_heading(title, level=1)
            
            for paragraph in content.split("\n\n"):
                if paragraph.strip():
                    doc.add_paragraph(paragraph)
                    
            doc.save(filepath)
            logger.info(f"Successfully generated DOCX report: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error generating DOCX report: {str(e)}")
            raise e

report_service = ReportService()