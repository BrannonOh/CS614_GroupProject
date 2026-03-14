from langgraph.graph import StateGraph, END 
from graph.state import GraphState
from agents.ted_agent import ted_agent_node

def build_graph(): 

    # Create graph builder 
    builder = StateGraph(GraphState)

    # Add nodes 
    builder.add_node("ted_agent", ted_agent_node)

    # Define flow 
    builder.set_entry_point("ted_agent")
    builder.add_edge("ted_agent", END)

    # Compile graph
    graph = builder.compile()

    return graph 

# From Yifang main.py file
# from typing_extensions import TypedDict
# from langgraph.graph import StateGraph, START, END
# from Agents.Planner_Agent import Planner_Agent
# from Agents.TED_Agent import TED_Agent
# from Agents.Content_Agent import Content_Agent
# from Agents.Stylistic_Agent import Stylistic_Agent
# from Agents.Structure_Checking_Agent import Structure_Checking_Agent
# from Agents.Grounding_Agent import Grounding_Agent
# from Agents.Reflection_Agent import Reflection_Agent
# from logger import logger

# class State(TypedDict):
#     graph_state: str
#     plan: str
#     ted_structure: str
#     ted_feedback: str
#     ted_approaved: bool
#     ted_attempts: int
#     content: str
#     content_feedback: str
#     content_approved: bool
#     content_attempts: int
#     stylistic_script: str
#     style_feedback: str
#     style_approved: bool
#     style_attempts: int


# def route_ted(state):
#     approved = state.get("ted_approved") or state.get("ted_attempts", 0) >= 2
#     logger.info(f"[ROUTE] TED -> {'Content_Agent' if approved else 'TED_Agent (retry)'}")
#     return "approved" if approved else "rejected"

# def route_content(state):
#     approved = state.get("content_approved") or state.get("content_attempts", 0) >= 2
#     logger.info(f"[ROUTE] Content -> {'Stylistic_Agent' if approved else 'Content_Agent (retry)'}")
#     return "approved" if approved else "rejected"

# def route_style(state):
#     approved = state.get("style_approved") or state.get("style_attempts", 0) >= 2
#     logger.info(f"[ROUTE] Style -> {'END' if approved else 'Stylistic_Agent (retry)'}")
#     return "approved" if approved else "rejected"



# builder = StateGraph(State)

# builder.add_node("Planner_Agent", Planner_Agent)
# builder.add_node("TED_Agent", TED_Agent)
# builder.add_node("Structure_Checking_Agent", Structure_Checking_Agent)
# builder.add_node("Content_Agent", Content_Agent)
# builder.add_node("Grounding_Agent", Grounding_Agent)
# builder.add_node("Stylistic_Agent", Stylistic_Agent)
# builder.add_node("Reflection_Agent", Reflection_Agent)


# builder.add_edge(START, "Planner_Agent")
# builder.add_edge("Planner_Agent", "TED_Agent")

# # Loop 1: TED <> Structure Checker
# builder.add_edge("TED_Agent", "Structure_Checking_Agent")
# builder.add_conditional_edges(
#     "Structure_Checking_Agent",
#     route_ted,
#     {
#         "approved": "Content_Agent",
#         "rejected": "TED_Agent"
#     }
# )

# # Loop 2: Content <> Grounding
# builder.add_edge("Content_Agent", "Grounding_Agent")
# builder.add_conditional_edges(
#     "Grounding_Agent",
#     route_content,
#     {
#         "approved": "Stylistic_Agent",
#         "rejected": "Content_Agent"
#     }
# )

# # Loop 3: Stylistic <> Reflection
# builder.add_edge("Stylistic_Agent", "Reflection_Agent")
# builder.add_conditional_edges(
#     "Reflection_Agent",
#     route_style,
#     {
#         "approved": END,
#         "rejected": "Stylistic_Agent"
#     }
# )

# graph = builder.compile()


# def main():
#     print("Speech Generator ready. Type 'quit' to exit.\n")
    
#     while True:
#         user_input = input("You: ").strip()
        
#         if user_input.lower() in ["quit", "exit", "q"]:
#             print("Goodbye!")
#             break
            
#         if not user_input:
#             continue
        
#         print("\nGenerating your speech...\n")
        
#         result = graph.invoke({
#             "graph_state": user_input
#         })
        
#         print("=== FINAL VOICE SCRIPT ===")
#         print(result["stylistic_script"])
#         print("==========================\n")