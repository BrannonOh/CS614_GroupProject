# Import typing tools to define lists and optional values
from typing import List, Optional, Literal

# Import Pydantic base class and Field helper 
from pydantic import BaseModel, Field, ConfigDict, model_validator

# ---------------------------------------------------
# SECTION MODEL
# ---------------------------------------------------
# A summarised version of ContentBlueprint, only containing the fields we are evaluating
class ScriptEvalSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^TS\d+$", description="Unique identifier for the TED-style section")
    matched_points: List[str] = Field(
        default_factory=list,
        description="Points that must be included in this section and were found in the speech draft"
    )
    matched_facts: List[str] = Field(
        default_factory=list,
        description="Facts that must be included in this section and were found in the speech draft"
    )

# ---------------------------------------------------
# SCRIPT EVALUATION MODEL
# ---------------------------------------------------
# A summarised version of ContentBlueprint
class ScriptEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eval_sections: List[ScriptEvalSection] = Field(
        default_factory=list,
        description="Narrative sections analysed"
    )

    @model_validator(mode="after")
    def check_section_ids_unique(self):
        ids = [section.id for section in self.eval_sections]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate section id detected")
        return self