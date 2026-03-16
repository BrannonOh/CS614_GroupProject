from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

JudgeScore = Literal[1, 2, 3, 4, 5]

class JudgingCriterionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: JudgeScore = Field(..., description="1=very poor, 5=excellent")
    justification: str = Field(..., description="Short justification for the score")

class JudgingCriteriaScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_audience_alignment: JudgingCriterionScore
    narrative_coherence: JudgingCriterionScore
    content_quality_credibility: JudgingCriterionScore
    clarity_fluency: JudgingCriterionScore
    engagement_ted_style: JudgingCriterionScore

class JudgingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_pass: bool = Field(..., description="Whether the final speech is strong enough overall")
    overall_summary: str = Field(..., description="Short overall evaluation summary")

    criteria_scores: JudgingCriteriaScores

    total_score: int = Field(..., ge=5, le=25)
    max_score: int = Field(default=25)

    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggested_improvements: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_total_score(self):
        computed = (
            self.criteria_scores.task_audience_alignment.score
            + self.criteria_scores.narrative_coherence.score
            + self.criteria_scores.content_quality_credibility.score
            + self.criteria_scores.clarity_fluency.score
            + self.criteria_scores.engagement_ted_style.score
        )
        if self.total_score != computed:
            raise ValueError(
                f"total_score must equal the sum of all criterion scores ({computed})."
            )
        return self