# Install Packages
import re
import json
import os
from pathlib import Path
from datetime import datetime

from pprint import pprint
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Import typing helpers for type hints 
from typing import TypedDict, Dict, List, Literal, Optional, Any

# BaseModel is the core class used to define structured data models 
from pydantic import BaseModel, Field, ConfigDict, model_validator, ValidationError

# Import LangGraph state
from graph.state import SpeechScriptState

# Load API Key
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Get project directory aka root folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Compared to enhanced flow, the baseline system prompt just translates the TED outline to speech
# No personalisation of voice using style_profile (this is not generated)
# There is no revision instructions too.
writer_system_prompt = """
You are a professional speechwriter.

Your task is to write a speech script using a ted_outline.

Your goal is to produce a natural speech that follows the above outline.

PRIORITY ORDER
1. Preserve all facts and key information from the ted_outline.
2. Follow the structure of the ted_outline.

GENERAL WRITING RULES
- Follow the order of sections in the ted_outline.
- Write in natural spoken language suitable for a speech.
- Do not invent new facts.

TED OUTLINE USAGE
- Hook: Use the hook description as guidance for the opening of the speech.
- Big Idea: Communicate the big_idea clearly early in the speech.

TED Sections
For each section in ted_sections:
- Use the narrative_role and purpose to guide the message of the section.
- Include all information from must_include_points. They may be rephrased but their meaning must not change.
- Include all facts listed in must_include_facts. They may be rephrased but their numbers must not change.
- Aim for approximately the specified word_budget (±15%).
- Use the transition_out sentence to move into the next section. Wording adjustments are acceptable.

OUTPUT
- Return only the final speech as natural prose.
- Do not output JSON, bullet explanations, commentary, or analysis.
"""

# The user prompt in the baseline flow just instructs the LLM to write the speech.
# No need for user prompt to vary depending on whether it is writing the speech for the first time, vs revising a draft.
def build_writer_user_prompt(ted_outline):
    prompt = f"""
Write a speech script using the TED outline below.

TED OUTLINE
{ted_outline}

Write the full speech.
"""
    return prompt

speech_writing_llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.5,
    top_p=0.9,
    frequency_penalty=0.3,
)

def Script_Writing_Agent(state: SpeechScriptState):
    """Generate a speech directly from the TED outline."""
    print("\n========SCRIPT WRITING AGENT ========")
    ted_outline = state.get("ted_blueprint")
    if ted_outline is None:
        raise ValueError("Missing 'ted_blueprint' in state before baseline script writing.")

    llm_script = speech_writing_llm.invoke([
        SystemMessage(content=writer_system_prompt),
        HumanMessage(
            content=build_writer_user_prompt(ted_outline=ted_outline)
        )
    ])
    speech_draft = llm_script.content.strip()
    
    # Store speech draft into data/speech_drafts folder in chronological order to keep track of each revision (for independent evaluation)
    # To differentiate outputted scripts from this baseline flow, the name of the txt file is called 'speech_draft_baseline_'
    draft_path = BASE_DIR / "data" / "speech_drafts"
    draft_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = draft_path / f"speech_draft_baseline_{timestamp}.txt"
    file_path.write_text(speech_draft, encoding="utf-8")
    
    print(f"Script Draft: {speech_draft}")
    return {"stylistic_script": speech_draft}
