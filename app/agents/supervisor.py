import json
from app.services.llm_service import llm_service
from app.utils.logger import logger

class SupervisorAgent:
    def __init__(self):
        self.name = "Supervisor Agent"
        self.role = "Task Classification, Routing & Workflow Supervision"

    def analyze_and_route(self, user_instruction: str, has_uploaded_docs: bool = False) -> dict:
        logger.info(f"[{self.name}] Analyzing instruction: {user_instruction[:80]}...")
        
        system_prompt = (
            "You are the Supervisor / Orchestrator Agent of an enterprise Multi-Agent AI Research & Automation System. "
            "Analyze the user's request and classify it into one of: 'research', 'document_qa', 'data_analysis', or 'complex_automation'. "
            "Respond strictly in valid JSON format with keys: 'task_type', 'requires_research' (bool), 'requires_rag' (bool), "
            "'requires_analysis' (bool), 'requires_automation' (bool), and 'supervisor_notes' (string)."
        )
        
        prompt = f"""
User Instruction: {user_instruction}
Uploaded Documents Available: {has_uploaded_docs}

Provide routing classification JSON:
"""
        try:
            raw_response = llm_service.generate_text(prompt, system_instruction=system_prompt, temperature=0.1)
            cleaned = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            decision = json.loads(cleaned)
            logger.info(f"[{self.name}] Routing decision: {decision.get('task_type')}")
            return decision
        except Exception as e:
            logger.error(f"[{self.name}] Routing fallback triggered due to error: {str(e)}")
            return {
                "task_type": "document_qa" if has_uploaded_docs else "research",
                "requires_research": not has_uploaded_docs,
                "requires_rag": has_uploaded_docs,
                "requires_analysis": True,
                "requires_automation": True,
                "supervisor_notes": "Fallback routing applied due to parsing variance."
            }

supervisor_agent = SupervisorAgent()