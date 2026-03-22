import json
import os

from pprint import pprint
from pathlib import Path
from langgraph.graph import StateGraph, END
from graph.state import SpeechScriptState
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import ValidationError

from prompts.judging_agent import JUDGING_SYSTEM_PROMPT, build_judging_user_prompt
from config.llm_config import get_judging_llm_b

def judging_agent_b_node(state: SpeechScriptState):
    print("Running Judging Agent B...")

    # Load raw text from "data/samples"
    samples_dir = Path("data/samples")

    planner_blueprint = state["planner_blueprint"]
    content_blueprint = state["content_blueprint"]
    raw_text = "\n\n".join(file.read_text(encoding="utf-8") for file in samples_dir.glob("*.txt"))
    stylistic_script = state["stylistic_script"]

    if stylistic_script is None:
        return {
            "judge_b_result": None,
            "last_error": "Judging agent (B) called without final_speech.",
        }

    if planner_blueprint is None or content_blueprint is None:
        return {
            "judge_b_result": None,
            "last_error": "Judging agent (B) called without planner_blueprint or content_blueprint.",
        }

    planner_blueprint_json = (
        planner_blueprint.model_dump_json(indent=2)
        if hasattr(planner_blueprint, "model_dump_json")
        else json.dumps(planner_blueprint, indent=2)
    )
    content_blueprint_json = (
        content_blueprint.model_dump_json(indent=2)
        if hasattr(content_blueprint, "model_dump_json")
        else json.dumps(content_blueprint, indent=2)
    )

    try:
        judging_model = get_judging_llm_b()
        judge_b_result = judging_model.invoke(
            [
                SystemMessage(content=JUDGING_SYSTEM_PROMPT),
                HumanMessage(
                    content=build_judging_user_prompt(
                        planner_blueprint_json,
                        raw_text,
                        content_blueprint_json,
                        stylistic_script,
                    )
                )
            ]
        )
        print("Successful! Judge B Result:")
        pprint(judge_b_result.model_dump(), sort_dicts=False)
        return {
            "judge_b_result": judge_b_result,
            "last_error": None,
        }
    
    except ValidationError as e:
        print(f"Judge B: Output Pydantic validation failed!")
        return {
            "judge_b_result": None,
            "last_error": f"Pydantic validation failed: {str(e)}"
        }        
    
    except Exception as e:
        print(f"Judge B: Output generation failed!")
        return {
            "judge_b_result": None,
            "last_error": f"Judging agent (B) failed: {str(e)}"
        }
