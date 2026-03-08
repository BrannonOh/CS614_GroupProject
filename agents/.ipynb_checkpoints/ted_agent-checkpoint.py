import json 
from schemas.ted_blueprint import TEDBlueprint
from graph.state import GraphState

def ted_agent_node(state: GraphState) -> GraphState: 
    """
    Temporary TED agent that loads mock output.
    Later we will replace this with an LLM call. 
    """

    # Load mock TED output 
    with open("mocks/mock_ted_blueprint.json") as f: 
        ted_data = json.load(f)

    # Validate using Pydantic 
    ted_blueprint = TEDBlueprint(**ted_data)

    # Store in graph state 
    state["ted_blueprint"] = ted_blueprint

    return state 