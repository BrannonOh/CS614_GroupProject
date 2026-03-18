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
from schemas.content_blueprint import ContentBlueprint
from schemas.style_profile import StyleProfileStructure
from schemas.reflection_blueprint import ReflectionBlueprint

# Import LangGraph state
from graph.state import SpeechScriptState

# Load API Key
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Get project directory aka root folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Define Utility Functions
def load_txt_file(path: str) -> str:
    """
    Opens a txt file in UTF-8 encoding given a file path
    """
    return Path(path).read_text(encoding="utf-8")

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
Examples: blunt issue naming, example-driven reasoning, problem-consequence framing, escalation through concrete examples, anticipation of objections.

7. "audience_relationship": How the speaker positions themselves relative to the audience.
Examples: direct address, authoritative stance, confrontational challenge, instructive tone.

Constraints
- Each list: maximum 5 items.
- Rank items by importance.
- Avoid duplication across fields.
"""

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

style_extraction_llm = ChatOpenAI(
    model="gpt-4.1-mini", 
    temperature=0
).with_structured_output(StyleProfileStructure)

def Style_Extraction_Agent(state: SpeechScriptState):
    """Chunk style samples, then ask the LLM to identify the style per chunk."""
    print("\n========STYLE EXTRACTION AGENT ========")
    # Assume user uploaded his style samples into data/samples folder and they are in .txt files
    # Load data
    style_samples_path = BASE_DIR / "data" / "samples"
    txt_files = list(style_samples_path.glob("*.txt"))
    raw_speeches = [load_txt_file(path) for path in txt_files]

    # Clean and chunk speeches
    cleaned_speeches = [clean_pdf_copied_text(speech) for speech in raw_speeches]
    
    chunks = []
    for speech in cleaned_speeches:
        chunks.extend(chunk_by_paragraphs(speech, paras_per_chunk=3))

    # Store chunks inside data/samples_chunks folder as .txt files for independent evaluation
    chunks_path = BASE_DIR / "data" / "samples_chunks"
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
