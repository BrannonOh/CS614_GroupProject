from typing import Literal
from langgraph.graph import StateGraph, START, END
from graph.state import SpeechScriptState

from agents.planner_agent_baseline import Planner_Agent
from agents.ted_agent_baseline import ted_agent_node
# from agents.content_agent_baseline_v2 import Content_Agent   
from agents.script_writing_agent_baseline_v2 import Script_Writing_Agent
from agents.judging_agent_A_baseline import judging_agent_a_node
from agents.judging_agent_B_baseline import judging_agent_b_node

# JUDGING 
def route_to_judges(state: SpeechScriptState):
    return["judge_a", "judge_b"]

def build_graph():
    builder = StateGraph(SpeechScriptState)

    # Add nodes
    builder.add_node("Planner_Agent", Planner_Agent)
    builder.add_node("TED_Agent", ted_agent_node)
    # builder.add_node("Content_Agent", Content_Agent)
    builder.add_node("Script_Writing_Agent", Script_Writing_Agent)
    builder.add_node("Judge_Fanout", lambda state: state)
    builder.add_node("Judge_A", judging_agent_a_node)
    builder.add_node("Judge_B", judging_agent_b_node)

    # Define flow
    builder.add_edge(START, "Planner_Agent") 
    builder.add_edge("Planner_Agent", "TED_Agent")
    # builder.add_edge("TED_Agent", "Content_Agent")
    # builder.add_edge("Content_Agent", "Script_Writing_Agent")
    builder.add_edge("TED_Agent", "Script_Writing_Agent")
    builder.add_edge("Script_Writing_Agent", "Judge_Fanout")
    builder.add_conditional_edges(
        "Judge_Fanout",
        route_to_judges,
        {
            "judge_a": "Judge_A",
            "judge_b": "Judge_B",
        }
    )

    builder.add_edge("Judge_A", END)
    builder.add_edge("Judge_B", END)
    
    # Compile graph
    return builder.compile()

graph = build_graph()
