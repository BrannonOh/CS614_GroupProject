# Import TypedDict to define the structure of the graph state 
from typing import TypedDict

# Import logging function so agents can use
from utils.logger import logger

# Import schemas to ensure outputs are structured instead of just strings
from schemas.planner_blueprint import PlannerBlueprint
from schemas.ted_blueprint import TEDBlueprint 

# Define the shared graph state, since we are writing script, just call it SpeechScriptState 
class SpeechScriptState(TypedDict):
    user_input: str # Raw user input

    planner_blueprint: PlannerBlueprint
    ted_blueprint: TEDBlueprint
    content_blueprint: str # To come up with blueprints and put in schemas/ folder
    stylistic_script: str 

    ted_feedback: str
    ted_approved: bool
    ted_attempts: int

    content_feedback: str
    content_approved: bool
    content_attempts: int

    style_feedback: str
    style_approved: bool
    style_attempts: int

def route_ted(state: SpeechScriptState):
    approved = state.get("ted_approved") or state.get("ted_attempts", 0) >= 2
    logger.info(f"[ROUTE] TED -> {'Content_Agent' if approved else 'TED_Agent (retry)'}")
    return "approved" if approved else "rejected"

def route_content(state: SpeechScriptState):
    approved = state.get("content_approved") or state.get("content_attempts", 0) >= 2
    logger.info(f"[ROUTE] Content -> {'Stylistic_Agent' if approved else 'Content_Agent (retry)'}")
    return "approved" if approved else "rejected"

def route_style(state: SpeechScriptState):
    approved = state.get("style_approved") or state.get("style_attempts", 0) >= 2
    logger.info(f"[ROUTE] Style -> {'END' if approved else 'Stylistic_Agent (retry)'}")
    return "approved" if approved else "rejected"