from typing import List
from pydantic import BaseModel, Field, ConfigDict

class StyleProfileStructure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone: List[str] = Field(..., max_length=6)
    avoid: List[str] = Field(..., max_length=6)
    lexical_preferences: List[str] = Field(..., max_length=6)
    syntax: List[str] = Field(..., max_length=6)
    rhetorical_devices: List[str] = Field(..., max_length=6)
    argument_structure: List[str] = Field(..., max_length=6)
    audience_relationship: List[str] = Field(..., max_length=6)