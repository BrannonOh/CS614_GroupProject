import json
import os

from langgraph.graph import StateGraph, END
from graph.state import SpeechScriptState
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import ValidationError

from schemas.structure_checking import StructureCheckOutput

from prompts.structure_checking_agent import STRUCTURE_SYSTEM_PROMPT, build_structure_user_prompt
from config.llm_config import get_structure_llm

def make_structure_feedback_brief(
        structure_result: StructureCheckOutput,
) -> dict: 
    """
    Convert the full structure checker output into a compact revision brief
    for the TED revision agent. 
    """
    print("Creating structure feedback brief...")
    blocking_issues = [
        {
            "severity": issue.severity,
            "category": issue.category,
            "planner_ref": issue.planner_ref,
            "ted_ref": issue.ted_ref,
            "message": issue.message,
            "suggested_fix": issue.suggested_fix,
        }
        for issue in structure_result.issues 
        if issue.severity in {"critical", "major"}
    ]

    section_alignment_notes = [
        {
            "planner_section_id": sa.planner_section_id,
            "planner_section_name": sa.planner_section_name,
            "mapped_ted_section_ids": sa.mapped_ted_section_ids,
            "purpose_coverage": sa.purpose_coverage,
            "points_coverage": sa.points_coverage,
            "facts_coverage": sa.facts_coverage,
            "missing_or_weakened_points": sa.missing_or_weakened_points,
            "missing_or_weakened_facts": sa.missing_or_weakened_facts,
            "notes": sa.notes,
        }
        for sa in structure_result.section_alignment
        if (
            sa.purpose_coverage != "full"
            or sa.points_coverage != "full"
            or sa.facts_coverage != "full"
        )
    ]

    return {
        "overall_summary": structure_result.overall_summary,
        "blocking_issues": blocking_issues,
        "warnings": structure_result.warnings,
        "section_alignment_notes": section_alignment_notes,
        "suggested_fixes": structure_result.suggested_fixes,
    }

def structure_checking_agent_node(state: SpeechScriptState):
    # 1. Read `planner_blueprint` and current `ted_blueprint`
    # 2. Call the structure checker LLM
    # 3. If successful:
    #       - Save `structure_check_result`
    #       - Reset `structure_check_retry_count`
    #       - Clear `last_error`
    #       - If `is_valid` == False, create `structure_feedback_brief`
    # 4. If parsing fails: 
    #       - Clear `structure_check_result`
    #       - Increment `structure_check_retry_count`
    #       - Store `last_error`
    print("Running Structure Checking agent...")
    planner_blueprint = state["planner_blueprint"]
    ted_blueprint = state["ted_blueprint"]
    planner_blueprint_json = planner_blueprint.model_dump_json()
    ted_blueprint_json = ted_blueprint.model_dump_json()

    try: 
        structure_model = get_structure_llm()
        structure_result = structure_model.invoke(
            [
                SystemMessage(content=STRUCTURE_SYSTEM_PROMPT),
                HumanMessage(content=build_structure_user_prompt(planner_blueprint_json, ted_blueprint_json))
            ]
        )

        updates = {
            "structure_check_result": structure_result,
            "structure_check_retry_count": 0,
            "last_error": None,
        }

        if structure_result.is_valid is False: 
            updates["structure_feedback_brief"] = make_structure_feedback_brief(structure_result)
        else:
            updates["structure_feedback_brief"] = None 

        return updates 
    
    except ValidationError as e: 
        return {
            "structure_check_result": None, 
            "structure_check_retry_count": state["structure_check_retry_count"] + 1,
            "last_error": f"Pydantic validation failed: {str(e)}"
        }        
    
    except Exception as e: 
        return {
            "structure_check_result": None, 
            "structure_check_retry_count": state["structure_check_retry_count"] + 1,
            "last_error": f"Structure check failed: {str(e)}"
        }