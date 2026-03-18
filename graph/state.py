# Import TypedDict to define the structure of the graph state 
from typing import List, Dict, Any, TypedDict, Optional

# Import logging function so agents can use
from utils.logger import logger

# Import schemas to ensure outputs are structured instead of just strings
from schemas.planner_blueprint import PlannerBlueprint
from schemas.query_check_blueprint import QueryCheckBlueprint
from schemas.ted_blueprint import TEDBlueprint
from schemas.structure_checking import StructureCheckOutput
from schemas.judging_output import JudgingOutput


# Define the shared graph state, since we are writing script, just call it SpeechScriptState 
class SpeechScriptState(TypedDict):
    user_input: str 

    query_check: Optional[QueryCheckBlueprint]
    query_facts: List[Dict[str, Any]]
    query_approved: bool
    query_attempts: int
    query_feedback: str
    
    planner_blueprint: Optional[PlannerBlueprint]
    
    # Brannon
    ted_blueprint: Optional[TEDBlueprint]
    structure_check_result: Optional[StructureCheckOutput]
    structure_feedback_brief: Optional[dict]
    final_speech: Optional[str]
    judging_result: Optional[JudgingOutput]
    ted_output_retry_count: int 
    structure_check_retry_count: int 
    ted_revision_count: int 
    last_error: Optional[str]

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
