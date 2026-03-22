import json
import os

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
    raw_text = "\n\n".join(file.read_text(encoding="utf-8") for file in samples_dir.glob("*.txt"))
    stylistic_script = state["stylistic_script"]

    if stylistic_script is None: 
        return {
            "judge_b_result": None, 
            "last_error": "Judging agent (B) called without final_speech.",
        }
    
    planner_blueprint_json = planner_blueprint.model_dump_json(indent=2)

    try:
        judging_model = get_judging_llm_b()
        judge_b_result = judging_model.invoke(
            [
                SystemMessage(content=JUDGING_SYSTEM_PROMPT),
                HumanMessage(
                    content=build_judging_user_prompt(
                        planner_blueprint_json,
                        raw_text,
                        stylistic_script,
                    )
                )
            ]
        )

        return {
            "judge_b_result": judge_b_result,
            "last_error": None,
        }
    
    except ValidationError as e:
        return {
            "judge_b_result": None,
            "last_error": f"Pydantic validation failed: {str(e)}"
        }        
    
    except Exception as e:
        return {
            "judge_b_result": None,
            "last_error": f"Judging agent (B) failed: {str(e)}"
        }