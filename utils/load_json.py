import json 
from schemas.planner_blueprint import PlannerBlueprint

def load_planner_blueprint(path: str) -> PlannerBlueprint:

    # Load raw json
    with open(path, "r") as f: 
        data = json.load(f)

    # Validate using Pydantic
    blueprint = PlannerBlueprint(**data)

    return blueprint