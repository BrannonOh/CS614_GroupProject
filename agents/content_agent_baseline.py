import sys
from pathlib import Path

sys.path.append(str(Path.cwd().parent))  

#from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, ValidationError, Field

from dotenv import load_dotenv
load_dotenv(dotenv_path =".env")

from schemas.content_working_blueprint import ContentBlueprint
from graph.state import SpeechScriptState as State

# Set your API key
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"] 
# Initialize the model object (NOT a string)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)

### helpers ###

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


content_llm = llm.with_structured_output(ContentBlueprint)


def Content_Agent(state: State) -> State:
    user_input = state["ted_blueprint"]
    config = state["config"]
    attempts = state.get("content_attempts", 0)

    prompt = f"""
You are a Content Agent.

Your task:
- Identify weak claims in all must_include_facts and must_include_points.
- Identify missing claims in all must_include_facts and must_include_points.
- Ensure each section has at least 3 strong must_include_facts and 3 strong must_include_points.
- For missing claims, infer the most likely intended claim from the section purpose, narrative_role, transition_out, big_idea, and existing facts.
- Prefer claims that directly support the stated purpose of the section.
- Do not introduce side topics or generic ideas unless they are clearly required.
- If a section already has enough strong claims, do not invent extras.
- Return exactly one section_plan for every ted section in the input.
- Do not skip any section.
- Even if a section has no weak claims, return it with weak_claims = [].

JSON:
{json.dumps(user_input, indent=2)}

Config:
{json.dumps(config, indent=2)}
"""

    try:
        result: ContentBlueprint = content_llm.invoke(prompt)

        content_tasks: List[Dict[str, Any]] = []
        for sec in result.section_plans:
            content_tasks.extend([w.model_dump() for w in sec.weak_claims])

        content_results = [s.model_dump() for s in result.section_plans]
        final_json = apply_content_tasks_to_json(user_input, content_tasks)

        # print("CONTENT AGENT content_tasks:")
        # print(json.dumps(content_tasks, indent=2, default=str))
        # print("CONTENT AGENT content_results:")
        # print(json.dumps(content_results, indent=2, default=str))
        # print("===== CONTENT AGENT END =====")

        return {
            "content_check": result.model_dump(),
            "content_results": content_results,
            "content_tasks": content_tasks,
            "content_approved": True,
            "content_attempts": attempts + 1,
            "content_feedback": result.content_feedback,
            "user_input": user_input,
            "config": config,
            "final_json": final_json,
        }

    except Exception as e:
        # print("CONTENT AGENT ERROR:")
        # print(str(e))
        # print("===== CONTENT AGENT END (ERROR) =====")

        return {
            "content_approved": False,
            "content_feedback": f"Structured output failed: {str(e)}",
            "content_attempts": attempts + 1,
            "user_input": user_input,
            "config": config,
        }