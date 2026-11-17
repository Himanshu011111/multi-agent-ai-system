from langgraph.graph import StateGraph, END
from app.orchestration.state import AgentState, update_live_agent_status
from app.agents.supervisor import supervisor_agent
from app.agents.planner_agent import planner_agent
from app.agents.research_agent import research_agent
from app.agents.analyst_agent import analyst_agent
from app.agents.writer_agent import writer_agent
from app.agents.reviewer_agent import reviewer_agent
from app.agents.automation_agent import automation_agent
from app.database.db import SessionLocal
from app.database.models import TaskModel, AgentLogModel
from app.utils.logger import logger


def _log_to_db(task_id: int, agent_name: str, action: str, status: str, details: str = "") -> None:
    db = SessionLocal()
    try:
        log_entry = AgentLogModel(
            task_id=task_id,
            agent_name=agent_name,
            action=action,
            status=status,
            details=details[:2000] if details else "",
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to write agent log to DB: {str(e)}")
        db.rollback()
    finally:
        db.close()


def _check_cancelled(task_id: int) -> bool:
    db = SessionLocal()
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        return bool(task and task.status == "cancelled")
    finally:
        db.close()


def supervisor_node(state: AgentState) -> dict:
    task_id = state["task_id"]
    if _check_cancelled(task_id):
        return {"error": "Task was cancelled by user."}

    agent_name = supervisor_agent.name
    update_live_agent_status(agent_name, "running", "Classifying task and determining agent routing...")
    try:
        decision = supervisor_agent.analyze_and_route(
            user_instruction=state["user_instruction"],
            has_uploaded_docs=state.get("has_uploaded_docs", False),
        )
        summary = f"Classified as '{decision.get('task_type')}'. Notes: {decision.get('supervisor_notes')}"
        update_live_agent_status(agent_name, "completed", "Routing complete", result=summary)
        _log_to_db(task_id, agent_name, "Task Classification & Routing", "success", summary)
        return {
            "task_type": decision.get("task_type", "research"),
            "requires_research": decision.get("requires_research", True),
            "requires_rag": decision.get("requires_rag", False),
            "requires_analysis": decision.get("requires_analysis", True),
            "requires_automation": decision.get("requires_automation", True),
            "supervisor_notes": decision.get("supervisor_notes", ""),
        }
    except Exception as e:
        update_live_agent_status(agent_name, "error", "Failed during routing", error=str(e))
        _log_to_db(task_id, agent_name, "Task Classification & Routing", "error", str(e))
        return {"error": f"Supervisor error: {str(e)}"}


def planner_node(state: AgentState) -> dict:
    if state.get("error") or _check_cancelled(state["task_id"]):
        return {"error": state.get("error") or "Task was cancelled by user."}

    task_id = state["task_id"]
    agent_name = planner_agent.name
    update_live_agent_status(agent_name, "running", "Decomposing goal into prioritized subtasks...")
    try:
        plan = planner_agent.create_execution_plan(
            user_instruction=state["user_instruction"],
            task_type=state.get("task_type", "research"),
        )
        subtask_count = len(plan.get("subtasks", []))
        summary = f"Created roadmap with {subtask_count} subtasks: {plan.get('plan_summary', '')}"
        update_live_agent_status(agent_name, "completed", "Execution plan ready", result=summary)
        _log_to_db(task_id, agent_name, "Execution Roadmap Generation", "success", summary)
        return {"execution_plan": plan}
    except Exception as e:
        update_live_agent_status(agent_name, "error", "Failed creating plan", error=str(e))
        _log_to_db(task_id, agent_name, "Execution Roadmap Generation", "error", str(e))
        return {"error": f"Planner error: {str(e)}"}


async def research_node(state: AgentState) -> dict:
    if state.get("error") or _check_cancelled(state["task_id"]):
        return {"error": state.get("error") or "Task was cancelled by user."}

    task_id = state["task_id"]
    agent_name = research_agent.name
    update_live_agent_status(agent_name, "running", "Searching web & querying RAG vector store...")
    try:
        use_web = state.get("requires_research", True)
        use_rag = state.get("requires_rag", False) or state.get("has_uploaded_docs", False)

        result = await research_agent.conduct_research(
            query=state["user_instruction"],
            use_web=use_web,
            use_rag=use_rag,
        )
        sources = result.get("sources", [])
        notes = result.get("research_notes", "")
        summary = f"Collected {len(sources)} sources and synthesized {len(notes)} chars of verified facts."
        update_live_agent_status(agent_name, "completed", "Research synthesis complete", result=summary)
        _log_to_db(task_id, agent_name, "Web & RAG Research", "success", summary)
        return {
            "research_notes": notes,
            "sources": sources,
        }
    except Exception as e:
        update_live_agent_status(agent_name, "error", "Research failed", error=str(e))
        _log_to_db(task_id, agent_name, "Web & RAG Research", "error", str(e))
        return {"error": f"Research error: {str(e)}"}


def analyst_node(state: AgentState) -> dict:
    if state.get("error") or _check_cancelled(state["task_id"]):
        return {"error": state.get("error") or "Task was cancelled by user."}

    task_id = state["task_id"]
    agent_name = analyst_agent.name
    update_live_agent_status(agent_name, "running", "Running statistical analysis and pattern synthesis...")
    try:
        analysis = analyst_agent.analyze(
            user_instruction=state["user_instruction"],
            research_notes=state.get("research_notes", ""),
            csv_file_path=state.get("csv_file_path"),
        )
        summary = "Extracted statistical summaries, trends, and structured insights."
        if analysis.get("chart_path"):
            summary += f" Generated chart at {analysis['chart_path']}."
        update_live_agent_status(agent_name, "completed", "Analysis complete", result=summary)
        _log_to_db(task_id, agent_name, "Data & Trend Analysis", "success", summary)
        return {
            "analysis_insights": analysis.get("analysis_insights", ""),
            "stats_summary": analysis.get("stats_summary", ""),
            "chart_path": analysis.get("chart_path"),
        }
    except Exception as e:
        update_live_agent_status(agent_name, "error", "Analysis failed", error=str(e))
        _log_to_db(task_id, agent_name, "Data & Trend Analysis", "error", str(e))
        return {"error": f"Analyst error: {str(e)}"}


def writer_node(state: AgentState) -> dict:
    if state.get("error") or _check_cancelled(state["task_id"]):
        return {"error": state.get("error") or "Task was cancelled by user."}

    task_id = state["task_id"]
    agent_name = writer_agent.name
    revision_count = state.get("revision_count", 0)
    action_label = "Revising Report Draft" if revision_count > 0 else "Drafting Structured Report"
    update_live_agent_status(agent_name, "running", f"{action_label}...")
    try:
        draft = writer_agent.draft_report(
            title=state["title"],
            user_instruction=state["user_instruction"],
            research_notes=state.get("research_notes", ""),
            analysis_insights=state.get("analysis_insights", ""),
            sources=state.get("sources", []),
        )
        summary = f"Generated structured Markdown report ({len(draft)} characters)."
        update_live_agent_status(agent_name, "completed", "Report draft ready", result=summary)
        _log_to_db(task_id, agent_name, action_label, "success", summary)
        return {
            "draft_report": draft,
            "revision_count": revision_count + 1,
        }
    except Exception as e:
        update_live_agent_status(agent_name, "error", "Report drafting failed", error=str(e))
        _log_to_db(task_id, agent_name, action_label, "error", str(e))
        return {"error": f"Writer error: {str(e)}"}


def reviewer_node(state: AgentState) -> dict:
    if state.get("error") or _check_cancelled(state["task_id"]):
        return {"error": state.get("error") or "Task was cancelled by user."}

    task_id = state["task_id"]
    agent_name = reviewer_agent.name
    update_live_agent_status(agent_name, "running", "Auditing factual accuracy, citations & quality score...")
    try:
        review = reviewer_agent.review_output(
            user_instruction=state["user_instruction"],
            draft_report=state.get("draft_report", ""),
            research_notes=state.get("research_notes", ""),
        )
        score = float(review.get("quality_score", 85.0))
        explanation = review.get("quality_explanation", "Passed quality review.")
        revision_needed = bool(review.get("revision_needed", False))
        refined = review.get("refined_report") or state.get("draft_report", "")

        summary = f"QA Score: {score}/100 | Revision Needed: {revision_needed} | {explanation}"
        update_live_agent_status(agent_name, "completed", f"QA Complete ({score}/100)", result=summary)
        _log_to_db(task_id, agent_name, "Quality Assurance & Audit", "success", summary)
        return {
            "quality_score": score,
            "quality_explanation": explanation,
            "revision_needed": revision_needed,
            "final_report": refined,
        }
    except Exception as e:
        update_live_agent_status(agent_name, "error", "QA audit failed", error=str(e))
        _log_to_db(task_id, agent_name, "Quality Assurance & Audit", "error", str(e))
        return {"error": f"Reviewer error: {str(e)}"}


def automation_node(state: AgentState) -> dict:
    if state.get("error") or _check_cancelled(state["task_id"]):
        return {"error": state.get("error") or "Task was cancelled by user."}

    task_id = state["task_id"]
    agent_name = automation_agent.name
    update_live_agent_status(agent_name, "running", "Generating PDF/DOCX artifacts & checking approval rules...")
    try:
        final_text = state.get("final_report") or state.get("draft_report", "")
        auto_result = automation_agent.execute_automation(
            task_id=task_id,
            title=state["title"],
            final_report=final_text,
            user_instruction=state["user_instruction"],
            human_approved=state.get("human_approved", False),
        )
        status = auto_result.get("status", "completed")
        msg = auto_result.get("message", "")
        update_live_agent_status(agent_name, "completed", f"Automation {status}", result=msg)
        _log_to_db(task_id, agent_name, "Report Export & Workflow Automation", "success", msg)
        return {
            "automation_status": status,
            "automation_message": msg,
            "pdf_path": auto_result.get("pdf_path"),
            "docx_path": auto_result.get("docx_path"),
        }
    except Exception as e:
        update_live_agent_status(agent_name, "error", "Automation failed", error=str(e))
        _log_to_db(task_id, agent_name, "Report Export & Workflow Automation", "error", str(e))
        return {"error": f"Automation error: {str(e)}"}


def should_revise(state: AgentState) -> str:
    if state.get("error"):
        return "automation"
    if state.get("revision_needed", False) and state.get("revision_count", 0) < 2:
        logger.info("Reviewer requested revision; routing back to Writer Agent.")
        return "writer"
    return "automation"


def build_orchestration_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("research", research_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("automation", automation_node)

    workflow.set_entry_point("supervisor")
    workflow.add_edge("supervisor", "planner")
    workflow.add_edge("planner", "research")
    workflow.add_edge("research", "analyst")
    workflow.add_edge("analyst", "writer")
    workflow.add_edge("writer", "reviewer")

    workflow.add_conditional_edges(
        "reviewer",
        should_revise,
        {
            "writer": "writer",
            "automation": "automation",
        },
    )
    workflow.add_edge("automation", END)

    return workflow.compile()


orchestrator_graph = build_orchestration_graph()