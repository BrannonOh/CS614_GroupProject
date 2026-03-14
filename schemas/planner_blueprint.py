# Import typing helpers for type hints
# These help define what type each field should be
from typing import List, Dict, Literal

# Import BaseModel from Pydantic
# BaseModel is the core class used to define structured data models
from pydantic import BaseModel, Field, ConfigDict, model_validator

# ---------------------------------------------------
# REQUEST SECTION
# ---------------------------------------------------
# Contains the original request information from the user
class Request(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str = Field(..., description="Main topic of the speech")
    audience: str = Field(..., description="Target audience")
    occasion: str = Field(..., description="Event where the speech will be delivered")
    time_limit_minutes: int = Field(
        ..., # required field 
        ge=1, # must be >=1 
        le=60, # must be <= 60
        description="Maximum allowed speech duration in minutes"
    )

# ---------------------------------------------------
# TARGETS SECTION
# ---------------------------------------------------
# Defines speech length and tone 
class Targets(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estimated_wpm: int = Field(
        default=140,
        ge=80,
        le=220,
        description="Estimated speaking speed in words per minute"
    )
    target_word_count: int = Field(
        ...,
        description="Target speech length in words"
    )

# ---------------------------------------------------
# SECTION
# ---------------------------------------------------
# Represents each planned section of the speech 
class Section(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(
        ...,
        pattern=r"^S\d+$", # Must look like S1, S2, S3
        description="Section identifier such as S1, S2, S3"
    )
    name: str = Field(..., description="Name of the section")
    purpose: str = Field(...,description="Purpose of the section")
    must_include_points: List[str] = Field(
        default_factory=list,
        description="Key talking points that appear in the section"
    )
    must_include_facts: List[str] = Field(
        default_factory=list,
        description="Specific factual details that appear in the section"
    )

# ---------------------------------------------------
# MAIN BLUEPRINT MODEL
# ---------------------------------------------------
# This is the top-level schema used by the planner 
class PlannerBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid") # Config ensures no unexpected keys appear 
    
    request: Request # Request metadata 
    targets: Targets # Speech targets 
    sections: List[Section] = Field(..., min_length=1) # Outline sections

    # ---------------------------------------------------
    # POST-VALIDATION CHECK
    # ---------------------------------------------------
    # Runs after model validation 
    @model_validator(mode="after")
    def check_internal_consistency(self):

        # Collect section IDs
        section_ids = [section.section_id for section in self.sections]

        # Ensure section IDs are unique 
        if len(section_ids) != len(set(section_ids)):
            raise ValueError("Duplicate section_id detected")
        
        return self 