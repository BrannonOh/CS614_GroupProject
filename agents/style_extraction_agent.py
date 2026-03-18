# %% [markdown]
# # Install Packages

# %%
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

# %%
# Import schemas
from schemas.content_blueprint import ContentBlueprint
from schemas.style_profile import StyleProfileStructure
from schemas.reflection_blueprint import ReflectionBlueprint

# %% [markdown]
# # Load API Key

# %%
import os
from dotenv import load_dotenv
load_dotenv()

# %%
api_key = os.getenv("OPENAI_API_KEY")

# %% [markdown]
# # Load Output from Previous Agent (Content Outline)

# %%
# Simulate this by loading the mock data json
with open("mocks/mock_content_blueprint.json", "r") as f:
    content_outline = json.load(f)

pprint(content_outline)

# %% [markdown]
# ## (Optional) Validate Schema to ensure previous output is valid for use
# To discuss: Actually I feel that it is better to assume that the previous agent has already validated its output to be correct before passing it down, so that we dont need to do double validation here. 
# * If the previous agent validate its own output and it's wrong, it can repeatedly correct itself
# * If the downstream validate for the upstream then in between EACH upstream and downstream we have to create maker-checker loops, which doesnt make sense.
# * Proposed approach: Each agent validate its own final output, before sending to downstream. Downstream agent takes it that output is correct. 

# %%
# if success, outputs a structured Python object with validated, typed data
try: 
    content_instance = ContentBlueprint.model_validate(content_outline)
except ValidationError as e: 
    validation_error = e
    pprint(validation_error.errors())

# %% [markdown]
# # Define SpeechScript State
# This state same as the one in our repo, so that my development is aligned immediately (no double work). I only included the state fields that I am working with.

# %%
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

# %% [markdown]
# # Overall Approach
# * agent 1: chunk docs and analyse rhetoric style per chunk
# * agent 2: read all rhetoric styles for all chunks and generalise to 1 style profile
# * agent 3: write the script based on the style profile
# 
# Justification
# * Better modularity: chunk analysis and style generalization are different tasks
# * separation makes debugging easier
# * Higher controllability: Can inspect per-chunk outputs before synthesis

# %% [markdown]
# # Create Style Extraction Agent
# 
# This agent works by 
# 1. loading the style samples (assume max 5 documents) and chunking them into shorter portions that the LLM can manage
# 2. Analyse each chunk to elucidate the author's style

# %% [markdown]
# ## Define Utility Functions

# %%
def load_txt_file(path: str) -> str:
    """
    Opens a txt file in UTF-8 encoding given a file path
    """
    return Path(path).read_text(encoding="utf-8")

# %%
def clean_pdf_copied_text(text: str) -> str:
    """
    Remove Title text
    Keep paragraph breaks (Denoted by 2 newlines), use that to split paragraphs
    Replace line breaks inside paragraphs (1 newline) with space " ".
    """
    # Replace newline formats across Windows and Mac into standard Linux format
    text = text.replace("\r\n", "\n").replace("\r", "\n") 

    # Remove first line if it starts with "Title:"
    text = re.sub(r"^\s*Title:.*\n+", "", text)
    
    # Split into paragraphs, based on at least 2 newlines (which may / may not have space in between)
    paragraphs = re.split(r"\n\s*\n+", text.strip())
    
    cleaned_paragraphs = []
    for p in paragraphs:
        p = re.sub(r"\n+", " ", p) # Replace 1 newline with space
        p = re.sub(r"\s+", " ", p).strip() # Remove multi-spacing
        if p:
            cleaned_paragraphs.append(p)
            
    # After cleaning, join back into complete document
    return "\n\n".join(cleaned_paragraphs)

# %%
def chunk_by_paragraphs(text: str, paras_per_chunk: int = 3) -> List[str]:
    """
    Groups speech into chunks of default 3 paragraphs each time
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []

    for i in range(0, len(paragraphs), paras_per_chunk):
        chunk = "\n\n".join(paragraphs[i:i + paras_per_chunk])
        chunks.append(chunk)

    return chunks

# %% [markdown]
# ## Analyse Style per Chunk
# 
# Design of the style profile is highly critical to the success of the user style incorporation. It needs to include lexical, discourse level patterns
# * Sentence behaviour
# * Argumentative habits
# * Relationship to audience
# * Also include negative constraints to tell model what to avoid

# %%
# No mention of returning JSON, will be done in with_structured_output()
style_extract_system_prompt = """
You are a style-extraction agent in a multi-agent speech generation pipeline.

Analyze speech excerpts and extract the author's WRITING STYLE only.
Do NOT summarize the topic or argument.

The goal is to produce a reusable style profile that another agent can use to generate new speeches in the same rhetorical style.

Output Rules
- Use short noun phrases only (no full sentences).
- Do NOT reference the speech topic.
- Include only patterns clearly supported by the excerpt.
- Prefer distinctive traits over generic ones.

Fields to extract
1. "tone": Delivery and emotional quality of the voice.
Examples: authoritative, conversational, combative, pragmatic, ironic.

2. "avoid": Language styles clearly NOT used by the speaker.
Examples: motivational slogans, corporate buzzwords, sentimental phrasing.

3. "lexical_preferences": Vocabulary and word-choice tendencies.
Examples: plainspoken vocabulary, concrete nouns, numerical comparisons, repeated key terms.

4. "syntax": Sentence structure habits.
Examples: short declarative sentences, abrupt pivots, sentence fragments, parenthetical insertions, parallel constructions.

5. "rhetorical_devices": Recurring rhetorical techniques.
Examples: rhetorical questions, contrast framing, anaphora, analogy, direct audience address.

6. "argument_structure": How arguments are typically developed.
Examples: blunt issue naming, example-driven reasoning, problem–consequence framing, escalation through concrete examples, anticipation of objections.

7. "audience_relationship": How the speaker positions themselves relative to the audience.
Examples: direct address, authoritative stance, confrontational challenge, instructive tone.

Constraints
- Each list: maximum 5 items.
- Rank items by importance.
- Avoid duplication across fields.
"""

# %%
# No mention of returning JSON, will be done in with_structured_output()
# Have to build a user_prompt function coz the {chunk} will be passed in dynamically at runtime
# If not user_prompt variable results in NameError as {chunk} is not defined yet.
def build_style_extract_user_prompt(chunk):
    return f"""
Analyze the following speech excerpt and extract the author's writing style.

Rules:
- Do NOT summarize the topic or argument.
- Extract reusable stylistic patterns only.
- Use short descriptive phrases.

Speech excerpt:
\"\"\"
{chunk}
\"\"\"
"""

# %%
# Initialize the LLM 
# Attach the Pydantic schema (structured outputs) - Converts Pydantic Schema into a JSON schema 
# Model is forced to produce JSON matching this schema, so no need to mention in the prompt
style_extraction_llm = ChatOpenAI(
    model="gpt-4.1-mini", 
    temperature=0
).with_structured_output(StyleProfileStructure)

# %%
def Style_Extraction_Agent(state: SpeechScriptState):
    """Chunk style samples, then ask the LLM to identify the style per chunk."""
    print("\n========STYLE EXTRACTION AGENT ========")
    # Assume user uploaded his style samples into data/samples folder and they are in .txt files
    # Load data
    style_samples_path = Path("data/samples")
    txt_files = list(style_samples_path.glob("*.txt"))
    raw_speeches = [load_txt_file(path) for path in txt_files]

    # Clean and chunk speeches
    cleaned_speeches = [clean_pdf_copied_text(speech) for speech in raw_speeches]
    
    chunks = []
    for speech in cleaned_speeches:
        chunks.extend(chunk_by_paragraphs(speech, paras_per_chunk=3))

    # Store chunks inside data/samples_chunks folder as .txt files for independent evaluation
    chunks_path = Path("data/samples_chunks")
    chunks_path.mkdir(parents=True, exist_ok=True)
    for i, chunk in enumerate(chunks):
        file_path = chunks_path / f"chunk_{i+1}.txt"
        file_path.write_text(chunk, encoding="utf-8")
    
    # Analyse style per chunk using LLM
    chunk_style_notes = []
    for i, chunk in enumerate(chunks, start=1):
        print(f"Extracting style from chunk {i}/{len(chunks)}...")
        llm_reply_chunk_style = style_extraction_llm.invoke([
            SystemMessage(content=style_extract_system_prompt),
            HumanMessage(content=build_style_extract_user_prompt(chunk))
        ])
        dumped = llm_reply_chunk_style.model_dump(mode="json")
        chunk_style_notes.append(dumped) # Convert Pydantic objects to JSON then store
        print(f"chunk {i}: {chunk}\n\nchunk_style: {dumped}")

    return {"chunk_style_notes": chunk_style_notes}
