import sys
from pathlib import Path

sys.path.append(str(Path.cwd().parent))  

import json
import os
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, ValidationError, Field

from dotenv import load_dotenv
load_dotenv(dotenv_path =".env")

from schemas.content_working_blueprint import ContentBlueprint as ContentWorkingBlueprint
from graph.state import SpeechScriptState as State # rename for compatibility

# Set your API key
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"] 

# Initialize the model object (NOT a string)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)

### helpers ###
# This function appends new text to existing points
# Note: The function outputs a dict, not json
def apply_content_tasks_to_json(
    ted_json: Dict[str, Any],
    content_tasks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    updated = deepcopy(ted_json)
    section_map = {sec["id"]: sec for sec in updated["ted_sections"]}

    for task in content_tasks:
        section_id = task["section_id"]
        field_name = task["field_name"]
        original_text = task.get("original_text")
        new_text = task["new_text"]

        if original_text == "None":
            original_text = None

        section = section_map.get(section_id)
        if not section:
            continue

        if field_name not in section:
            section[field_name] = []

        if original_text is None:
            section[field_name].append(new_text)
        else:
            try:
                idx = section[field_name].index(original_text)
                section[field_name][idx] = new_text
            except ValueError:
                section[field_name].append(new_text)

    return updated

content_llm = llm.with_structured_output(ContentWorkingBlueprint)

def Content_Agent(state: State) -> State:
    print("\n========CONTENT AGENT ========")
    user_input = state["ted_blueprint"] # This is a Pydantic object
    # config = state["config"] Removed, not required for baseline
    attempts = state.get("content_attempts", 0)

    # Changes to prompt: Removed this requirement - Ensure each section has at least 3 strong must_include_facts and 3 strong must_include_points.
    # Removed placeholder for config since in baseline this is not passed in
    # Convert Pydantic user input to JSON for LLM's easy reading
    prompt = f"""
You are a Content Agent.

Your task:
- Identify weak claims in all must_include_facts and must_include_points.
- Identify missing claims in all must_include_facts and must_include_points.
- For missing claims, infer the most likely intended claim from the section purpose, narrative_role, transition_out, big_idea, and existing facts.
- Prefer claims that directly support the stated purpose of the section.
- Do not introduce side topics or generic ideas unless they are clearly required.
- If a section already has enough strong claims, do not invent extras.
- Return exactly one section_plan for every ted section in the input.
- Do not skip any section.
- Even if a section has no weak claims, return it with weak_claims = [].

JSON:
{user_input.model_dump_json()}
"""

    try:
        result: ContentWorkingBlueprint = content_llm.invoke(prompt)
        print("Result from Content Agent LLM")
        print(result)

        content_tasks: List[Dict[str, Any]] = []
        for sec in result.section_plans:
            # Extract each WeakClaim() object in each section and convert to Dict
            content_tasks.extend([w.model_dump() for w in sec.weak_claims])

        # Convert each section's findings into Dict in the result
        content_results = [s.model_dump() for s in result.section_plans]

        # convert user_input to Dict (JSON compatible) as apply_content_tasks_to_json only accepts Dict input
        final_json = apply_content_tasks_to_json(user_input.model_dump(mode="json"), content_tasks)

        # print("CONTENT AGENT content_tasks:")
        # print(json.dumps(content_tasks, indent=2, default=str))
        # print("CONTENT AGENT content_results:")
        # print(json.dumps(content_results, indent=2, default=str))
        # print("===== CONTENT AGENT END =====")
        print("Success!\nOutput: Content Working Blueprint")
        print(final_json)

        return {
            "content_check": result.model_dump(),
            "content_results": content_results,
            "content_tasks": content_tasks,
            "content_approved": True,
            "content_attempts": attempts + 1,
            "content_feedback": result.content_feedback,
            "user_input": user_input,
            # "config": config, # Removed from baseline flow
            "content_blueprint": final_json,
        }

    except Exception as e:
        print("CONTENT AGENT ERROR:")
        print(str(e))

        return {
            "content_approved": False,
            "content_feedback": f"Structured output failed: {str(e)}",
            "content_attempts": attempts + 1,
            "user_input": user_input,
            # "config": config, # Removed from baseline flow
        }