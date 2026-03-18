# # Install Packages
import re
import json
import os
from pathlib import Path
from datetime import datetime

from pprint import pprint
from __future__ import annotations
from IPython.display import Image
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Import typing helpers for type hints 
from typing import TypedDict, Dict, List, Literal, Optional, Any

# BaseModel is the core class used to define structured data models 
from pydantic import BaseModel, Field, ConfigDict, model_validator, ValidationError

# Import schemas
from schemas.content_blueprint import ContentBlueprint
from schemas.style_profile import StyleProfileStructure
from schemas.reflection_blueprint import ReflectionBlueprint

# # Load API Key
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

# # Load Output from Previous Agent (Content Outline)
# Simulate this by loading the mock data json
with open("mocks/mock_content_blueprint.json", "r") as f:
    content_outline = json.load(f)

pprint(content_outline)

# ## (Optional) Validate Schema to ensure previous output is valid for use
# To discuss: Actually I feel that it is better to assume that the previous agent has already validated its output to be correct before passing it down, so that we dont need to do double validation here. 
# * If the previous agent validate its own output and it's wrong, it can repeatedly correct itself
# * If the downstream validate for the upstream then in between EACH upstream and downstream we have to create maker-checker loops, which doesnt make sense.
# * Proposed approach: Each agent validate its own final output, before sending to downstream. Downstream agent takes it that output is correct. 

# if success, outputs a structured Python object with validated, typed data
try: 
    content_instance = ContentBlueprint.model_validate(content_outline)
except ValidationError as e: 
    validation_error = e
    pprint(validation_error.errors())

# # Define SpeechScript State
# This state same as the one in our repo, so that my development is aligned immediately (no double work). I only included the state fields that I am working with.

# Import schemas for the State (these will be part of state.py but for convenience sake load it here)
from schemas.content_blueprint import ContentBlueprint

class SpeechScriptState(TypedDict):
    # Other fields...
    content_blueprint: ContentBlueprint

    chunk_style_notes: List[Dict[str, Any]] # Newly added field so Style Extraction Agent can pass info to Style Aggregation Agent. 
    style_profile: Dict[str, Any] # Newly added field so Style Aggregation Agent can pass info to Script Writing Agent. Dict of str format as it is not critical to adhere to JSON structure for this field
    stylistic_script: str 

    # Feedback fields...

    style_feedback: ReflectionBlueprint
    style_approved: bool
    style_reviews: int # Change name for clarity

# # Style Aggregation Agent
# This agent reads all the style notes generated per chunk, and synthesizes it into a single style profile.
style_agg_system_prompt = """
You are a style aggregation agent.

Your task is to synthesize multiple chunk-level style notes into one stable overall style profile for the full speech.

Guidelines:
- Identify patterns that recur across chunks.
- Keep only traits that are consistent, representative, and generalizable.
- Deduplicate overlapping or near-synonymous traits.
- Prefer broader canonical labels over overly specific variants when they mean nearly the same thing.
- Exclude one-off, weak, or contradictory traits unless they clearly support a dominant pattern.
- Preserve meaningful distinctions when two traits are related but not redundant.
- Do not refer to chunk numbers, ordering, or frequency counts explicitly.
- Treat the input as noisy evidence: infer the dominant style, not a union of all items.

Field-specific guidance:
1. "tone": Delivery and emotional quality of the voice.
2. "avoid": Language styles clearly NOT used by the speaker.
3. "lexical_preferences": Vocabulary and word-choice tendencies.
4. "syntax": Sentence structure habits.
5. "rhetorical_devices": Recurring rhetorical techniques.
6. "argument_structure": How arguments are typically developed.
7. "audience_relationship": How the speaker positions themselves relative to the audience.

Be conservative:
- include only the strongest traits
- avoid repeating the same idea in different words
"""

def build_style_agg_user_prompt(chunk_style_notes):
    return f"""
Aggregate the following chunk-level style notes into one stable style profile for the speech:

{chunk_style_notes}
"""

# Initialize the LLM 
# Attach the Pydantic schema (structured outputs) - Converts Pydantic Schema into a JSON schema 
# Model is forced to produce JSON matching this schema, so no need to mention in the prompt
style_aggregation_llm = ChatOpenAI(
    model="gpt-4.1-mini", 
    temperature=0
).with_structured_output(StyleProfileStructure)

def Style_Aggregation_Agent(state: SpeechScriptState):
    """Analyse chunk_style_notes to derive a coherent description of the author's writing style"""
    print("\n========STYLE AGGREGATION AGENT ========")
    llm_reply = style_aggregation_llm.invoke([
        SystemMessage(content=style_agg_system_prompt),
        HumanMessage(content=build_style_agg_user_prompt(state["chunk_style_notes"]))
    ])
    dumped = llm_reply.model_dump(mode="json")
    print(f"style_profile: {dumped}")
    return {"style_profile": dumped}