# Import typing tools to define lists and optional values
from typing import List, Optional, Literal

# Import Pydantic base class and Field helper 
from pydantic import BaseModel, Field, ConfigDict, model_validator

# ---------------------------------------------------
# HOOK MODEL
# ---------------------------------------------------
# No change in schema from upstream
class Hook(BaseModel): 
    model_config = ConfigDict(extra="forbid")
    type: Literal[
        "personal anecdote", "surprising statistic", "rhetorical question",
        "bold/contrarian statement", "What-if scenario",
        "quote", "relatable problem", "observation"] = Field(..., description="Type of opening hook used in the speech")
    description: str = Field(..., description="Description of the hook idea")

# ---------------------------------------------------
# TED SECTION MODEL
# ---------------------------------------------------
# No change in schema from upstream 
class TedSection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., pattern=r"^TS\d+$", description="Unique identifier for the TED-style section")
    narrative_role: Literal[
        "hook_and_context", "core_insight",
        "evidence_and_examples", "implication_and_close"] = Field(..., description="Narrative role played by this section in the TED-style speech")
    purpose: str = Field(..., description="Purpose of this section in the overall speech")
    must_include_points: List[str] = Field(
        default_factory=list,
        description="Points that must be included in this section"
    )
    must_include_facts: List[str] = Field(
        default_factory=list,
        description="Facts that must be included in this section"
    )
    transition_out: Optional[str] = Field(
        None, 
        description="Transition from this section to the next section"
    )
    word_budget: int = Field(..., ge=0, description="Approximate word budget for this section")

# ---------------------------------------------------
# CONTENT BLUEPRINT MODEL
# ---------------------------------------------------
# By right, no change in schema from upstream
class ContentBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hook: Hook
    big_idea: str = Field(..., description="The single core idea of the TED-style speech")
    ted_sections: List[TedSection] = Field(
        default_factory=list,
        description="Narrative sections transformed from the planner outline"
    )

    @model_validator(mode="after")
    def check_section_ids_unique(self):
        ids = [section.id for section in self.ted_sections]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate ted section id detected")
        return self