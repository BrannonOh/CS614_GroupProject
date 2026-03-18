from langgraph.graph import StateGraph, START, END
# Import TypedDict to define the structure of the graph state 
from typing import List, Dict, Any, TypedDict, Optional, Literal
from graph.state import SpeechScriptState
from agents.query_agent import Query_Agent
from agents.planner_agent import Planner_Agent
from agents.ted_agent import ted_agent_node
from agents.structure_checking_agent import structure_checking_agent_node
from agents.ted_revision_agent import ted_revision_agent_node
# from agents.content_agent import Content_Agent
# from agents.stylistic_agent import Stylistic_Agent
# from agents.structure_checking_agent import Structure_Checking_Agent
# from agents.grounding_agent import Grounding_Agent
# from agents.reflection_agent import Reflection_Agent
from agents.human_feedback import Human_Feedback, collect_user_feedback
from agents.judging_agent import judging_agent_node

# =================
# ROUTING FUNCTIONS 
# =================
MAX_TED_GENERATION_RETRIES = 3
MAX_STRUCTURE_CHECK_RETRIES = 3 
MAX_TED_REVISIONS_RETRIES = 3 

def route_user(state: SpeechScriptState):
    approved = state.get("query_approved") or state.get("query_attempts", 0) >= 2
    return "approved" if approved else "rejected"

def route_after_ted_agent(state: SpeechScriptState) -> Literal[
    "pass", "retry_ted", "fail"
]:
    print("Routing after TED agent:", state.get("ted_blueprint"), state["ted_output_retry_count"])
    if state.get("ted_blueprint") is not None: 
        return "pass"

    if state["ted_output_retry_count"] < MAX_TED_GENERATION_RETRIES:
        return "retry_ted"

    return "fail"

def route_after_structure_check(state: SpeechScriptState) -> Literal[
    "is_valid = True", 
    "retry_structure",
    "is_valid = False",
    "fail"
]:
    print("Routing after Structure Checking agent:", state["structure_check_retry_count"])
    structure_result = state.get("structure_check_result")

    if structure_result is not None: 
        if structure_result.is_valid: 
            return "is_valid = True"
    
        if state["ted_revision_count"] < MAX_TED_REVISIONS_RETRIES:
            return "is_valid = False"
        
        return "fail"
    
    if state["structure_check_retry_count"] < MAX_STRUCTURE_CHECK_RETRIES:
        return "retry_structure"

    return "fail"







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
    # builder.add_node("Content_Agent", Content_Agent)
    # builder.add_node("Grounding_Agent", Grounding_Agent)
    # builder.add_node("Stylistic_Agent", Stylistic_Agent)
    # builder.add_node("Reflection_Agent", Reflection_Agent)
    builder.add_node("judging_agent", judging_agent_node)

    # Define flow
    builder.add_edge(START, "Query_Agent")
    builder.add_edge("Human_Feedback", "Query_Agent") 
    builder.add_conditional_edges(
        "Query_Agent",
        route_user,
        {
            "approved": "Planner_Agent",
            "rejected": "Human_Feedback" # HITL - needs to go back to user with feedback
        }
    )

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
        "is_valid = True": END, #"content_agent", # CHANGE LATER
        "retry_structure": "Structure_Checking_Agent",
        "is_valid = False": "TED_Revision_Agent",
        "fail": END,
    }
    )
    builder.add_edge("TED_Revision_Agent", "Structure_Checking_Agent")
    builder.add_edge("Structure_Checking_Agent", END)

    # # Loop 2: Content <> Grounding
    # builder.add_edge("Content_Agent", "Grounding_Agent")
    # builder.add_conditional_edges(
    #     "Grounding_Agent",
    #     route_content,
    #     {
    #         "approved": "Stylistic_Agent",
    #         "rejected": "Content_Agent",
    #     },
    # )

    # # Loop 3: Stylistic <> Reflection
    # builder.add_edge("Stylistic_Agent", "Reflection_Agent")
    # builder.add_conditional_edges(
    #     "Reflection_Agent",
    #     route_style,
    #     {
    #         "approved": END,
    #         "rejected": "Stylistic_Agent",
    #     },
    # )

    # builder.add_edge("judging_agent", END)

    # Compile graph
    return builder.compile()

graph = build_graph()


