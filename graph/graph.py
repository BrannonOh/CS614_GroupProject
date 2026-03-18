from langgraph.graph import StateGraph, START, END
from graph.state import SpeechScriptState, route_ted, route_content, route_style
from agents.planner_agent import Planner_Agent
from agents.ted_agent import TED_Agent
from agents.content_agent import Content_Agent
from agents.stylistic_agent import Stylistic_Agent
from agents.structure_checking_agent import Structure_Checking_Agent
from agents.grounding_agent import Grounding_Agent
from agents.reflection_agent import Reflection_Agent

def route_user(state):
    approved = state.get("query_approved") or state.get("query_attempts", 0) >= 2
    return "approved" if approved else "rejected"

def build_graph():
    builder = StateGraph(SpeechScriptState)

    # Add nodes
    builder.add_node("Query_Agent", Query_Agent)
    builder.add_node("Human_Feedback", Human_Feedback)
    builder.add_node("Planner_Agent", Planner_Agent)
    builder.add_node("TED_Agent", TED_Agent)
    builder.add_node("Structure_Checking_Agent", Structure_Checking_Agent)
    builder.add_node("Content_Agent", Content_Agent)
    builder.add_node("Grounding_Agent", Grounding_Agent)
    builder.add_node("Stylistic_Agent", Stylistic_Agent)
    builder.add_node("Reflection_Agent", Reflection_Agent)

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

    # Loop 1: TED <> Structure Checker
    builder.add_edge("TED_Agent", "Structure_Checking_Agent")
    builder.add_conditional_edges(
        "Structure_Checking_Agent",
        route_ted,
        {
            "approved": "Content_Agent",
            "rejected": "TED_Agent",
        },
    )

    # Loop 2: Content <> Grounding
    builder.add_edge("Content_Agent", "Grounding_Agent")
    builder.add_conditional_edges(
        "Grounding_Agent",
        route_content,
        {
            "approved": "Stylistic_Agent",
            "rejected": "Content_Agent",
        },
    )

    # Loop 3: Stylistic <> Reflection
    builder.add_edge("Stylistic_Agent", "Reflection_Agent")
    builder.add_conditional_edges(
        "Reflection_Agent",
        route_style,
        {
            "approved": END,
            "rejected": "Stylistic_Agent",
        },
    )

    # Compile graph
    return builder.compile()

graph = build_graph()

        