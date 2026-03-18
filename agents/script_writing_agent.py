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

# # Script Writing Agent
# This agent generates the text script from the `content_outline` JSON provided and `style_profile` JSON.

# **Prompt Design Considerations**  
# Focus is on rules that affect writing behaviour. Evaluation will be done by Reflection Agent later.
# 
# 1. Define priority so the model know what is most important when amending (following style vs outline, dropping facts to suit style etc)
# 2. Explain clearly how each field in the JSONs can be used, but still...
# 3. Allow controlled rewriting: It is acceptable to rephrase content provided in JSON to match style to prevent model from producing outline-like writing
# 4. In general style as a guidance, not constraint, so that it uses where appropriate.
# 5. Provide instructions in the event that `style_feedback` is provided

writer_system_prompt = """
You are a professional speechwriter.

Your task is to write or revise a speech script using:
1. content_outline
2. style_profile
3. optional style_feedback
4. optional previous_draft

Your goal is to produce a natural speech that follows the outline while sounding like the author's voice.

PRIORITY ORDER
1. Preserve all facts and key information from the content_outline.
2. Apply the writing style from style_profile.
3. Follow the structure of the content_outline.
4. If style_feedback is provided, fix all identified problems without introducing new facts.

GENERAL WRITING RULES
- Follow the order of sections in the content_outline.
- Write in natural spoken language suitable for a speech.
- You may rephrase outline content to match the author's voice.
- Do not invent new facts.
- Do not remove correct content unless a change is required to resolve a flagged issue.
- Prefer targeted revisions over unnecessary rewrites.

STYLE PROFILE USAGE
The style_profile describes how the author typically writes and argues. Use it to shape the voice of the speech.
- Tone: Maintain the emotional and delivery qualities listed in the tone field throughout the speech.
- Avoid: Do not use language styles listed in avoid.
- Lexical Preferences: Prefer the vocabulary tendencies listed in lexical_preferences.
- Syntax: Reflect the sentence patterns listed in syntax.
- Rhetorical Devices: Use the rhetorical_devices where appropriate.
- Argument Structure: Shape paragraphs according to argument_structure patterns.
- Audience Relationship: Maintain the speaker's stance toward the audience described in audience_relationship.
Apply the style consistently across the speech. Style should influence sentence rhythm, argument flow, and audience engagement — not just word choice.

CONTENT OUTLINE USAGE
- Hook: Use the hook description as guidance for the opening of the speech.
- Big Idea: Communicate the big_idea clearly early in the speech.

TED Sections
For each section in ted_sections:
- Use the narrative_role and purpose to guide the message of the section.
- Include all information from must_include_points. They may be rephrased but their meaning must not change.
- Include all facts listed in must_include_facts. They may be rephrased but their numbers must not change.
- Aim for approximately the specified word_budget (±15%).
- Use the transition_out sentence to move into the next section. Wording adjustments are acceptable.

REVISION RULES
If style_feedback is provided:
- Treat it as a diagnosis of issues in the previous draft.
- Revise the previous_draft, rather than starting over unless a full rewrite is truly necessary.
- Fix every valid issue identified in style_feedback.
- Preserve wording, structure, and passages that already work.
- If style_feedback conflicts with content_outline, follow content_outline.
- If style_feedback conflicts with style_profile, follow style_profile.
- Do not mention the feedback, diagnosis, or revision process in the output.

OUTPUT
- Return only the final speech as natural prose.
- Do not output JSON, bullet explanations, commentary, or analysis.
"""

# Helper functions to transform the Reflection Agent's JSON output into prose for the Script Writing Agent to digest.
# Helper function to use inside build_revision_brief()
# Reformats ItemIssue object from ReflectionAgent output
def format_item_issues(title, items):
    if not items:
        return ""
    lines = [f"{title}:"]
    for idx, issue in enumerate(items, 1):
        lines.append(f"  {idx}. Item: {issue["item"]}")
        lines.append(f"     Problem: {issue["issue"]}")
    return "\n".join(lines)

def build_revision_brief(feedback):
    sections = []

    # Content issues
    ci = feedback["content_issues"]

    if ci["hook"]:
        hook_lines = ["HOOK ISSUE:"]
        if ci["hook"]["type"]:
            hook_lines.append(f"Hook type issue: {ci["hook"]["type"]}.")
        if ci["hook"]["description"]:
            hook_lines.append(f"Hook description issue: {ci["hook"]["description"]}.")
        sections.append("\n".join(hook_lines))

    if ci["big_idea"]:
        sections.append("BIG IDEA ISSUE:\n- " + ci["big_idea"])

    if ci["ted_sections"]:
        ted_section_blocks = []
        for sec in ci["ted_sections"]:
            block = [f"TED SECTION ISSUE: section id = {sec["id"]}"]
            if sec["purpose"]:
                block.append(f"- Purpose issue: {sec["purpose"]}")
            if sec["narrative_role"]:
                block.append(f"- Narrative role issue: {sec["narrative_role"]}")
            if sec["transition_out"]:
                block.append(f"- Transition issue: {sec["transition_out"]}")
            if sec["word_budget"]:
                block.append(f"- Word budget issue: {sec["word_budget"]}")

            if sec["must_include_facts"]:
                block.append(format_item_issues("Must-include facts issues", sec["must_include_facts"]))
            if sec["must_include_points"]:
                block.append(format_item_issues("Must-include points issues", sec["must_include_points"]))

            ted_section_blocks.append("\n".join([b for b in block if b]))
        sections.append("\n\n".join(ted_section_blocks))

    # Style issues
    si = feedback["style_issues"]

    style_categories = [
        ("Argument structure issues", si["argument_structure"]),
        ("Audience relationship issues", si["audience_relationship"]),
        ("Avoid-list violations", si["avoid"]),
        ("Lexical preference issues", si["lexical_preferences"]),
        ("Rhetorical device issues", si["rhetorical_devices"]),
        ("Syntax issues", si["syntax"]),
        ("Tone issues", si["tone"]),
    ]

    for title, items in style_categories:
        formatted = format_item_issues(title, items)
        if formatted:
            sections.append(formatted)

    if not sections:
        return "No issues were identified."

    return "\n\n".join(sections)

# The user prompt varies depending on whether it is writing the speech for the first time, vs revising a draft.
def build_writer_user_prompt(
    content_outline,
    style_profile,
    previous_draft,
    style_feedback,
    style_reviews
):
    prompt = f"""
Write a speech script using the following inputs.

CONTENT OUTLINE
{content_outline}

STYLE PROFILE
{style_profile}
"""

    # Need revision if the style_feedback object has stuff inside
    is_revision = style_feedback is not None and (bool(style_feedback.get("content_issues")) or bool(style_feedback.get("style_issues")))
    print(f"is_revision status: {is_revision}")
    
    if is_revision and previous_draft:
        revision_brief = build_revision_brief(style_feedback)
        print(f"revision brief: {revision_brief}")
        prompt += f"""

PREVIOUS DRAFT
{previous_draft}

REVISION FEEDBACK
{revision_brief}

Revision instructions
- Revise the PREVIOUS DRAFT to resolve all issues listed in REVISION FEEDBACK.
- Preserve all correct facts, strong passages, and structure unless change is needed.
- Keep the speech natural and spoken.
- Do not invent new facts.
- Maintain alignment with the content outline and style profile.
"""
    else:
        prompt += """

Instructions
- Write the first full draft of the speech.
- Follow the structure defined in the content_outline.
- Include all facts and key points.
- Use the style_profile to shape the voice of the speech.
- The speech should sound natural and spoken.
- Stay close to the word budgets for each section.
- Use the transition_out sentence as guidance to move into the next section.
"""

    prompt += """

Write the full speech.
"""
    return prompt

# For script writing, some creativity is involved. This LLM will have more parameters to play around with.
# * temperature: Allow more creativity in word choice
# * top_p: Large leeway with probability 0.9
# * frequency_penalty: Reduces repetition so that speeches are not boring
# * max_tokens: Have a cap in case the LLM keeps writing non-stop 

# Initialize the LLM 
speech_writing_llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.5,
    top_p=0.9,
    frequency_penalty=0.3,
)

def Script_Writing_Agent(state: SpeechScriptState):
    """Generate a speech from an outline while preserving an author's voice OR revise an existing draft"""
    print("\n========SCRIPT WRITING AGENT ========")
    llm_script = speech_writing_llm.invoke([
        SystemMessage(content=writer_system_prompt),
        HumanMessage(
            content=build_writer_user_prompt(
                content_outline=state["content_blueprint"], 
                style_profile=state["style_profile"],
                previous_draft=state.get("stylistic_script"),
                style_feedback=state.get("style_feedback"),
                style_reviews=state.get("style_reviews", 0)
            )
        )
    ])
    speech_draft = llm_script.content.strip()
    
    # Store speech draft into data/speech_drafts folder in chronological order to keep track of each revision (for independent evaluation)
    draft_path = Path("data/speech_drafts")
    draft_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = draft_path / f"speech_draft_{timestamp}.txt"
    file_path.write_text(speech_draft, encoding="utf-8")
    
    print(f"Script Draft: {speech_draft}")
    return {"stylistic_script": speech_draft}