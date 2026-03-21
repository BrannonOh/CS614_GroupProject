# Install packages
from pathlib import Path
import json
import os
from pprint import pprint 

from langchain_google_genai import ChatGoogleGenerativeAI

# Import typing helpers for type hints 
from typing import Any, Dict, List, Literal, Optional, TypedDict

# BaseModel is the core class used to define structured data models 
from pydantic import BaseModel, ValidationError, Field

# Import LangGraph state
from graph.state import SpeechScriptState

# Import schemas
from schemas.content_blueprint import ContentBlueprint

# Load API Key
import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize LLM
# Ensure it only outputs JSON in ContentBlueprint schema (for use by Script Writing Baseline Agent downstream)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)
content_llm = llm.with_structured_output(ContentBlueprint)

def build_content_prompt(ted_blueprint):
    prompt = f"""
You are revising a content_outline to make its arguments stronger.

Revise every ted_section by improving its must_include_points and must_include_facts so they are more specific, concrete, and persuasive.

Rules:
- Keep structure unchanged
- Keep hook, big_idea, section ids, narrative_role, purpose, and transition_out unchanged
- Only modify must_include_points and must_include_facts
- Prefer rewriting weak claims over adding new ones
- Add new claims only if needed to complete the logic of the section
- Avoid redundancy and side topics

Return the full revised content_outline in valid JSON only.

content_outline:
{ted_blueprint.model_dump_json()}
"""
    return prompt

def Content_Agent(state: SpeechScriptState):
    """Beef up content inside content outline"""
    print("\n========CONTENT AGENT ========")
    ted_blueprint = state["ted_blueprint"] # This is a Pydantic object

    try:
        result = content_llm.invoke(build_content_prompt(ted_blueprint))
        dumped = result.model_dump(mode="json") # Convert Pydantic output into Dict
        print("Content Blueprint (Refined)")
        pprint(dumped)

        return {"content_blueprint": dumped}

    except Exception as e:
        print("CONTENT AGENT ERROR:")
        print(str(e))