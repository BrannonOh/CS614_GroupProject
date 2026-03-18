# Install Packages
import re
import json
import os
from pathlib import Path

from pprint import pprint
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Import typing helpers for type hints 
from typing import TypedDict, Dict, List, Literal, Optional, Any

# BaseModel is the core class used to define structured data models 
from pydantic import BaseModel, Field, ConfigDict, model_validator, ValidationError

# Import schemas
from schemas.style_profile import StyleProfileStructure

# Import LangGraph state
from graph.state import SpeechScriptState

# Load API Key
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

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