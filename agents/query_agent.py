
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

def Query_Agent(state: SpeechScriptState):
    user_input = state["user_input"]
    attempts = state.get("query_attempts", 0)

    query_check_prompt = f"""
You are an expert fact-checking agent.
Your task is to identify factual claims and fact-check them.
Instructions:
1. Extract every fact from the details.
2. Check each fact for accuracy using reliable public sources. You MUST use Tavily for every factual verification and include the exact URL returned by the tool.
3. Evaluate whether the fact is relevant to the occasion described.
4. If a fact refers to information that is unlikely to be publicly available, do NOT attempt to fact-check it. Mark it as supported = null.
5. Return ONLY valid JSON. Following the output format strictly.

Details:
{user_input}

Output format:
{{
  "checks_results": [
    {{
      "serial_number": 1,
      "fact_identified": "<extracted factual claim>",
      "supported": <true | false | null>,
      "relevant": <true | false | null>,
      "source_url": "<URL used to verify the claim, or null if not checked>",
      "feedback": "<optional feedback>"
    }}
  ]
}}
"""

    # Run search agent to gather facts with web access
    search_result = search_agent.invoke({
        "messages": [
            {"role": "user", "content": query_check_prompt}
        ]
    })

    # Extract last assistant message and parse into structured output
    last_message = search_result["messages"][-1].content
    print("FACT CHECK RESULTS")
    print(last_message)
    parsed_json = json.loads(last_message)
    facts = QueryCheckBlueprint.model_validate(parsed_json)

    # Step 3: Evaluate results
    query_approved = True
    feedback_list = []
    for item in facts.checks_results:
        if item.supported is False or item.relevant is False:
            query_approved = False
            feedback_list.append(
                f"Fact: {item.fact_identified}\n"
                f"Supported: {item.supported}\n"
                f"Relevance: {item.relevant}\n"
                f"Feedback: {item.feedback}"
            )

    query_feedback = "\n\n".join(feedback_list)  # cleaner separator

    return {
        "query_check": facts,
        "query_facts": [f.model_dump() for f in facts.checks_results],
        "query_approved": query_approved,
        "query_attempts": attempts + 1,
        "query_feedback": query_feedback,
        "user_input": user_input,
    }



