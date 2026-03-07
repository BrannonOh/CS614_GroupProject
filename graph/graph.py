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
    