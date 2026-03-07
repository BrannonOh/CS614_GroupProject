# Import TypedDict to define the structure of the graph state 
from typing import TypedDict

# Import the scehmas we created earlier 
from schemas.planner_blueprint import PlannerBlueprint
# from schemas.ted_blueprint import TEDBlueprint 

# Define the shared graph state 
class GraphState(TypedDict):
    user_input: dict # Raw user input (optional depending on the pipeline)
    planner_blueprint: PlannerBlueprint # Validated planner blueprint produced earlier 
    ted_blueprint: TEDBlueprint # Output of the TED agent 