import sys
from pathlib import Path

sys.path.append(str(Path.cwd().parent))  

#from __future__ import annotations

import json
import os
import time
import traceback
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, TypedDict

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import Command, interrupt

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, ValidationError, Field

from tavily import TavilyClient

from graph.state import SpeechScriptState

# helpers 
from utils.helpers import (
    get_sections,
    get_section_id,
    get_claim_field_specs,
    get_field_items,
    set_field_items,
    safe_json_loads,
    dedupe_preserve_order,
    attach_citation,
    count_query_shortfalls,
    truncate_text,
    run_tavily_search,
    build_initial_state,
    strip_citations,
)

#schemas

from schemas.content_working_blueprint import (
    WeakClaim,
    ContentSectionPlan,
    ContentBlueprint,
    EvidenceCandidate,
    ResearchItem,
    ResearchBlueprint,
    Citation,
    FactCitationMap,
    PointCitationMap,
    HookSchema,
    TedSectionGrounded,
    FinalOutputGrounded,
    GroundingBlueprint,
)

GOOGLE_API_KEY = "AIzaSyAHWWj4dK2mu1X5H1XVRjzSZfRC7mhvJwc"
GOOGLE_CSE_ID = "b0444741720284e80"
TAVILY_API_KEY= "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"

tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Set your API key
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Initialize the model object (NOT a string)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)


# In[5]:


# configuration
# There must be at least 3 of must_include_facts and must_include_points each

GENERIC_JSON_CONFIG: Dict[str, Any] = {
    "sections_path": "ted_sections",
    "section_id_field": "id",
    "fact_fields": [
        {"name": "must_include_facts", "min_items": 3, "type": "fact"}
    ],
    "point_fields": [
        {"name": "must_include_points", "min_items": 3, "type": "point"}
    ],
    "max_queries_per_weak_item": 3,
    "top_k_tavily_results": 3,
    "max_retry_rounds": 1,
}




# linking up search engine
def build_tavily() -> TavilyClient:
    return TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# LLM links
content_llm = llm.with_structured_output(ContentBlueprint)
grounding_llm = llm.with_structured_output(GroundingBlueprint)
research_llm = llm




# content agent

content_llm = llm.with_structured_output(ContentBlueprint)

def Content_Agent(state: SpeechScriptState):
    user_input = state["user_input"] # TAKE IN TED BLUEPRINT
    config = GENERIC_JSON_CONFIG ## TO CHECK WITH JESS ON LOGIC
    attempts = state.get("content_attempts", 0)

    print("\n===== CONTENT AGENT START =====")
    print("state keys:", list(state.keys()))
    print("content_attempts:", attempts)
    print("user_input exists:", "user_input" in state)
    print("config exists:", "config" in state)

    prompt = f"""
You are a Content Agent. Your task is to review the outline and identify weak or missing claims that require additional information retrieval. 

Definitions:
- Weak claim: A statement that is vague, unsupported, lacks specificity, or would benefit from evidence, data, or examples.
- Missing claim: Important information that is expected for the section but is not present.

Instructions:
1. **Review ALL "must_include_facts" and "must_include_points"**.
2. Identify ALL weak claims and convert each into a clear, specific search query.
3. Identify ALL missing claims based on the section’s context and generate appropriate search queries.
4. Follow the output format strictly.

Outline:
{user_input}

Output Format:
{json.dumps(config, indent=2)}
"""

    try:
        result: ContentBlueprint = content_llm.invoke(prompt)

        print("=====CONTENT AGENT raw result:====")
        print(result)

        content_tasks = []
        for sec in result.section_plans:
            content_tasks.extend([w.model_dump() for w in sec.weak_claims])

        content_results = [s.model_dump() for s in result.section_plans]

        print("CONTENT AGENT content_tasks:")
        print(json.dumps(content_tasks, indent=2, default=str))
        print("CONTENT AGENT content_results:")
        print(json.dumps(content_results, indent=2, default=str))
        print("===== CONTENT AGENT END =====")

        return {
            "content_check": result.model_dump(),
            "content_results": content_results,
            "content_tasks": content_tasks,
            "content_approved": True,
            "content_attempts": attempts + 1,
            "content_feedback": result.content_feedback,
            "user_input": user_input,
            "config": config,
            #"graph_state": state["graph_state"],
        }

    except Exception as e:
        import traceback

        print("CONTENT AGENT ERROR:")
        print(traceback.format_exc())
        print("===== CONTENT AGENT END (ERROR) =====")

        return {
            "content_approved": False,
            "content_feedback": f"Structured output failed: {str(e)}",
            "content_attempts": attempts + 1,
            "user_input": user_input,
            "config": config,
            #"graph_state": state["graph_state"], ##TO CHECK WITH JESS
        }



# # RESEARCH AGENT

# # Note: Cannot fully replace this with with_structured_output because Tavily returns raw data not generated by LLM

# def llm_rank_evidence(
#     original_text: str,
#     claim_type: str,
#     query: str,
#     tavily_results: List[Dict[str, Any]],
# ) -> List[Dict[str, Any]]:
#     ranking_prompt = f"""
# You are an evidence ranking agent. Your task is to select the most relevant and usable evidence to strengthen a weak or missing claim.

# Definitions:
# - relevance_score (0–1): How directly the result addresses the claim/query.
# - usefulness_score (0–1): How easily the result can be used in the final output (specific, clear, factual, well-structured).
# - combined_score (0–1): Overall quality. Must reflect BOTH relevance and usefulness (not an average—prioritise strong evidence).

# Instructions:
# 1. Review the claim, claim type, query, and all Tavily results.
# 2. Score EACH result using the three metrics.
# 3. Rank results by combined_score (highest first).
# 4. Select ONLY the top 3 results.
# 5. For facts, prefer evidence with concrete specifics, numbers, dates, named entities.
# 6. For points, prefer evidence that sharpens the analytical point.
# 7. Follow the output format strictly.

# Original text:
# {original_text}

# Claim type:
# {claim_type}

# Query:
# {query}

# Raw Tavily results:
# {json.dumps(tavily_results, indent=2)}

# Output format:
# {{
#   "top_evidence": [
#     {{
#       "snippet": "<best usable snippet>",
#       "source_title": "<title or null>",
#       "source_url": "<url or null>",
#       "published_date": "<date or null>",
#       "tavily_score": 0.0,
#       "relevance_score": 0.0,
#       "usefulness_score": 0.0,
#       "combined_score": 0.0,
#       "feedback": "<optional note>"
#     }}
#   ]
# }}
# """

#     result = research_llm.invoke(ranking_prompt)

#     print("=== llm_rank_evidence raw result ===")
#     print(result)
#     print("=== llm_rank_evidence result.content ===")
#     print(getattr(result, "content", None))

#     raw_content = getattr(result, "content", "")

#     if isinstance(raw_content, str):
#         content_text = raw_content
#     elif isinstance(raw_content, list):
#         text_parts = []
#         for part in raw_content:
#             if isinstance(part, dict) and part.get("type") == "text":
#                 text_parts.append(part.get("text", ""))
#         content_text = "\n".join(text_parts).strip()
#     else:
#         content_text = str(raw_content)

#     print("=== llm_rank_evidence content_text ===")
#     print(content_text)

#     parsed = safe_json_loads(content_text)

#     print("=== llm_rank_evidence parsed ===")
#     print(parsed)

#     if parsed and isinstance(parsed.get("top_evidence"), list):
#         cleaned = []
#         for item in parsed["top_evidence"][:3]:
#             try:
#                 cleaned.append(EvidenceCandidate.model_validate(item).model_dump())
#             except Exception as e:
#                 print("Validation error:", e)
#                 continue
#         if cleaned:
#             return cleaned

#     fallback = []
#     sorted_results = sorted(
#         tavily_results,
#         key=lambda x: float(x.get("score", 0.0) or 0.0),
#         reverse=True,
#     )[:3]

#     for item in sorted_results:
#         snippet = truncate_text((item.get("content") or "").strip(), 500)
#         if not snippet:
#             continue
#         score = float(item.get("score", 0.0) or 0.0)
#         fallback.append({
#             "snippet": snippet,
#             "source_title": item.get("title"),
#             "source_url": item.get("url"),
#             "published_date": item.get("published_date"),
#             "tavily_score": score,
#             "relevance_score": score,
#             "usefulness_score": score,
#             "combined_score": score,
#             "feedback": "Fallback ranking used."
#         })

#     return fallback


# def Research_Agent(state: State) -> State:
#     import time
#     import traceback

#     user_input = state["user_input"]
#     config = state["config"]
#     attempts = state.get("research_attempts", 0)
#     content_tasks = state.get("content_tasks", [])

#     client = tavily_client
#     research_results: List[Dict[str, Any]] = []

#     print("===== RESEARCH AGENT START =====")
#     print("state keys:", list(state.keys()))
#     print(f"content_tasks count = {len(content_tasks)}")

#     # for task in content_tasks[:1]:   # for debugging
#     for task in content_tasks:
#         print("\nRESEARCH task:")
#         print({
#             "section_id": task.get("section_id"),
#             "field_name": task.get("field_name"),
#             "claim_type": task.get("claim_type"),
#             "original_text": truncate_text(task.get("original_text", ""), 120),
#         })

#         queries = task.get("search_queries", [])
#         if not queries:
#             fallback_query = f'{task.get("section_id", "")} {task.get("field_name", "")} {task.get("claim_type", "")} {task.get("reason", "")}'
#             queries = [fallback_query]

#         # for query in queries[:1]:   # for debugging
#         for query in queries:
#             print(f"Running Tavily query: {query}")

#             response = run_tavily_search(client, query, config)
#             if response is None:
#                 research_results.append({
#                     "section_id": task.get("section_id"),
#                     "field_name": task.get("field_name"),
#                     "claim_type": task.get("claim_type"),
#                     "original_text": task.get("original_text"),
#                     "query": query,
#                     "top_evidence": [],
#                     "feedback": "Tavily search failed after retries."
#                 })
#                 continue

#             try:
#                 raw_results = response.get("results", [])
#                 print("TAVILY_raw_results", raw_results)
#                 print(f"Tavily raw_results count: {len(raw_results)}")

#                 ranked = llm_rank_evidence(
#                     original_text=task["original_text"],
#                     claim_type=task["claim_type"],
#                     query=query,
#                     tavily_results=raw_results,
#                 )

#                 research_results.append({
#                     "section_id": task["section_id"],
#                     "field_name": task["field_name"],
#                     "claim_type": task["claim_type"],
#                     "original_text": task["original_text"],
#                     "query": query,
#                     "top_evidence": ranked,
#                 })

#                 time.sleep(1)

#             except Exception:
#                 print("Ranking error:")
#                 print(traceback.format_exc())

#                 research_results.append({
#                     "section_id": task.get("section_id"),
#                     "field_name": task.get("field_name"),
#                     "claim_type": task.get("claim_type"),
#                     "original_text": task.get("original_text"),
#                     "query": query,
#                     "top_evidence": [],
#                     "feedback": "Ranking/post-processing failed."
#                 })

#     print("\nRESEARCH SUMMARY")
#     for i, item in enumerate(research_results):
#         print(f"\n[{i}] section={item.get('section_id')} | query={item.get('query')}")
#         print(f"top_evidence_count={len(item.get('top_evidence', []))}")
#         for j, ev in enumerate(item.get("top_evidence", [])[:3]):
#             print(f"  evidence {j+1}: {ev.get('source_title')} | score={ev.get('combined_score')}")
#             print(f"    snippet: {truncate_text(ev.get('snippet', ''), 180)}")

#     research_feedback = f"Completed research for {len(research_results)} query runs."

#     return {
#         "research_check": {
#             "research_results": research_results,
#             "research_feedback": research_feedback,
#         },
#         "research_results": research_results,
#         "research_approved": True,
#         "research_attempts": attempts + 1,
#         "research_feedback": research_feedback,
#         "user_input": user_input,
#         "graph_state": state["graph_state"],
#         "config": config,
#         "content_tasks": content_tasks,
#         "content_results": state.get("content_results", []),
#         "retry_count": state.get("retry_count", 0),
#     }


# # # **Grounding Agent**

# # In[19]:


# # grounding agent


# def Grounding_Agent(state: State) -> State:
#     user_input = state["user_input"]
#     content_results = state.get("content_results", [])
#     research_results = state.get("research_results", [])
#     config = state.get("config", {})
#     retry_count = state.get("retry_count", 0)

#     print("\n===== GROUNDING AGENT START =====")
#     print("state keys:", list(state.keys()))
#     print("research_results_count:", len(research_results))
#     print("content_results_count:", len(content_results))

#     prompt = f"""
# You are a Grounding Agent.

# Your role:
# - Preserve the original JSON format exactly for:
#   - hook
#   - big_idea
#   - ted_sections
#   - must_include_facts as List[str]
#   - must_include_points as List[str]
# - Do NOT convert must_include_facts or must_include_points into object lists.
# - Enrich the outline conservatively using the research evidence.
# - Remove weak, duplicate, or unsupported facts/points.
# - Append newly supported facts/points into the existing string lists.
# - Add parallel citation fields:
#   - fact_citations
#   - point_citations
# - Each item in fact_citations / point_citations must include:
#   - text
#   - citations
#   - added_by_grounding
# - text must exactly match the corresponding fact/point string in must_include_facts or must_include_points.
# - Do not invent unsupported claims.
# - Keep the output outline-level only.



# Original user JSON:
# {json.dumps(user_input, indent=2)}

# Content planning results:
# {json.dumps(content_results, indent=2)}

# Research results:
# {json.dumps(research_results, indent=2)}

# Return structured output only.
# """

#     try:
#         result: GroundingBlueprint = grounding_llm.invoke(prompt)

#         print("GROUNDING AGENT raw result:")
#         print(result)
#         print("GROUNDING final_output:")
#         print(json.dumps(result.final_output.model_dump(), indent=2, default=str))
#         print("===== GROUNDING AGENT END =====")

#         return {
#             "grounding_check": result.model_dump(),
#             "grounding_results": result.model_dump(),
#             "grounding_approved": True,
#             "grounding_feedback": result.grounding_feedback,
#             "needs_retry": result.needs_retry,
#             "retry_reason": result.retry_reason,
#             "final_output": result.final_output.model_dump(),
#             "research_results": research_results,
#             "content_results": content_results,
#             "user_input": user_input,
#             "graph_state": state["graph_state"],
#             "config": config,
#             "retry_count": retry_count,
#         }

#     except Exception as e:
#         print("GROUNDING AGENT ERROR:")
#         print(traceback.format_exc())
#         print("===== GROUNDING AGENT END (ERROR) =====")

#         return {
#             "grounding_approved": False,
#             "grounding_feedback": str(e),
#             "needs_retry": False,
#             "retry_reason": str(e),
#             "final_output": {},
#             "research_results": research_results,
#             "content_results": content_results,
#             "user_input": user_input,
#             "graph_state": state["graph_state"],
#             "config": config,
#             "retry_count": retry_count,
#         }


