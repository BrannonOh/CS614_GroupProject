from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

# -----------------------------
# Shared small enums / helpers
# -----------------------------

ScoreValue = Literal[0, 1, 2]

CoverageStatus = Literal["full", "partial", "missing"]
StrengthStatus = Literal["strong", "adequate", "weak"]
BigIdeaStatus = Literal["aligned", "partially_aligned", "misaligned"]
ReadinessStatus = Literal["ready", "mostly_ready", "not_ready"]
WordBudgetStatus = Literal["aligned", "slightly_off", "misaligned"]

IssueSeverity = Literal["critical", "major", "minor"]
IssueCategory = Literal[
    "coverage",
    "narrative",
    "distinctiveness",
    "transition",
    "big_idea",
    "downstream_readiness",
    "word_budget",
]


# -----------------------------
# Section alignment models
# -----------------------------

class SectionAlignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    planner_section_id: str = Field(..., description="ID of the planner section, e.g. S1")
    planner_section_name: str = Field(..., description="Human-readable planner section name")
    mapped_ted_section_ids: List[str] = Field(
        default_factory=list,
        description="TED section IDs that implement this planner section, e.g. ['TS1'] or ['TS2', 'TS3']"
    )

    purpose_coverage: CoverageStatus = Field(
        ...,
        description="Whether the planner section purpose is fully, partially, or not covered"
    )
    points_coverage: CoverageStatus = Field(
        ...,
        description="Whether required points are fully, partially, or not covered"
    )
    facts_coverage: CoverageStatus = Field(
        ...,
        description="Whether required facts are fully, partially, or not covered"
    )

    missing_or_weakened_points: List[str] = Field(
        default_factory=list,
        description="Planner points that were omitted, weakened, or overly compressed"
    )
    missing_or_weakened_facts: List[str] = Field(
        default_factory=list,
        description="Planner facts that were omitted, weakened, or overly compressed"
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Short notes about section mapping or compression quality"
    )


# -----------------------------
# Criterion score models
# -----------------------------

class BaseCriterionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: ScoreValue = Field(..., description="0=weak/missing, 1=adequate/partial, 2=strong/full")
    notes: List[str] = Field(default_factory=list)

class StrengthCriterionScore(BaseCriterionScore):
    status: StrengthStatus

class BigIdeaCriterionScore(BaseCriterionScore):
    status: BigIdeaStatus

class ReadinessCriterionScore(BaseCriterionScore):
    status: ReadinessStatus

class WordBudgetCriterionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: WordBudgetStatus
    score: ScoreValue = Field(..., description="0=misaligned, 1=slightly_off, 2=aligned")
    target_word_count: int = Field(..., ge=0)
    ted_total_word_budget: int = Field(..., ge=0)
    notes: List[str] = Field(default_factory=list)

class CriteriaScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coverage_fidelity: StrengthCriterionScore
    narrative_coherence: StrengthCriterionScore
    section_distinctiveness: StrengthCriterionScore
    transition_quality: StrengthCriterionScore
    big_idea_alignment: BigIdeaCriterionScore
    downstream_readiness: ReadinessCriterionScore
    word_budget_sanity: WordBudgetCriterionScore

# -----------------------------
# Issues
# -----------------------------
class StructureIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: IssueSeverity
    category: IssueCategory
    planner_ref: str = Field(
        default="",
        description="Optional planner reference, e.g. S3, RP2, or blank if not applicable"
    )
    ted_ref: str = Field(
        default="",
        description="Optional TED reference, e.g. TS2, TS4, or blank if not applicable"
    )
    message: str = Field(..., description="Concise issue description")
    suggested_fix: str = Field(..., description="Concrete revision guidance")

# -----------------------------
# Top-level output
# -----------------------------
class StructureCheckOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_valid: bool = Field(
        ...,
        description="Whether the TED blueprint is structurally sound enough for downstream use"
    )
    overall_summary: str = Field(
        ...,
        description="Short overall assessment of the TED blueprint"
    )

    section_alignment: List[SectionAlignment] = Field(
        default_factory=list,
        description="Planner-to-TED mapping analysis for each planner section"
    )

    criteria_scores: CriteriaScores

    total_score: int = Field(..., ge=0, le=14)
    max_score: int = Field(default=14, ge=0)

    strengths: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    issues: List[StructureIssue] = Field(default_factory=list)
    suggested_fixes: List[str] = Field(default_factory=list)

    @field_validator("max_score")
    @classmethod
    def validate_max_score(cls, v: int) -> int:
        if v != 14:
            raise ValueError("max_score must be 14 for 7 criteria scored from 0 to 2.")
        return v

    @model_validator(mode="after")
    def validate_total_score(self):
        computed_total = (
            self.criteria_scores.coverage_fidelity.score
            + self.criteria_scores.narrative_coherence.score
            + self.criteria_scores.section_distinctiveness.score
            + self.criteria_scores.transition_quality.score
            + self.criteria_scores.big_idea_alignment.score
            + self.criteria_scores.downstream_readiness.score
            + self.criteria_scores.word_budget_sanity.score
        )

        if self.total_score != computed_total:
            raise ValueError(
                f"total_score must equal the sum of all criterion scores ({computed_total})."
            )

        return self