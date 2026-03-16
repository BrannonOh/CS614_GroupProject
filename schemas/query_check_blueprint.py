from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from typing import List, Optional


# FACT CHECK RESULT
# Represents a single fact that has been checked
class FactCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    serial_number: int = Field(
        ...,
        ge=1,
        description="Sequential identifier for the fact"
    )

    fact_identified: str = Field(
        ...,
        description="The factual claim extracted from the speech input"
    )

    supported: Optional[bool] = Field(
        ...,
        description="Whether the claim is supported by reliable sources. Null if unverifiable."
    )

    relevant: Optional[bool] = Field(
        ...,
        description="Whether the fact is relevant to the speech topic or occasion"
    )

    source_url: Optional[str] = Field(
        None,
        description="URL used to verify the claim"
    )

    feedback: Optional[str] = Field(
        None,
        description="Optional feedback explaining issues with the claim"
    )



# QUERY CHECK BLUEPRINT
# Top-level schema returned by the Query Agent
class QueryCheckBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checks_results: List[FactCheckResult] = Field(
        ...,
        description="List of fact-checking results"
    )

    # POST-VALIDATION CHECK
    # Ensures serial numbers are unique
    def model_post_init(self, __context):

        serial_numbers = [item.serial_number for item in self.checks_results]

        if len(serial_numbers) != len(set(serial_numbers)):
            raise ValueError("Duplicate serial_number detected in fact checks")