
from typing import List, Dict, Any, TypedDict, Optional
from langgraph.graph import StateGraph, START, END
import json
import os
import getpass
import re
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from pprint import pprint
from pydantic import BaseModel, ValidationError

import sys
from pathlib import Path

sys.path.append(str(Path.cwd().parent))  

from schemas.query_check_blueprint import QueryCheckBlueprint
from schemas.planner_blueprint import PlannerBlueprint

from graph.state import SpeechScriptState

from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from dotenv import load_dotenv
load_dotenv(dotenv_path =".env")

    
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0
)



tavily_search_tool = TavilySearch(
    max_results=5,
    topic="general",
)

search_agent = create_agent(llm,[tavily_search_tool])


def Planner_Agent(state: SpeechScriptState):
    user_input = state.get("user_input")

    planner_prompt = f"""
You are an expert speech coach.

Given verified speech details, your task is to produce a structured speech plan.

Instructions:
1. Facts should be placed under "must_include_facts". All other content should be placed under "must_include_points".
2. estimated_wpm must be an integer between 120 and 150.
3. target_word_count must be calculated using: time_limit_minutes * estimated_wpm.
4. Return ONLY valid JSON. Follow the JSON structure strictly. Do not include explanations or text outside the JSON.

Speech Details: {user_input}

JSON structure:
{{
  "request": {{
    "topic": "",
    "audience": "",
    "occasion": "",
    "time_limit_minutes": 5
  }},
  "targets": {{
    "estimated_wpm": 130,
    "target_word_count": 650
  }},
  "sections": [
    {{
      "section_id": "S1",
      "name": "",
      "purpose": "",
      "must_include_points": [],
      "must_include_facts": []
    }}
  ]
}}
"""

    response = llm.invoke(planner_prompt)
    print("PLANNER RESPONSE")
    content_str = response.content.strip()
    
    # Robust markdown fence removal
    content_str = re.sub(r"^```(?:json)?\s*\n?", "", content_str)
    content_str = re.sub(r"\n?```$", "", content_str).strip()
    print("CONTENT_STR")
    print(content_str)
    try:
        plan = PlannerBlueprint(**json.loads(content_str))
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(
            f"Planner_Agent failed to parse LLM output: {e}\n"
            f"Raw output:\n{content_str}"
        )

    return {"planner_blueprint": plan}

