from typing import List
from pydantic import BaseModel, Field, ConfigDict 

class StructureCheckResult(BaseModel): 
    model_config = ConfigDict(extra="forbid")

    is_valid: bool = Field(
        ..., 
        description="Whether the TED blueprint structure is acceptable"
    )

    issues: List[str] = Field(
        default_factory=list,
        description="Critical structural issues that must be fixed"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Minor concerns that do not block generation"
    )

    strengths: List[str] = Field(
        default_factory=list, 
        description="Positive aspects of the structure"
    )

    suggested_fixes: List[str] = Field(
        default_factory=list,
        description="Suggested improvements if issues exist"
    )