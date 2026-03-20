#!/usr/bin/env python
# coding: utf-8

# In[1]:


# !pip install google-search-results tavily-python requests
# !pip install scikit-learn
# !pip install sentence-transformers
# !pip install ipywidgets
# !pip install langchain-google-genai
# !pip install serpapi google-search-results
# !pip install tavily-python
# !pip install langchain-tavily


# In[2]:


from __future__ import annotations

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



# In[3]:


GOOGLE_API_KEY = "AIzaSyAHWWj4dK2mu1X5H1XVRjzSZfRC7mhvJwc"
GOOGLE_CSE_ID = "b0444741720284e80"
TAVILY_API_KEY= "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"
# SERPAPI_API_KEY= "3bfb05c601c9c69619c2a6e95b2005a1599b0c1fa819cc12be2bb5232d7ee99b"

# Create Tavily client after key is loaded; SerpAPI is request-based usage & Google is custom search which is just a HTTP endpoint. Hence no need to create client-based SDK
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


# Optional debug check
print("GOOGLE:", bool(GOOGLE_API_KEY))
print("GOOGLE_CSE_ID:", bool(GOOGLE_CSE_ID))
# print("SERPAPI:", bool(SERPAPI_API_KEY))
print("TAVILY:", bool(TAVILY_API_KEY))


# In[4]:


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


# In[6]:


# ted_agent_json
ted_agent_json = {
    "hook": {
        "type": "question",
        "description": "What happens to the world economy when one country that supplies nearly one-fifth of global LNG is suddenly disrupted by war?"
    },
    "big_idea": "The escalation of the U.S.-Israeli war on Iran has turned the Strait of Hormuz and Qatar's LNG system into a global energy stress point. Because Qatar accounts for nearly 20% of global LNG exports and all of its LNG moves through Hormuz, even a temporary shutdown can tighten supply, lift prices, force buyers into competition for replacement cargoes, and test how much resilience exists in storage, contracts, and alternative supply.",
    "ted_sections": [
        {
            "id": "TS1",
            "narrative_role": "hook_and_context",
            "purpose": "Capture attention and frame the stakes of the war's impact on LNG, especially through Qatar and the Strait of Hormuz.",
            "must_include_facts": [
                "Reuters reports that the current conflict began with U.S.-Israeli strikes on Iran and has disrupted energy flows through the Gulf."
            ],
            "must_include_points": [
                "Open with the idea that this is not just a regional war; it is a global gas-market shock.",
                "Ask how much LNG supply disappears when Qatar is constrained."
            ],
            "transition_out": "So the real question is not only how severe the disruption is, but how long the world has to live with it.",
            "word_budget": 120
        },
        {
            "id": "TS2",
            "narrative_role": "core_insight",
            "purpose": "Explain why Qatar matters so much to the LNG market and why this disruption is hard to replace.",
            "must_include_facts": [
                # "QatarEnergy LNG operates 14 LNG trains with total annual production capacity of 77 million tonnes.",
                # "Qatar is one of the world's top LNG exporters and supplied nearly 20% of global LNG exports in 2024.",
                # "Qatar's LNG is sold largely through long-term contracts, with major demand centers in Asia and Europe."
                           ],
            "must_include_points": [
                "Explain that Qatar matters because of scale, reliability, and concentration: so much supply comes from one system at Ras Laffan.",
                "Show that the problem is not only production; it is also shipping access through Hormuz."
            ],
            "transition_out": "And once you understand how concentrated this system is, the next question becomes: what does the shock look like on the ground for buyers?",
            "word_budget": 220
        },
        {
            "id": "TS3",
            "narrative_role": "evidence_and_examples",
            "purpose": "Show how the disruption spreads through prices, contracts, trade flows, and buyer behavior across Asia and Europe.",
            "must_include_facts": [
                "Reuters reported that Asia and Europe are the regions most exposed to LNG disruption from the Iran conflict.",
                "Japanese buyer JERA said it was seeking additional LNG purchases to hedge against worsening Middle East risk.",
                "Shell declared force majeure to clients for LNG cargoes purchased from QatarEnergy after the shutdown.",
                "Reuters reported that cargoes originally intended for Europe were being redirected toward Asia as buyers scrambled for supply."
            ],
            "must_include_points": [
                # "Explain the first-order impact: prices rise and buyers rush to secure replacement cargoes.",
                # "Explain the second-order impact: trade flows re-route, Europe competes harder with Asia, and contract performance becomes strained.",
                # "Use JERA as an example of how utilities respond by sourcing backup cargoes and considering demand-side measures.",
                # "Use Shell's force majeure as an example of how disruption moves from geopolitics into commercial contracts.",
                # "Show that storage can buy time, but not indefinitely if the outage lasts for weeks or months.",
                # "Explain that alternative supply from the U.S. and other exporters helps, but replacement is partial and slower than the lost Qatari volumes."
            ],
            "transition_out": "When these effects spread across contracts, shipping lanes, and power systems, this stops being a Qatar story and becomes a global resilience test.",
            "word_budget": 280
        },
        {
            "id": "TS4",
            "narrative_role": "implication_and_close",
            "purpose": "End with the big lesson: LNG security now depends on resilience, diversification, and the ability to absorb shocks from concentrated supply routes.",
            "must_include_facts": [
                "Qatari officials have said that even if the conflict ended immediately, normal LNG deliveries could still take weeks or months"             ],
            "must_include_points": [
                "Argue that the real lesson is concentration risk: too much supply depends on too few facilities and one chokepoint.",
                "Say that resilience must come from diversified suppliers, stronger storage, more flexible contracts, and better emergency planning.",
                "Acknowledge that extra LNG capacity coming later this decade may ease pressure, but it does not solve today's vulnerability.",
                "Close with the idea that in energy, reliability is not just about reserves in the ground; it is about routes, redundancy, and recovery speed."
            ],
            "transition_out": None,
            "word_budget": 220
        }
    ]
}


# # **Schema**

# In[8]:


# schema

class WeakClaim(BaseModel):
    section_id: str
    field_name: str
    claim_type: Literal["fact", "point"]
    original_text: str
    reason: str
    search_queries: List[str] = Field(default_factory=list)


class ContentSectionPlan(BaseModel):
    section_id: str
    weak_claims: List[WeakClaim] = Field(default_factory=list)


class ContentBlueprint(BaseModel):
    section_plans: List[ContentSectionPlan]
    content_feedback: str


class EvidenceCandidate(BaseModel):
    snippet: str
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    published_date: Optional[str] = None
    tavily_score: float = 0.0
    relevance_score: float = 0.0
    usefulness_score: float = 0.0
    combined_score: float = 0.0
    feedback: Optional[str] = None


class ResearchItem(BaseModel):
    section_id: str
    field_name: str
    claim_type: Literal["fact", "point"]
    original_text: str
    query: str
    top_evidence: List[EvidenceCandidate] = Field(default_factory=list)


class ResearchBlueprint(BaseModel):
    research_results: List[ResearchItem]
    research_feedback: str


class Citation(BaseModel):
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    published_date: Optional[str] = None
    query: Optional[str] = None


class FactCitationMap(BaseModel):
    text: str
    citations: List[Citation] = Field(default_factory=list)
    added_by_grounding: bool = False


class PointCitationMap(BaseModel):
    text: str
    citations: List[Citation] = Field(default_factory=list)
    added_by_grounding: bool = False


class HookSchema(BaseModel):
    type: str
    description: str


class TedSectionGrounded(BaseModel):
    id: str
    narrative_role: str
    purpose: str
    must_include_facts: List[str]
    must_include_points: List[str]
    transition_out: Optional[str] = None
    word_budget: int

    fact_citations: List[FactCitationMap] = Field(default_factory=list)
    point_citations: List[PointCitationMap] = Field(default_factory=list)


class FinalOutputGrounded(BaseModel):
    hook: HookSchema
    big_idea: str
    ted_sections: List[TedSectionGrounded]


class GroundingBlueprint(BaseModel):
    grounding_feedback: str
    needs_retry: bool
    retry_reason: str
    final_output: FinalOutputGrounded

class State(TypedDict, total=False):
    user_input: Dict[str, Any]
    config: Dict[str, Any]
    graph_state: str
    retry_count: int

    content_check: Dict[str, Any]
    content_results: List[Dict[str, Any]]
    content_tasks: List[Dict[str, Any]]
    content_approved: bool
    content_attempts: int
    content_feedback: str

    research_check: Dict[str, Any]
    research_results: List[Dict[str, Any]]
    research_approved: bool
    research_attempts: int
    research_feedback: str

    grounding_check: Dict[str, Any]
    grounding_results: Dict[str, Any]
    grounding_approved: bool
    grounding_attempts: int
    grounding_feedback: str

    needs_retry: bool
    retry_reason: str
    final_output: Dict[str, Any]

    needs_retry: bool
    retry_reason: str

    final_output: FinalOutputGrounded | Dict[str, Any]


# # **- search engine**
# # **- LLM links**

# In[10]:


# linking up search engine
def build_tavily() -> TavilyClient:
    return TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# LLM links
content_llm = llm.with_structured_output(ContentBlueprint)
grounding_llm = llm.with_structured_output(GroundingBlueprint)
research_llm = llm


# In[11]:


# helpers

def get_sections(doc: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    sections = doc.get(config["sections_path"], [])
    if not isinstance(sections, list):
        return []
    return [s for s in sections if isinstance(s, dict)]


def get_section_id(section: Dict[str, Any], config: Dict[str, Any], fallback_idx: int) -> str:
    key = config.get("section_id_field", "id")
    value = section.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return f"section_{fallback_idx}"


def get_claim_field_specs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    return config.get("fact_fields", []) + config.get("point_fields", [])


def get_field_items(section: Dict[str, Any], field_name: str) -> List[str]:
    raw = section.get(field_name, [])
    if isinstance(raw, list):
        return [x.strip() for x in raw if isinstance(x, str) and x.strip()]
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    return []


def set_field_items(section: Dict[str, Any], field_name: str, items: List[str]) -> None:
    section[field_name] = [x.strip() for x in items if isinstance(x, str) and x.strip()]


def safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        return None


def dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        norm = " ".join(item.strip().lower().split())
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(item.strip())
    return out


def attach_citation(snippet: str, title: Optional[str], url: Optional[str]) -> str:
    if title and url:
        return f"{snippet} [Source: {title} | {url}]"
    if title:
        return f"{snippet} [Source: {title}]"
    if url:
        return f"{snippet} [Source: {url}]"
    return snippet


def count_query_shortfalls(user_input: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    sections = get_sections(user_input, config)

    for idx, sec in enumerate(sections, start=1):
        sid = get_section_id(sec, config, idx)
        for field_spec in get_claim_field_specs(config):
            field_name = field_spec["name"]
            claim_type = field_spec["type"]
            min_items = int(field_spec["min_items"])
            items = get_field_items(sec, field_name)
            if len(items) < min_items:
                missing = min_items - len(items)
                for n in range(missing):
                    tasks.append({
                        "section_id": sid,
                        "field_name": field_name,
                        "claim_type": claim_type,
                        "original_text": "Missing slot",
                        "reason": f"Field has fewer than {min_items} items.",
                        "search_queries": []
                    })
    return tasks

def truncate_text(text: str, max_len: int = 180) -> str:
    if not text:
        return ""
    text = str(text).replace("\n", " ").strip()
    return text if len(text) <= max_len else text[:max_len] + "..."

def run_tavily_search(client, query, config, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Tavily attempt {attempt}/{max_retries}: {query}")
            response = client.search(
                query=query,
                topic="general",
                max_results=config.get("top_k_tavily_results", 3),
                search_depth="advanced",
                include_answer=False,
                include_raw_content=False,
            )
            return response
        except Exception:
            print("Tavily error:")
            print(traceback.format_exc())

            if attempt < max_retries:
                sleep_time = 2 * attempt
                print(f"Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                print("Tavily failed after all retries.")


def build_initial_state():
  return {
          "user_input": ted_agent_json,
          "config": GENERIC_JSON_CONFIG,
          "graph_state": "start",
          "retry_count": 0,
          "content_tasks": [],
          "content_results": [],
          "research_results": [],
          "verbose": False,

      }

def strip_citations(final_output):
    import copy

    clean_output = copy.deepcopy(final_output)

    for section in clean_output.get("ted_sections", []):
        section.pop("fact_citations", None)
        section.pop("point_citations", None)

    return clean_output


# # **Content Agent**

# In[13]:


# content agent

content_llm = llm.with_structured_output(ContentBlueprint)

def Content_Agent(state: State) -> State:
    user_input = state["user_input"]
    print("user_input", user_input)
    config = state["config"]
    print("config", config)
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
{json.dumps(user_input, indent=2)}

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
            "graph_state": state["graph_state"],
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
            "graph_state": state["graph_state"],
        }


# # **CHECKS**

# In[15]:


# # check

# state = {
#     "user_input": ted_agent_json,
#     "config": GENERIC_JSON_CONFIG,
#     "graph_state": "start",
#     "retry_count": 0,
# }

# state = Content_Agent(state)

# print("CONTENT APPROVED:", state.get("content_approved"))
# print("CONTENT TASKS COUNT:", len(state.get("content_tasks", [])))


# # **Research Agent**

# In[17]:


# RESEARCH AGENT

# Note: Cannot fully replace this with with_structured_output because Tavily returns raw data not generated by LLM

def llm_rank_evidence(
    original_text: str,
    claim_type: str,
    query: str,
    tavily_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    ranking_prompt = f"""
You are an evidence ranking agent. Your task is to select the most relevant and usable evidence to strengthen a weak or missing claim.

Definitions:
- relevance_score (0–1): How directly the result addresses the claim/query.
- usefulness_score (0–1): How easily the result can be used in the final output (specific, clear, factual, well-structured).
- combined_score (0–1): Overall quality. Must reflect BOTH relevance and usefulness (not an average—prioritise strong evidence).

Instructions:
1. Review the claim, claim type, query, and all Tavily results.
2. Score EACH result using the three metrics.
3. Rank results by combined_score (highest first).
4. Select ONLY the top 3 results.
5. For facts, prefer evidence with concrete specifics, numbers, dates, named entities.
6. For points, prefer evidence that sharpens the analytical point.
7. Follow the output format strictly.

Original text:
{original_text}

Claim type:
{claim_type}

Query:
{query}

Raw Tavily results:
{json.dumps(tavily_results, indent=2)}

Output format:
{{
  "top_evidence": [
    {{
      "snippet": "<best usable snippet>",
      "source_title": "<title or null>",
      "source_url": "<url or null>",
      "published_date": "<date or null>",
      "tavily_score": 0.0,
      "relevance_score": 0.0,
      "usefulness_score": 0.0,
      "combined_score": 0.0,
      "feedback": "<optional note>"
    }}
  ]
}}
"""

    result = research_llm.invoke(ranking_prompt)

    print("=== llm_rank_evidence raw result ===")
    print(result)
    print("=== llm_rank_evidence result.content ===")
    print(getattr(result, "content", None))

    raw_content = getattr(result, "content", "")

    if isinstance(raw_content, str):
        content_text = raw_content
    elif isinstance(raw_content, list):
        text_parts = []
        for part in raw_content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        content_text = "\n".join(text_parts).strip()
    else:
        content_text = str(raw_content)

    print("=== llm_rank_evidence content_text ===")
    print(content_text)

    parsed = safe_json_loads(content_text)

    print("=== llm_rank_evidence parsed ===")
    print(parsed)

    if parsed and isinstance(parsed.get("top_evidence"), list):
        cleaned = []
        for item in parsed["top_evidence"][:3]:
            try:
                cleaned.append(EvidenceCandidate.model_validate(item).model_dump())
            except Exception as e:
                print("Validation error:", e)
                continue
        if cleaned:
            return cleaned

    fallback = []
    sorted_results = sorted(
        tavily_results,
        key=lambda x: float(x.get("score", 0.0) or 0.0),
        reverse=True,
    )[:3]

    for item in sorted_results:
        snippet = truncate_text((item.get("content") or "").strip(), 500)
        if not snippet:
            continue
        score = float(item.get("score", 0.0) or 0.0)
        fallback.append({
            "snippet": snippet,
            "source_title": item.get("title"),
            "source_url": item.get("url"),
            "published_date": item.get("published_date"),
            "tavily_score": score,
            "relevance_score": score,
            "usefulness_score": score,
            "combined_score": score,
            "feedback": "Fallback ranking used."
        })

    return fallback


def Research_Agent(state: State) -> State:
    import time
    import traceback

    user_input = state["user_input"]
    config = state["config"]
    attempts = state.get("research_attempts", 0)
    content_tasks = state.get("content_tasks", [])

    client = tavily_client
    research_results: List[Dict[str, Any]] = []

    print("===== RESEARCH AGENT START =====")
    print("state keys:", list(state.keys()))
    print(f"content_tasks count = {len(content_tasks)}")

    # for task in content_tasks[:1]:   # for debugging
    for task in content_tasks:
        print("\nRESEARCH task:")
        print({
            "section_id": task.get("section_id"),
            "field_name": task.get("field_name"),
            "claim_type": task.get("claim_type"),
            "original_text": truncate_text(task.get("original_text", ""), 120),
        })

        queries = task.get("search_queries", [])
        if not queries:
            fallback_query = f'{task.get("section_id", "")} {task.get("field_name", "")} {task.get("claim_type", "")} {task.get("reason", "")}'
            queries = [fallback_query]

        # for query in queries[:1]:   # for debugging
        for query in queries:
            print(f"Running Tavily query: {query}")

            response = run_tavily_search(client, query, config)
            if response is None:
                research_results.append({
                    "section_id": task.get("section_id"),
                    "field_name": task.get("field_name"),
                    "claim_type": task.get("claim_type"),
                    "original_text": task.get("original_text"),
                    "query": query,
                    "top_evidence": [],
                    "feedback": "Tavily search failed after retries."
                })
                continue

            try:
                raw_results = response.get("results", [])
                print("TAVILY_raw_results", raw_results)
                print(f"Tavily raw_results count: {len(raw_results)}")

                ranked = llm_rank_evidence(
                    original_text=task["original_text"],
                    claim_type=task["claim_type"],
                    query=query,
                    tavily_results=raw_results,
                )

                research_results.append({
                    "section_id": task["section_id"],
                    "field_name": task["field_name"],
                    "claim_type": task["claim_type"],
                    "original_text": task["original_text"],
                    "query": query,
                    "top_evidence": ranked,
                })

                time.sleep(1)

            except Exception:
                print("Ranking error:")
                print(traceback.format_exc())

                research_results.append({
                    "section_id": task.get("section_id"),
                    "field_name": task.get("field_name"),
                    "claim_type": task.get("claim_type"),
                    "original_text": task.get("original_text"),
                    "query": query,
                    "top_evidence": [],
                    "feedback": "Ranking/post-processing failed."
                })

    print("\nRESEARCH SUMMARY")
    for i, item in enumerate(research_results):
        print(f"\n[{i}] section={item.get('section_id')} | query={item.get('query')}")
        print(f"top_evidence_count={len(item.get('top_evidence', []))}")
        for j, ev in enumerate(item.get("top_evidence", [])[:3]):
            print(f"  evidence {j+1}: {ev.get('source_title')} | score={ev.get('combined_score')}")
            print(f"    snippet: {truncate_text(ev.get('snippet', ''), 180)}")

    research_feedback = f"Completed research for {len(research_results)} query runs."

    return {
        "research_check": {
            "research_results": research_results,
            "research_feedback": research_feedback,
        },
        "research_results": research_results,
        "research_approved": True,
        "research_attempts": attempts + 1,
        "research_feedback": research_feedback,
        "user_input": user_input,
        "graph_state": state["graph_state"],
        "config": config,
        "content_tasks": content_tasks,
        "content_results": state.get("content_results", []),
        "retry_count": state.get("retry_count", 0),
    }


# # **Grounding Agent**

# In[19]:


# grounding agent


def Grounding_Agent(state: State) -> State:
    user_input = state["user_input"]
    content_results = state.get("content_results", [])
    research_results = state.get("research_results", [])
    config = state.get("config", {})
    retry_count = state.get("retry_count", 0)

    print("\n===== GROUNDING AGENT START =====")
    print("state keys:", list(state.keys()))
    print("research_results_count:", len(research_results))
    print("content_results_count:", len(content_results))

    prompt = f"""
You are a Grounding Agent.

Your role:
- Preserve the original JSON format exactly for:
  - hook
  - big_idea
  - ted_sections
  - must_include_facts as List[str]
  - must_include_points as List[str]
- Do NOT convert must_include_facts or must_include_points into object lists.
- Enrich the outline conservatively using the research evidence.
- Remove weak, duplicate, or unsupported facts/points.
- Append newly supported facts/points into the existing string lists.
- Add parallel citation fields:
  - fact_citations
  - point_citations
- Each item in fact_citations / point_citations must include:
  - text
  - citations
  - added_by_grounding
- text must exactly match the corresponding fact/point string in must_include_facts or must_include_points.
- Do not invent unsupported claims.
- Keep the output outline-level only.



Original user JSON:
{json.dumps(user_input, indent=2)}

Content planning results:
{json.dumps(content_results, indent=2)}

Research results:
{json.dumps(research_results, indent=2)}

Return structured output only.
"""

    try:
        result: GroundingBlueprint = grounding_llm.invoke(prompt)

        print("GROUNDING AGENT raw result:")
        print(result)
        print("GROUNDING final_output:")
        print(json.dumps(result.final_output.model_dump(), indent=2, default=str))
        print("===== GROUNDING AGENT END =====")

        return {
            "grounding_check": result.model_dump(),
            "grounding_results": result.model_dump(),
            "grounding_approved": True,
            "grounding_feedback": result.grounding_feedback,
            "needs_retry": result.needs_retry,
            "retry_reason": result.retry_reason,
            "final_output": result.final_output.model_dump(),
            "research_results": research_results,
            "content_results": content_results,
            "user_input": user_input,
            "graph_state": state["graph_state"],
            "config": config,
            "retry_count": retry_count,
        }

    except Exception as e:
        print("GROUNDING AGENT ERROR:")
        print(traceback.format_exc())
        print("===== GROUNDING AGENT END (ERROR) =====")

        return {
            "grounding_approved": False,
            "grounding_feedback": str(e),
            "needs_retry": False,
            "retry_reason": str(e),
            "final_output": {},
            "research_results": research_results,
            "content_results": content_results,
            "user_input": user_input,
            "graph_state": state["graph_state"],
            "config": config,
            "retry_count": retry_count,
        }

# conditional routing for retry

def route_after_grounding(state: State) -> str:
    needs_retry = state.get("needs_retry", False)
    retry_count = state.get("retry_count", 0)
    max_retry_rounds = state["config"].get("max_retry_rounds", 1)

    if needs_retry and retry_count <= max_retry_rounds:
        return "retry"
    return "end"


# # **# checks**  [NOT NEED TO INCLUDE]
# 
# **Testing for citations attachments, no duplicates, added claims cited, appending of new information**

# In[21]:


# def build_initial_state():
#     return {
#         "user_input": ted_agent_json,
#         "config": GENERIC_JSON_CONFIG,
#         "graph_state": "start",
#         "retry_count": 0,
#         "content_tasks": [],
#         "content_results": [],
#         "research_results": [],
#     }


# In[22]:


# def check_citation_shape(grounding_state):
#     final_output = grounding_state.get("final_output", {})

#     for section in final_output.get("ted_sections", []):
#         print(f"\nSECTION {section['id']}")

#         print("must_include_facts_count:", len(section.get("must_include_facts", [])))
#         print("fact_citations_count:", len(section.get("fact_citations", [])))

#         for item in section.get("fact_citations", []):
#             print("FACT TEXT:", item.get("text"))
#             print("  added_by_grounding:", item.get("added_by_grounding"))
#             print("  citations_count:", len(item.get("citations", [])))

#         print("must_include_points_count:", len(section.get("must_include_points", [])))
#         print("point_citations_count:", len(section.get("point_citations", [])))

#         for item in section.get("point_citations", []):
#             print("POINT TEXT:", item.get("text"))
#             print("  added_by_grounding:", item.get("added_by_grounding"))
#             print("  citations_count:", len(item.get("citations", [])))


# In[23]:


# def check_duplicates(final_output):
#     for section in final_output.get("ted_sections", []):
#         sid = section.get("id")

#         facts = section.get("must_include_facts", [])
#         points = section.get("must_include_points", [])

#         fact_dupes = len(facts) - len(set(facts))
#         point_dupes = len(points) - len(set(points))

#         print(f"SECTION {sid}: fact_dupes={fact_dupes}, point_dupes={point_dupes}")


# In[24]:


# def check_added_claims_have_citations(final_output, original_json):
#     orig_sections = {s["id"]: s for s in original_json.get("ted_sections", [])}
#     problems = []

#     for section in final_output.get("ted_sections", []):
#         sid = section.get("id")
#         orig = orig_sections.get(sid, {})

#         orig_facts = set(orig.get("must_include_facts", []))
#         orig_points = set(orig.get("must_include_points", []))

#         fin_facts = section.get("must_include_facts", [])
#         fin_points = section.get("must_include_points", [])

#         fact_citation_map = {
#             item.get("text"): item for item in section.get("fact_citations", [])
#         }
#         point_citation_map = {
#             item.get("text"): item for item in section.get("point_citations", [])
#         }

#         for fact in fin_facts:
#             if fact not in orig_facts:
#                 item = fact_citation_map.get(fact)
#                 if not item or not item.get("citations"):
#                     problems.append((sid, "fact", fact))

#         for point in fin_points:
#             if point not in orig_points:
#                 item = point_citation_map.get(point)
#                 if not item or not item.get("citations"):
#                     problems.append((sid, "point", point))

#     if not problems:
#         print("PASS: all added claims have citations")
#     else:
#         print("FAIL: some added claims are missing citations")
#         for p in problems:
#             print(p)


# In[25]:


# def compare_original_vs_final(original_json, final_output):
#     orig_sections = {s["id"]: s for s in original_json.get("ted_sections", [])}
#     final_sections = {s["id"]: s for s in final_output.get("ted_sections", [])}

#     for sid in final_sections:
#         print(f"\nSECTION {sid}")

#         orig = orig_sections.get(sid, {})
#         fin = final_sections.get(sid, {})

#         orig_facts = orig.get("must_include_facts", [])
#         fin_facts = fin.get("must_include_facts", [])

#         orig_points = orig.get("must_include_points", [])
#         fin_points = fin.get("must_include_points", [])

#         added_facts = [x for x in fin_facts if x not in orig_facts]
#         added_points = [x for x in fin_points if x not in orig_points]

#         print("original facts:", len(orig_facts))
#         print("final facts:", len(fin_facts))
#         print("added facts:", added_facts)

#         print("original points:", len(orig_points))
#         print("final points:", len(fin_points))
#         print("added points:", added_points)


# In[26]:


# state = build_initial_state()

# state = Content_Agent(state)
# state = Research_Agent(state)
# state = Grounding_Agent(state)

# print("\n=== BASIC STATUS ===")
# print("grounding_approved:", state.get("grounding_approved"))
# print("needs_retry:", state.get("needs_retry"))
# print("has_final_output:", bool(state.get("final_output")))

# print("\n=== RESEARCH COVERAGE ===")
# coverage = {}
# for item in state.get("research_results", []):
#     sid = item.get("section_id")
#     coverage[sid] = coverage.get(sid, 0) + 1
# print(coverage)

# print("\n=== DUPLICATES ===")
# check_duplicates(state["final_output"])

# print("\n=== APPEND CHECK ===")
# compare_original_vs_final(state["user_input"], state["final_output"])

# print("\n=== CITATION SHAPE ===")
# check_citation_shape(state)

# print("\n=== ADDED CLAIMS MUST HAVE CITATIONS ===")
# check_added_claims_have_citations(state["final_output"], state["user_input"])


# # **LangGraph**

# In[28]:


def build_graph():
    builder = StateGraph(State)

    builder.add_node("content_agent", Content_Agent)
    builder.add_node("research_agent", Research_Agent)
    builder.add_node("grounding_agent", Grounding_Agent)

    builder.add_edge(START, "content_agent")
    builder.add_edge("content_agent", "research_agent")
    builder.add_edge("research_agent", "grounding_agent")

    builder.add_conditional_edges(
        "grounding_agent",
        route_after_grounding,
        {
            "retry": "content_agent",
            "end": END,
        },
    )

    return builder.compile()


# In[29]:


try:
    from IPython.display import Image, display

    graph = build_graph()
    png_data = graph.get_graph().draw_mermaid_png()
    display(Image(png_data))

except Exception as e:
    print("Graph rendering failed:")
    print(type(e).__name__, e)


# # **# Check [No need to include]**
# 
# for debugging purposes

# In[31]:


# # debugGERS!!!

# def build_initial_state() -> State:
#     return {
#         "user_input": ted_agent_json,
#         "config": GENERIC_JSON_CONFIG,
#         "graph_state": "start",
#         "retry_count": 0,
#     }


# def test_content_agent():
#     state = build_initial_state()

#     print("===== TEST CONTENT AGENT: INPUT =====")
#     print(json.dumps(state, indent=2, default=str))

#     result = Content_Agent(state)

#     print("\n===== TEST CONTENT AGENT: OUTPUT =====")
#     print(json.dumps(result, indent=2, default=str))
#     return result


# def test_research_agent():
#     content_state = Content_Agent(build_initial_state())

#     print("\n===== TEST RESEARCH AGENT: INPUT =====")
#     print(json.dumps(content_state, indent=2, default=str))

#     result = Research_Agent(content_state)

#     print("\n===== TEST RESEARCH AGENT: OUTPUT =====")
#     print(json.dumps(result, indent=2, default=str))
#     return result


# def test_grounding_agent():
#     content_state = Content_Agent(build_initial_state())
#     research_state = Research_Agent(content_state)

#     print("\n===== TEST GROUNDING AGENT: INPUT =====")
#     print(json.dumps(research_state, indent=2, default=str))

#     result = Grounding_Agent(research_state)

#     print("\n===== TEST GROUNDING AGENT: OUTPUT =====")
#     print(json.dumps(result, indent=2, default=str))
#     return result


# # **# MAIN()**

# In[ ]:


def main():
    graph = build_graph()
    initial_state = build_initial_state()

    print("===== INITIAL STATE =====")
    print(json.dumps(initial_state, indent=2, default=str))

    result = graph.invoke(initial_state)

    print("\n===== FINAL STATE =====")
    print(json.dumps(result, indent=2, default=str))

    # after grounding agent
    final_output = result.get("final_output", {})

    print("\n=== FINAL OUTPUT (WITH CITATIONS) ===")
    print(json.dumps(final_output, indent=2))

    clean_output = strip_citations(final_output)

    print("\n=== FINAL OUTPUT (CLEAN - NO CITATIONS) ===")
    print(json.dumps(clean_output, indent=2))


if __name__ == "__main__":
    main()

