# %% [markdown]
# ## Main changes
# - Added evaluation

# %% [markdown]
# # Config

# %%
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

from langchain_tavily import TavilySearch
from langchain.agents import create_agent

# %%
# if not os.environ.get("OPENAI_API_KEY"):
#     os.environ["OPENAI_API_KEY"] = getpass.getpass("OPENAI_API_KEY:\n")
    
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0
)

# %%
# if not os.environ.get("TAVILY_API_KEY"):
#     os.environ["TAVILY_API_KEY"] = getpass.getpass("Tavily API key:\n")

tavily_search_tool = TavilySearch(
    max_results=5,
    topic="general",
)

search_agent = create_agent(llm,[tavily_search_tool])

# %% [markdown]
# # Agents


# %%
def collect_user_feedback(topic, audience, occasion, time_limit_in_minutes) -> str:
    revised_content = input("Revised Content to be included (i.e. Point, Examples and Facts):").strip()
    return (
        f"Topic: {topic}\n"
        f"Audience: {audience}\n"
        f"Occasion: {occasion}\n"
        f"Time limit (in minutes): {time_limit_in_minutes}\n\n"
        f"Revised Content:\n{revised_content}"
    )

# %%
def Human_Feedback(state: State) -> dict:
    print("\n" + "=" * 50)
    print("FACT-CHECK FAILED — Amendment required")
    print("=" * 50)
    print(f"{state.get('query_feedback', 'No feedback provided.')}")
    print()
    print("Please re-enter your speech content with the issues fixed.")

    # Extract existing values from state
    existing_input = state.get("user_input", "")
    parsed = {}
    for line in existing_input.splitlines():
        for key in ["Topic", "Audience", "Occasion", "Time limit (in minutes)"]:
            if line.startswith(f"{key}:"):
                parsed[key] = line[len(f"{key}:"):].strip()

    updated_input = collect_user_feedback(
        topic=parsed.get("Topic", ""),
        audience=parsed.get("Audience", ""),
        occasion=parsed.get("Occasion", ""),
        time_limit_in_minutes=parsed.get("Time limit (in minutes)", ""),
    )

    return {
        "user_input":     updated_input,
        "graph_state":    updated_input,
        "query_approved": False,
        "query_feedback": "",
    }


# %%
