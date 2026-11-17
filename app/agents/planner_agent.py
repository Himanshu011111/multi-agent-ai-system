import json
from app.services.llm_service import llm_service
from app.utils.logger import logger

class PlannerAgent:
    def __init__(self):
        self.name = "Planner Agent"
        self.role = "Task Decomposition, Prioritization & Roadmap Generation"

    def create_execution_plan(self, user_instruction: str, task_type: str) -> dict:
        logger.info(f"[{self.name}] Creating execution plan for task type: {task_type}")
        
        system_prompt = (
            "You are the Planner Agent. Break down the user's instruction into 3 to 6 actionable, sequential subtasks. "
            "Respond strictly in valid JSON format with keys: 'plan_summary' (string) and 'subtasks' (list of objects, "
            "each containing 'step_id' (int), 'title' (string), 'assigned_agent' (string), 'priority' (High/Medium/Low), and 'dependency' (string))."
        )
        
        prompt = f"""
User Instruction: {user_instruction}
Task Classification: {task_type}

Generate the structured execution plan JSON:
"""
        try:
            raw_response = llm_service.generate_text(prompt, system_instruction=system_prompt, temperature=0.2)
            cleaned = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            plan = json.loads(cleaned)
            logger.info(f"[{self.name}] Generated {len(plan.get('subtasks', []))} subtasks.")
            return plan
        except Exception as e:
            logger.error(f"[{self.name}] Fallback plan generated due to error: {str(e)}")
            return {
                "plan_summary": f"Standard execution roadmap for: {user_instruction}",
                "subtasks": [
                    {"step_id": 1, "title": "Gather information & sources", "assigned_agent": "Research Agent", "priority": "High", "dependency": "None"},
                    {"step_id": 2, "title": "Analyze findings & patterns", "assigned_agent": "Data Analyst Agent", "priority": "High", "dependency": "Step 1"},
                    {"step_id": 3, "title": "Draft structured report", "assigned_agent": "Writer Agent", "priority": "Medium", "dependency": "Step 2"},
                    {"step_id": 4, "title": "Quality assurance & verification", "assigned_agent": "Reviewer Agent", "priority": "High", "dependency": "Step 3"}
                ]
            }

planner_agent = PlannerAgent()