# Import typing tools to define lists and optional values
from typing import List, Optional, Literal

# Import Pydantic base class and Field helper 
from pydantic import BaseModel, Field, ConfigDict 
from schemas.planner_blueprint import Request, Targets, RequiredPoint, Constraints, OutlineSection, CoverageMap
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

# # ---------------------------------------------------
# # SPOKEN BEAT MODEL
# # ---------------------------------------------------    
# # Represents one short spoken idea inside a section 
# class SpokenBeat(BaseModel):
#     model_config = ConfigDict(extra="forbid")

#     # Description of one spoken beat
#     description: str = Field(..., description="A single spoken idea for the section")

# ---------------------------------------------------
# TED SECTION MODEL
# ---------------------------------------------------
# Represents one TED-style narrative section 
class TedSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Unique TED Section ID
    # Example: TS1, TS2, TS3, ...
    id: str = Field(..., pattern=r"^TS\d+$", description="Unique identifier for the TED-style section")

    # Reference back to the original planner section 
    # Example: S1, S2, S3, ...
    source_section_id: str = Field(..., pattern=r"^S\d+$", description="Original planner section ID that this TED section came from")

    # Narrative role of the section in the speech 
    # Example: hook_and_context, core_insight, evidence_and_examples, implication_and_close
    narrative_role: Literal[
        "hook_and_context", "core_insight",
        "evidence_and_examples", "implication_and_close"] = Field(..., description="Narrative role played by this section in the TED-style speech")

    # Purpose of the section 
    purpose: str = Field(..., description="Purpose of this section in the overall speech")

    # Spoken beats that later become actual speech text 
    spoken_beats: List[str] = Field(
        default_factory=list,
        description="Short spoken beats taht capture the ideas for this section"
    )

    # Transition sentence leading to the next section
    transition_out: Optional[str] = Field(
        None, 
        description="Transition from this section to the next section"
    )

    # Word budget for this section 
    word_budget: int = Field(..., ge=0, description="Approximate word budget for this section")

# ---------------------------------------------------
# RETRIEVAL REQUEST MODEL
# ---------------------------------------------------
# Represents a placeholder for facts/examples that the Content Agent should fetch later 
class RetrievalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Unique retrieval request ID 
    # Example: R1, R2, R3, ...
    id: str = Field(..., pattern=r"^R\d+$", description="Unique identifier for the retrieval request")
    
    # Description of what information is needed
    description: str=Field(..., description="Description of what factual support or example should be retrieved later")

# ---------------------------------------------------
# TED AGENT OUTPUT MODEL
# ---------------------------------------------------
# This is the schema that the LLM should directly generate. 
# It contains ONLY TED-specific fields. 
class TEDAgentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    # Opening hook for the speech 
    hook: Hook

    # Single central message of the talk 
    big_idea: str = Field(..., description="The single core idea of the TED-style speech")

    # Short description of the narrative flow
    # Example: hook -> challenge -> insight -> examples -> takeaway
    narrative_arc: str = Field(..., description="Description of the overall TED-style narrative arc")

    # TED-style narrative sections 
    ted_sections: List[TedSection] = Field(
        default_factory=list,
        description="Narrative sections transformed from the planner outline"
    )

    # Requests for additional grounding that later agents should handle
    retrieval_requests: List[RetrievalRequest] = Field(
        default_factory=list, 
        description="Placeholders for facts, examples, or evidence to retrieve later"
    ) 

# ---------------------------------------------------
# FINAL TED BLUEPRINT MODEL
# ---------------------------------------------------
# This is the full schema stored in the graph state AFTER merging: 
# validated planner blueprint + TEDAgentOutput 
class TEDBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Blueprint version inherited from planner 
    blueprint_version: str = Field(...,  description="Blueprint version inherited from the planner blueprint")   

    # Indicates the source type used to create this blueprint 
    source_blueprint_type: str = Field(
        default="planner_blueprint",
        description="Type of source blueprint used in input"
    )  

    # Type of this blueprint 
    blueprint_type: str = Field(
        default="ted_blueprint",
        description="Identifier for the blueprint type"
    )

    # Planner metadata copied through unchanged 
    # We keep these as dict because they were already validated upstream
    # request: dict = Field(..., description="Request metadata copied from the validated planner blueprint")
    # targets: dict = Field(..., description="Speech targets copied from the validated planner blueprint")
    # constraints: dict = Field(..., description="Constraints copied from the validated planner blueprint")
    # coverage_map: dict = Field(..., description="Coverage map copied from the validated planner blueprint")
    # original_outline: List[dict] = Field(..., description="Original outline copied from the validated planner blueprint")
    request: Request
    targets: Targets
    constraints: Constraints
    coverage_map: CoverageMap
    original_outline: List[OutlineSection]

    # TED-specific fields merged in from TEDAgentOutput
    hook: Hook
    big_idea: str = Field(..., description="The single core idea of the TED-style speech")
    narrative_arc: str = Field(..., description="Description of the overall TED-style narrative arc")
    ted_sections: List[TedSection] = Field(
        default_factory=list,
        description="Narrative sections transformed from the planner outline"
    )
    retrieval_requests: List[RetrievalRequest] = Field(
        default_factory=list, 
        description="Placeholders for facts, examples, or evidence to retrieve later"
    ) 
