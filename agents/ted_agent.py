import json
import os

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from prompts.ted_agent import TED_SYSTEM_PROMPT, build_ted_user_prompt
from config.llm_config import ted_llm 


def ted_agent_node(state: GraphState, ted_llm) -> dict:
    # 1. Read `planner_blueprint` from state 
    # 2. Call the TED LLM with structured output
    # 3. If successful, store the parsed `ted_blueprint` and clear any TED-generation error
    # 4. If parsing fails, increment the TED retry counter and store the error message 
    print("Running TED agent...")
    planner_blueprint = state["planner_blueprint"] # Pydantic Object
    planner_blueprint_json = planner_blueprint.model_dump_json() # Convert Pydantic Object to JSON

    try: 
        ted_blueprint = ted_llm.invoke([
            SystemMessage(content=TED_SYSTEM_PROMPT),
            HumanMessage(content=build_ted_user_prompt(planner_blueprint_json))
        ])

        # Apply to state 
        return {
            "ted_blueprint": ted_blueprint,
            "ted_output_retry_count": 0,
            "last_error": None,
        }
    
    except Exception as e: 
        return {
            "ted_blueprint": None,
            "ted_output_retry_count": state["ted_output_retry_count"] + 1,
            "last_error": f"TED Generation / Pydantic validation failed: {str()}",
        }