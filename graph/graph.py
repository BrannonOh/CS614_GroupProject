from typing import Literal
from langgraph.graph import StateGraph, START, END
from graph.state import SpeechScriptState
from pprint import pprint

from agents.query_agent import Query_Agent
from agents.human_feedback import Human_Feedback, collect_user_feedback
from agents.planner_agent import Planner_Agent
from agents.ted_agent import ted_agent_node
from agents.structure_checking_agent import structure_checking_agent_node
from agents.ted_revision_agent import ted_revision_agent_node
from agents.content_agent import Content_Agent
from agents.style_extraction_agent import Style_Extraction_Agent
from agents.style_aggregation_agent import Style_Aggregation_Agent
from agents.script_writing_agent import Script_Writing_Agent
from agents.reflection_agent import Reflection_Agent
from agents.judging_agent import judging_agent_node

# =================
# ROUTING FUNCTIONS 
# =================
MAX_TED_RETRIES = 3
MAX_STRUCTURE_RETRIES=3
MAX_TED_USER_RETRIES = 3
MAX_STYLE_REVIEWS = 2

# QUERY CHECK | PLANNER 
# def route_user(state: SpeechScriptState):
#     approved = state.get("query_approved") or state.get("query_attempts", 0) >= 3
#     return "approved" if approved else "rejected"

def route_user(state: SpeechScriptState):
    attempts = state.get("query_attempts", 0)

    if attempts >= MAX_TED_USER_RETRIES:
        return "quit"   # stop the workflow

    if state.get("query_approved"):
        return "approved"

    return "rejected"

# TED | STRUCTURE CHECK | TED REVISION  
def route_after_ted_agent(state: SpeechScriptState) -> Literal[
    "pass", "retry_ted", "fail"
]:
    print("Routing after TED agent:")
    if state.get("ted_blueprint") is not None: 
        print("TED Agent output is successful. TED Blueprint:")
        pprint(state.get("ted_blueprint").model_dump(), sort_dicts=False)
        print("Moving on to Structure Checking Agent...")
        return "pass"

    error_type = state.get("ted_error_type")

    if error_type == "validation":
        if state.get("ted_validation_retry_count", 0) < MAX_TED_RETRIES:
            print(f"Number of TED Output validation retries: {state.get("ted_validation_retry_count")}")
            return "retry_ted"

    if error_type == "generation": 
        if state.get("ted_output_retry_count", 0) < MAX_TED_RETRIES:
            print(f"Number of TED Output generation retries: {state.get("ted_output_retry_count")}")
            return "retry_ted"

    print(f"TED Agent failed due to max. `ted_validation_retry_count` or `ted_output_retry_count`.")
    return "fail"

def route_after_structure_check(state: SpeechScriptState) -> Literal[
    "is_valid = True", 
    "retry_structure",
    "is_valid = False",
    "fail"
]:
    print("Routing after Structure Checking agent:")
    structure_result = state.get("structure_check_result")

    if structure_result is not None: 
        if structure_result.is_valid: 
            print("Structure result is valid. Structure Result:")
            pprint(structure_result.model_dump(), sort_dicts=False)
            print("Moving on to Content Agent...")
            return "is_valid = True"

        # structure_result.is_valid = False 
        if state.get("ted_revision_count", 0) < MAX_TED_RETRIES:
            print("Structure result is not valid. Structure Result:")
            pprint(structure_result.model_dump(), sort_dicts=False)
            print("Moving on to TED Revision Agent...")
            return "is_valid = False"
        
        return "fail"

    error_type = state.get("structure_error_type")

    if error_type == "validation": 
        if state.get("structure_check_validation_retry_count", 0) < MAX_STRUCTURE_RETRIES:
            print(f"Number of Structure Check validation retries: {state.get("structure_check_validation_retry_count")}")
            return "retry_structure"    

    if error_type == "generation":
        if state.get("structure_check_retry_count", 0) < MAX_STRUCTURE_RETRIES:
            print(f"Number of Structure Check generation retries: {state.get("structure_check_retry_count")}")
            return "retry_structure"

    print(f"Structure Checking Agent failed due to max. `structure_check_validation_retry_count` or `structure_check_retry_count`.")
    return "fail"

# CONTENT

# STYLE EXTRACT | AGGREGATE | SCRIPT WRITING | REFLECTION
def route_after_reflection_check(state: SpeechScriptState):
    style_feedback = state.get("style_feedback", {})
    has_content_issues = bool(style_feedback.get("content_issues"))
    has_style_issues = bool(style_feedback.get("style_issues"))

    has_any_issues = has_content_issues or has_style_issues
    attempts = state.get("style_reviews", 0)

    if not has_any_issues:
        return "pass"

    if attempts > MAX_STYLE_REVIEWS:
        return "pass"   # stop looping after MAX_STYLE_REVIEWS reviews

    return "repair"


# =============
# BUILD GRAPH 
# =============
def build_graph():
    builder = StateGraph(SpeechScriptState)

    # Add nodes
    builder.add_node("Query_Agent", Query_Agent)
    builder.add_node("Human_Feedback", Human_Feedback)
    builder.add_node("Planner_Agent", Planner_Agent)
    builder.add_node("TED_Agent", ted_agent_node)
    builder.add_node("Structure_Checking_Agent", structure_checking_agent_node)
    builder.add_node("TED_Revision_Agent", ted_revision_agent_node)
    builder.add_node("Content_Agent", Content_Agent)
    builder.add_node("Style_Extraction_Agent", Style_Extraction_Agent)
    builder.add_node("Style_Aggregation_Agent", Style_Aggregation_Agent)
    builder.add_node("Script_Writing_Agent", Script_Writing_Agent)
    builder.add_node("Reflection_Agent", Reflection_Agent)
    builder.add_node("judging_agent", judging_agent_node)

    # Define flow
    builder.add_edge(START, "Query_Agent")
    builder.add_edge("Human_Feedback", "Query_Agent") 
    builder.add_conditional_edges(
        "Query_Agent",
        route_user,
        {
            "approved": "Planner_Agent",
            "rejected": "Human_Feedback",
            "quit": END   # or a custom termination node
        }
    )
    # builder.add_conditional_edges(
    #     "Query_Agent",
    #     route_user,
    #     {
    #         "approved": "Planner_Agent",
    #         "rejected": "Human_Feedback" # HITL - needs to go back to user with feedback
    #     }
    # )

    builder.add_edge("Planner_Agent", "TED_Agent")
    builder.add_conditional_edges(
        "TED_Agent", 
        route_after_ted_agent,
        {
            "pass": "Structure_Checking_Agent",
            "retry_ted": "TED_Agent",
            "fail": END,
        }
    )

    builder.add_conditional_edges(
        "Structure_Checking_Agent",
        route_after_structure_check,
        {
            "is_valid = True": "Content_Agent",
            "retry_structure": "Structure_Checking_Agent",
            "is_valid = False": "TED_Revision_Agent",
            "fail": END,
        }
    )
    builder.add_edge("TED_Revision_Agent", "Structure_Checking_Agent")

    # Jesseline to fill in her part here
    builder.add_edge("Structure_Checking_Agent", "Content_Agent")

    builder.add_edge("Content_Agent", "Style_Extraction_Agent")
    builder.add_edge("Style_Extraction_Agent", "Style_Aggregation_Agent")
    builder.add_edge("Style_Aggregation_Agent", "Script_Writing_Agent")
    builder.add_edge("Script_Writing_Agent", "Reflection_Agent")

    builder.add_conditional_edges(
        "Reflection_Agent", 
        route_after_reflection_check,
        {
            "pass": END, # Go to Judging Agent 
            "repair": "Script_Writing_Agent"
        }
    )

    # builder.add_edge("judging_agent", END)

    # Compile graph
    return builder.compile()

graph = build_graph()