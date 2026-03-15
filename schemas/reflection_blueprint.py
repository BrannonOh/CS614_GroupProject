from pydantic import BaseModel, Field
from typing import List, Optional

class ItemIssue(BaseModel):
    item: str = Field(description="The original required item from the reference JSON.")
    issue: str = Field(description="What is wrong with how this item appears in the script.")

class TedSectionIssue(BaseModel):
    id: str
    purpose: Optional[str] = None
    narrative_role: Optional[str] = None
    must_include_facts: Optional[List[ItemIssue]] = None
    must_include_points: Optional[List[ItemIssue]] = None
    transition_out: Optional[str] = None
    word_budget: Optional[str] = None

class HookIssue(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None

class ContentIssues(BaseModel):
    model_config = {"extra": "forbid"}
    hook: Optional[HookIssue] = None
    big_idea: Optional[str] = None
    ted_sections: Optional[List[TedSectionIssue]] = None

class StyleIssues(BaseModel):
    model_config = {"extra": "forbid"}
    argument_structure: Optional[List[ItemIssue]] = None
    audience_relationship: Optional[List[ItemIssue]] = None
    avoid: Optional[List[ItemIssue]] = None
    lexical_preferences: Optional[List[ItemIssue]] = None
    rhetorical_devices: Optional[List[ItemIssue]] = None
    syntax: Optional[List[ItemIssue]] = None
    tone: Optional[List[ItemIssue]] = None

class ReflectionBlueprint(BaseModel):
    model_config = {"extra": "forbid"}
    content_issues: ContentIssues = Field(default_factory=ContentIssues)
    style_issues: StyleIssues = Field(default_factory=StyleIssues)