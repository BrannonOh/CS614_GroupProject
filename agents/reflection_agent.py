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
from schemas.reflection_blueprint import ReflectionBlueprint

# Import LangGraph state
from graph.state import SpeechScriptState

# Load API Key
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

reflection_system_prompt = """
You are a Reflection Agent.

Your task is to compare a generated script against:
1) content_outline JSON
2) style_profile JSON

Return a sparse exception report that identifies only problems in the script.

Rules:
- Only report issues. Omit anything that is adequately covered.
- Mirror the input structure where possible so the writer can fix the script easily.
- Missing, weak, generic, misplaced, or contradictory content should be reported as issues.

Content checks:
- big_idea
- hook (type and description)
- each ted_section: purpose, narrative_role, must_include_facts, must_include_points, transition_out, word_budget
- Only include a ted_section if it contains an issue.
- Compute no. of words in ted_section and compare to word_budget. Report if it exceeds or is under the word_budget by 15%

Style checks:
- argument_structure
- audience_relationship
- avoid
- lexical_preferences
- rhetorical_devices
- syntax
- tone

Formatting rules:
- Return valid JSON only.
- Use the Pydantic structure: content_issues and style_issues.
- Omit fields with no issues.
- For checklist items (facts, points, style items), return objects with:
  { "item": "...", "issue": "..." }

Keep issue descriptions short and actionable.
"""

def build_reflection_user_prompt(content_outline, style_profile, stylistic_script):
    return f"""
Evaluate the script against the content_outline and style_profile.

Return a sparse exception report using the Pydantic schema.

Guidelines:
- Only include issues.
- Omit anything that is adequately covered.
- If there are no issues in a section, omit it.
- Always return both top-level fields: content_issues and style_issues.

content_outline:
{content_outline}

style_profile:
{style_profile}

script:
{stylistic_script}
"""

reflection_llm = ChatOpenAI(
    model="gpt-4.1-mini", 
    temperature=0
).with_structured_output(ReflectionBlueprint)

def Reflection_Agent(state: SpeechScriptState):
    """Check script output adherence to content outline and style profile"""
    print("\n========REFLECTION AGENT ========")
    llm_feedback = reflection_llm.invoke([
        SystemMessage(content=reflection_system_prompt),
        HumanMessage(
            content=build_reflection_user_prompt(
                content_outline=state["content_blueprint"], 
                style_profile=state["style_profile"],
                stylistic_script=state["stylistic_script"]
            )
        )
    ])
    dumped = llm_feedback.model_dump(mode="json")
    print("style_feedback:")
    pprint(dumped)
    return {
        "style_feedback": dumped,
        "style_reviews": state.get("style_reviews", 0) + 1 # Increment the Review Number after each review
    }