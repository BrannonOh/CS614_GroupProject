# Import typing helpers for type hints
# These help define what type each field should be
from typing import List, Dict, Literal

# Import BaseModel from Pydantic
# BaseModel is the core class used to define structured data models
from pydantic import BaseModel, Field, ConfigDict, model_validator


# Define allowed values for voice strictness 
# Literal ensures only these values are allowed 
StyleStrictness = Literal["low", "medium", "high"]

# ---------------------------------------------------
# REQUEST SECTION
# ---------------------------------------------------
# Contains the original request information from the user
class Request(BaseModel):
    topic: str = Field(..., description="Main topic of the speech")
    audience: str = Field(..., description="Target audience")
    occasion: str = Field(..., description="Event where the speech will be delivered")
    time_limit_minutes: int = Field(
        ..., # required field 
        ge=1, # must be >=1 
        le=60, # must be <= 60
        description="Maximum allowed speech duration"
    )
    style_target: str = Field(
        default="BMW",
        description="Corporate voice to emulate"
    )
    style_strictness: StyleStrictness=Field(
        default="medium",
        description="How strictly the style should be followed"
    )

# ---------------------------------------------------
# TARGETS SECTION
# ---------------------------------------------------
# Defines speech length and tone 
class Targets(BaseModel):
    estimated_wpm: int = Field(
        default=140,
        description="Estimated speaking speed"
    )
    target_word_count: int = Field(
        ...,
        description="Target speech length in words"
    )
    tone_keywords: List[str] = Field(
        default_factory=list,
        description="Tone guidance keywords"
    )

# ---------------------------------------------------
# REQUIRED POINTS
# ---------------------------------------------------
# Required points that must appear somewhere in the speech 
class RequiredPoint(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^RP\d+$", # Must look like RP1, RP2, RP3 
        description="Unique identifier for required point"
    )
    text: str = Field(
        ...,
        description="Text describing the required point"
    )

# ---------------------------------------------------
# CONSTRAINTS SECTION
# ---------------------------------------------------
class Constraints(BaseModel):
    required_points: List[RequiredPoint] = Field(
        default_factory=list 
    )
    avoid_topics: List[str] = Field(
        default_factory=list
    )
    max_iterations: int = Field(
        default=2,
        description="Maximum allowed iteration loops"
    )

# ---------------------------------------------------
# OUTLINE SECTION
# ---------------------------------------------------
# Represents each planned section of the speech 
class OutlineSection(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^S\d+$", # Must look like S1, S2, S3
        description="Section identifier"
    )
    label: str = Field(
        ...,
        description="Name of the section"
    )
    purpose: str = Field(
        ...,
        description="Purpose of the section"
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="Key talking points"
    )
    must_include: List[str] = Field(
        default_factory=list,
        description="Points that must appear inside the section"
    )
    word_budget: int = Field(
        ...,
        ge=0,
        description="Maximum words allowed for section"
    )

# ---------------------------------------------------
# COVERAGE MAP
# ---------------------------------------------------
class CoverageMap(BaseModel):
    required_points_to_sections: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Mapping from required point ID -> section IDs"
    )

# ---------------------------------------------------
# MAIN BLUEPRINT MODEL
# ---------------------------------------------------
# This is the top-level schema used by the planner 
class PlannerBlueprint(BaseModel):
    
    model_config = ConfigDict(extra="forbid") # Config ensures no unexpected keys appear 
    blueprint_version: str = Field(default="1.0")
    request: Request # Request metadata 
    targets: Targets # Speech targets 
    constraings: Constraints # Planner constraints 
    outline: List[OutlineSection] # Outline sections
    coverage_map: CoverageMap # Coverage mapping 

    # ---------------------------------------------------
    # POST-VALIDATION CHECK
    # ---------------------------------------------------
    # Runs after model validation 
    @model_validator(mode="after")
    def check_internal_consistency(self):

        # Collect section IDs
        section_ids = [section.id for section in self.outline]

        # Ensure section IDs are unique 
        if len(section_ids) != len(set(section_ids)):
            raise ValueError("Duplicate section ID detected")
        
        return self 