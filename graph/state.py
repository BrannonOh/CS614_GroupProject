# Import TypedDict to define the structure of the graph state 
from typing import List, Dict, Any, TypedDict, Optional

# Import logging function so agents can use
from utils.logger import logger

# Import schemas to ensure outputs are structured instead of just strings
from schemas.planner_blueprint import PlannerBlueprint
from schemas.query_check_blueprint import QueryCheckBlueprint
from schemas.ted_blueprint import TEDBlueprint
from schemas.structure_checking import StructureCheckOutput
from schemas.content_blueprint import ContentBlueprint
from schemas.reflection_blueprint import ReflectionBlueprint
from schemas.judging_output import JudgingOutput
from schemas.content_working_blueprint import FinalOutputGrounded


# Define the shared graph state
class SpeechScriptState(TypedDict):
    user_input: str 

    # QUERY CHECK | PLANNER 
    query_check: Optional[QueryCheckBlueprint]
    query_facts: List[Dict[str, Any]]
    query_approved: bool
    query_attempts: int
    query_feedback: str
    
    planner_blueprint: Optional[PlannerBlueprint]
    
    # TED | STRUCTURE CHECK | TED REVISION 
    ted_blueprint: Optional[TEDBlueprint]
    ted_validation_retry_count: int 
    ted_output_retry_count: int 
    ted_error_type: str

    structure_check_result: Optional[StructureCheckOutput]
    structure_check_validation_retry_count: int 
    structure_check_retry_count: int 
    structure_error_type: str
    structure_feedback_brief: Optional[dict]

    ted_revision_validation_count: int
    ted_revision_count: int 
    ted_revision_error_type: str

    # CONTENT | RESEARCH | GROUNDING
    user_input: Dict[str, Any]
    config: Dict[str, Any]
    graph_state: str
    retry_count: int

    content_check: Dict[str, Any]
    content_results: List[Dict[str, Any]]
    content_tasks: List[Dict[str, Any]]
    content_approved: bool
    content_attempts: int
    content_feedback: str

    research_check: Dict[str, Any]
    research_results: List[Dict[str, Any]]
    research_approved: bool
    research_attempts: int
    research_feedback: str

    grounding_check: Dict[str, Any]
    grounding_results: Dict[str, Any]
    grounding_approved: bool
    grounding_attempts: int
    grounding_feedback: str

    needs_retry: bool
    retry_reason: str
    final_output: Dict[str, Any]

    needs_retry: bool
    retry_reason: str

    final_output: FinalOutputGrounded | Dict[str, Any]

    content_blueprint: Optional[ContentBlueprint]

    # STYLE EXTRACT | AGGREGATE | SCRIPT WRITING | REFLECTION
    chunk_style_notes: List[Dict[str, Any]] 
    style_profile: Dict[str, Any]
    stylistic_script: str 
    style_feedback: Optional[ReflectionBlueprint]
    style_reviews: int

    # JUDGING RESULT 
    stylistic_script: Optional[str]
    judge_a_result: Optional[JudgingOutput]
    judge_b_result: Optional[JudgingOutput]
    last_error: Optional[str]
