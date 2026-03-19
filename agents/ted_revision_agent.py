import json
import os

from langgraph.graph import StateGraph, END
from graph.state import SpeechScriptState
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import ValidationError

from prompts.ted_revision_agent import TED_REVISION_SYSTEM_PROMPT, build_ted_revision_user_prompt
from config.llm_config import get_ted_revision_llm

def ted_revision_agent_node(state: SpeechScriptState):
    """
    Revise the current TED blueprint using structure checker feedback.

    Behavior:
    - Uses planner blueprint + previous TED blueprint + structure_feedback_brief
    - Expects structured output matching TEDBlueprint
    - On success:
        * overwrites ted_blueprint with revised blueprint
        * increments ted_revision_count
        * clears last_error
        * clears previous structure checker artifacts
    - On failure:
        * keeps existing ted_blueprint
        * increments ted_revision_count
        * stores error message in last_error
    """
    print("Reached TED revision agent")

    planner_blueprint = state["planner_blueprint"]
    ted_blueprint = state["ted_blueprint"]
    structure_feedback_brief = state["structure_feedback_brief"]

    planner_blueprint_json = planner_blueprint.model_dump_json(indent=2)
    ted_blueprint_json = ted_blueprint.model_dump_json(indent=2)
    structure_feedback_brief_json = json.dumps(structure_feedback_brief, indent=2)

    try:
        ted_revision_model = get_ted_revision_llm()
        revised_ted_blueprint = ted_revision_model.invoke(
            [
                SystemMessage(content=TED_REVISION_SYSTEM_PROMPT),
                HumanMessage(content=build_ted_revision_user_prompt(
                    planner_blueprint_json, 
                    ted_blueprint_json,
                    structure_feedback_brief_json,
                    )
                ),
            ]
        )

        return {
            "ted_blueprint": revised_ted_blueprint,
            "ted_revision_count": state["ted_revision_count"] + 1,
            "structure_check_result": None, 
            "structure_feedback_brief": None,
            "last_error": None,
        }

    except ValidationError as e: 
        return {
            "ted_revision_count": state.get("ted_revision_count", 0) + 1,
            "last_error": f"TED revision / Pydantic validation failed: {str(e)}",
        }
            
    except Exception as e:
        return {
            "ted_revision_count": state.get("ted_revision_count", 0) + 1,
            "last_error": f"TED revision / Pydantic validation failed: {str(e)}",
        }