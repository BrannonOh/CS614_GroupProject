import json
import os

from pathlib import Path
from langgraph.graph import StateGraph, END
from graph.state import SpeechScriptState
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import ValidationError

from prompts.judging_agent import JUDGING_SYSTEM_PROMPT, build_judging_user_prompt
from config.llm_config import get_judging_llm_a

def judging_agent_a_node(state: SpeechScriptState):
    print("Running Judging Agent A...")

    # Load raw text from "data/samples"
    samples_dir = Path("data/samples")

    planner_blueprint = state["planner_blueprint"]
    raw_text = "\n\n".join(file.read_text(encoding="utf-8") for file in samples_dir.glob("*.txt"))
    stylistic_script = state["stylistic_script"]

    if stylistic_script is None: 
        return {
            "judge_a_result": None, 
            "last_error": "Judging agent (A) called without final_speech.",
        }
    
    planner_blueprint_json = planner_blueprint.model_dump_json(indent=2)

    try:
        judging_model = get_judging_llm_a()
        judge_a_result = judging_model.invoke(
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
            "judge_a_result": judge_a_result,
            "last_error": None,
        }
    
    except ValidationError as e:
        return {
            "judge_a_result": None,
            "last_error": f"Pydantic validation failed: {str(e)}"
        }        
    
    except Exception as e:
        return {
            "judge_a_result": None,
            "last_error": f"Judging agent (A) failed: {str(e)}"
        }