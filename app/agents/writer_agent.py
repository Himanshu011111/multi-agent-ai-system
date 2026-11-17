from app.services.llm_service import llm_service
from app.utils.logger import logger

class WriterAgent:
    def __init__(self):
        self.name = "Writer Agent"
        self.role = "Structured Report Drafting, Executive Summarization & Documentation"

    def draft_report(self, title: str, user_instruction: str, research_notes: str, analysis_insights: str, sources: list[dict]) -> str:
        logger.info(f"[{self.name}] Drafting structured report for: {title}")
        
        formatted_sources = "\n".join(
            [f"- [{s.get('title', 'Source')}]({s.get('url', '#')})" for s in sources]
        ) if sources else "No external URLs cited."
        
        system_prompt = (
            "You are the Writer Agent. Produce a well-structured, professional research and analysis report in Markdown. "
            "Include an Executive Summary, Key Findings, Detailed Analysis, Recommendations, and a References section. "
            "Maintain an objective, formal tone suitable for technical and academic documentation."
        )
        
        prompt = f"""
Report Title: {title}
Original User Request: {user_instruction}

Verified Research Findings:
{research_notes}

Data & Trend Analysis:
{analysis_insights}

Verified References:
{formatted_sources}

Write the complete, polished report:
"""
        draft = llm_service.generate_text(prompt, system_instruction=system_prompt, temperature=0.3)
        logger.info(f"[{self.name}] Report draft completed ({len(draft)} characters).")
        return draft

writer_agent = WriterAgent()