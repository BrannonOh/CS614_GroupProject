import json
import os
import pprint

from langgraph.graph import StateGraph, END
from graph.state import SpeechScriptState
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import ValidationError

from prompts.ted_agent_baseline import TED_SYSTEM_PROMPT, build_ted_user_prompt
from config.llm_config import get_ted_llm

def ted_agent_node(state: SpeechScriptState) -> dict:
    # 1. Read `planner_blueprint` from state 
    # 2. Call the TED LLM with structured output
    # 3. If successful, store the parsed `ted_blueprint` and clear any TED-generation error
    # 4. If parsing fails, increment the TED retry counter and store the error message 
    print("Running TED agent...")
    planner_blueprint = state["planner_blueprint"] # Pydantic Object
    planner_blueprint_json = planner_blueprint.model_dump_json() # Convert Pydantic Object to JSON

    try: 
        ted_model = get_ted_llm()
        ted_blueprint = ted_model.invoke([
            SystemMessage(content=TED_SYSTEM_PROMPT),
            HumanMessage(content=build_ted_user_prompt(planner_blueprint_json))
        ])

        # Apply to state 
        print(f"Success! TED blueprint: {pprint(state.get("ted_blueprint").model_dump(), sort_dicts=False)}")
        return {
            "ted_blueprint": ted_blueprint,
            "ted_validation_retry_count": 0,
            "ted_output_retry_count": 0,
            "ted_error_type": None,
            "last_error": None,
        }
    
    except ValidationError as e: 
        print(f"TED Blueprint Pydantic validation failed: {str(e)}")
        return {
            "ted_blueprint": None,
            "ted_validation_retry_count": state.get("ted_validation_retry_count", 0) + 1,
            "ted_error_type": "validation",
            "last_error": f"TED Blueprint Pydantic validation failed: {str(e)}"
        }
    
    except Exception as e: 
        print(f"TED Blueprint Generation failed: {str(e)}")
        return {
            "ted_blueprint": None,
            "ted_output_retry_count": state.get("ted_output_retry_count", 0) + 1,
            "ted_error_type": "generation",
            "last_error": f"TED Blueprint Generation failed: {str(e)}",
        }