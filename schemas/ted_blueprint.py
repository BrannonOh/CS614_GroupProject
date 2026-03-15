# Import typing tools to define lists and optional values
from typing import List, Optional, Literal

# Import Pydantic base class and Field helper 
from pydantic import BaseModel, Field, ConfigDict, model_validator

# ---------------------------------------------------
# HOOK MODEL
# ---------------------------------------------------
# Represents the opening hook idea of the TED-style talk 
class Hook(BaseModel): 
    # Forbid unexpected extra fields 
    model_config = ConfigDict(extra="forbid")

    # Type of hook
    # Example values: question, statistic, anecdote, contrast
    type: Literal[
        "personal anecdote", "surprising statistic", "rhetorical question",
        "bold/contrarian statement", "What-if scenario",
        "quote", "relatable problem", "observation"] = Field(..., description="Type of opening hook used in the speech")
    description: str = Field(..., description="Description of the hook idea")

# ---------------------------------------------------
# TED SECTION MODEL
# ---------------------------------------------------
# Represents one TED-style narrative section 
class TedSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Unique TED Section ID
    # Example: TS1, TS2, TS3, ...
    id: str = Field(..., pattern=r"^TS\d+$", description="Unique identifier for the TED-style section")

    # Narrative role of the section in the speech 
    # Example: hook_and_context, core_insight, evidence_and_examples, implication_and_close
    narrative_role: Literal[
        "hook_and_context", "core_insight",
        "evidence_and_examples", "implication_and_close"] = Field(..., description="Narrative role played by this section in the TED-style speech")

    # Purpose of the section 
    purpose: str = Field(..., description="Purpose of this section in the overall speech")

    # Points that have to be covered 
    must_include_points: List[str] = Field(
        default_factory=list,
        description="Points that must be included in this section"
    )
    must_include_facts: List[str] = Field(
        default_factory=list, 
        description="Facts that must be included in this section"
    )
    # Transition sentence leading to the next section
    transition_out: Optional[str] = Field(
        None, 
        description="Transition from this section to the next section"
    )

    # Word budget for this section 
    word_budget: int = Field(..., ge=0, description="Approximate word budget for this section")

# ---------------------------------------------------
# TED AGENT OUTPUT MODEL & FINAL TED BLUEPRINT MODEL
# ---------------------------------------------------
# This is the full schema stored in the graph state AFTER merging: 
# validated planner blueprint + TEDAgentOutput 
class TEDBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # TED-specific fields merged in from TEDAgentOutput
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
