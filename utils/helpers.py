# helpers

import json
import os
import time
import traceback
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, TypedDict

from pydantic import BaseModel, ValidationError, Field

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
          "user_input": ted_blueprint,
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
