import json
import os

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from prompts.judging_agent import JUDGING_SYSTEM_PROMPT, build_judging_user_prompt
from config.llm_config import judging_llm

def judging_agent_node(state: GraphState, judging_llm):
    print("Running Judging Agent...")

    planner_blueprint = state["planner_blueprint"]
    final_speech = state["final_speech"]

    if final_speech is None: 
        return {
            "judging_result": None, 
            "last_error": "Judging agent called without final_speech.",
        }
    
    planner_blueprint_json = planner_blueprint.model_dump_json(indent=2)

    try:
        judging_result = judging_llm.invoke(
            [
                SystemMessage(content=JUDGING_SYSTEM_PROMPT),
                HumanMessage(
                    content=build_judging_user_prompt(
                        planner_blueprint_json,
                        final_speech,
                    )
                )
            ]
        )

        return {
            "judging_result": judging_result,
            "last_error": None,
        }
    
    except Exception as e:
        return {
            "judging_result": None,
            "last_error": f"Judging agent failed: {str(e)}"
        }