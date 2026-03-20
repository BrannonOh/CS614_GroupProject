import json
import os
import time
import traceback
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, TypedDict

from pydantic import BaseModel, Field

class WeakClaim(BaseModel):
    section_id: str
    field_name: str
    claim_type: Literal["fact", "point"]
    original_text: str
    reason: str
    search_queries: List[str] = Field(default_factory=list)


class ContentSectionPlan(BaseModel):
    section_id: str
    weak_claims: List[WeakClaim] = Field(default_factory=list)


class ContentBlueprint(BaseModel):
    section_plans: List[ContentSectionPlan]
    content_feedback: str


class EvidenceCandidate(BaseModel):
    snippet: str
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    published_date: Optional[str] = None
    tavily_score: float = 0.0
    relevance_score: float = 0.0
    usefulness_score: float = 0.0
    combined_score: float = 0.0
    feedback: Optional[str] = None


class ResearchItem(BaseModel):
    section_id: str
    field_name: str
    claim_type: Literal["fact", "point"]
    original_text: str
    query: str
    top_evidence: List[EvidenceCandidate] = Field(default_factory=list)


class ResearchBlueprint(BaseModel):
    research_results: List[ResearchItem]
    research_feedback: str


class Citation(BaseModel):
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    published_date: Optional[str] = None
    query: Optional[str] = None


class FactCitationMap(BaseModel):
    text: str
    citations: List[Citation] = Field(default_factory=list)
    added_by_grounding: bool = False


class PointCitationMap(BaseModel):
    text: str
    citations: List[Citation] = Field(default_factory=list)
    added_by_grounding: bool = False


class HookSchema(BaseModel):
    type: str
    description: str


class TedSectionGrounded(BaseModel):
    id: str
    narrative_role: str
    purpose: str
    must_include_facts: List[str]
    must_include_points: List[str]
    transition_out: Optional[str] = None
    word_budget: int

    fact_citations: List[FactCitationMap] = Field(default_factory=list)
    point_citations: List[PointCitationMap] = Field(default_factory=list)


class FinalOutputGrounded(BaseModel):
    hook: HookSchema
    big_idea: str
    ted_sections: List[TedSectionGrounded]


class GroundingBlueprint(BaseModel):
    grounding_feedback: str
    needs_retry: bool
    retry_reason: str
    final_output: FinalOutputGrounded