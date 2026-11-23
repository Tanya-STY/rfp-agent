"""Pydantic v2 schemas.

Two families of models live here:

* **Domain models** (Requirement, ApproachItem, Risk, ..., SolutionSummary) - the
  validated output of the whole pipeline, written to ``summary.json``.
* **LLM output models** (``*Draft`` / ``*Output``) - deliberately smaller shapes that
  the model is asked to produce. Fields the code can fill deterministically (ids,
  section ids after verification, metadata) are NOT asked of the model: fewer output
  tokens means faster runs on small local hardware and fewer chances to hallucinate.

The JSON schema of each LLM output model is passed to Ollama's ``format`` parameter,
which constrains decoding to that schema.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RequirementCategory = Literal[
    "functional", "non_functional", "security_compliance", "integration", "commercial", "timeline"
]
Priority = Literal["must", "should", "could"]
Level = Literal["low", "medium", "high"]
RiskCategory = Literal[
    "delivery",
    "technical",
    "security_compliance",
    "integration",
    "commercial",
    "operational",
    "requirement_conflict",
    "ambiguity",
]
NodeName = Literal["extract_requirements", "design_approach", "analyze_risks"]

# Category -> id prefix used when the code assigns requirement ids.
CATEGORY_PREFIX: dict[str, str] = {
    "functional": "FR",
    "non_functional": "NFR",
    "security_compliance": "SEC",
    "integration": "INT",
    "commercial": "COM",
    "timeline": "TL",
}


# ======================================================================================
# Domain models
# ======================================================================================


class Requirement(BaseModel):
    id: str = Field(description="Stable id assigned by code, e.g. FR-03")
    title: str
    description: str
    category: RequirementCategory
    priority: Priority
    source_section: str = Field(description="Section id the requirement was extracted from")
    source_quote: str = Field(description="Verbatim text copied from the RFP")
    confidence: float = Field(ge=0.0, le=1.0)
    quote_match_score: float | None = Field(
        default=None, description="0-100 grounding score from quote_in_source (set by code)"
    )


class ApproachItem(BaseModel):
    requirement_ids: list[str]
    summary: str
    components: list[str] = Field(default_factory=list)
    rationale: str


class Risk(BaseModel):
    id: str
    title: str
    description: str
    category: RiskCategory
    likelihood: Level
    impact: Level
    mitigation: str
    related_requirement_ids: list[str] = Field(default_factory=list)
    source_quote: str | None = None


class Assumption(BaseModel):
    statement: str
    rationale: str = ""


class OpenQuestion(BaseModel):
    question: str
    reason: str = ""
    related_requirement_ids: list[str] = Field(default_factory=list)
    raised_by: str = ""  # node that raised it (set by code)


class CriticIssue(BaseModel):
    severity: Level
    target_node: NodeName
    feedback: str
    related_ids: list[str] = Field(default_factory=list)
    check: str = Field(default="llm_review", description="Name of the check that raised it")
    # Where the extractor should look again on revision (set by deterministic checks).
    section_id: str | None = None
    passage: str | None = None


class CriticReport(BaseModel):
    passed: bool
    issues: list[CriticIssue] = Field(default_factory=list)
    revision: int = 0

    def blocking(self) -> list[CriticIssue]:
        return [i for i in self.issues if i.severity == "high"]


class DroppedRequirement(BaseModel):
    requirement: Requirement
    reason: str


class RunMetadata(BaseModel):
    run_id: str
    input_file: str
    model: str
    embed_model: str
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    started_at: datetime
    finished_at: datetime | None = None
    revisions: int = 0
    critic_passed: bool = False
    critic_history: list[CriticReport] = Field(default_factory=list)
    dropped_requirements: list[DroppedRequirement] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    usage: dict[str, float] = Field(default_factory=dict)


class SolutionSummary(BaseModel):
    executive_summary: str
    requirements: list[Requirement]
    approach: list[ApproachItem]
    risks: list[Risk]
    assumptions: list[Assumption] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)
    metadata: RunMetadata


# ======================================================================================
# LLM output models (what each agent is asked to emit)
# ======================================================================================


class RequirementDraft(BaseModel):
    title: str = Field(description="Short name, max 8 words")
    description: str = Field(description="One sentence restating the requirement")
    category: RequirementCategory
    priority: Priority
    section_id: str = Field(description="Id of the section the quote was copied from")
    source_quote: str = Field(description="Exact sentence copied character-for-character")
    confidence: float = Field(ge=0.0, le=1.0)


class QuestionDraft(BaseModel):
    question: str
    reason: str = ""


class ExtractionOutput(BaseModel):
    requirements: list[RequirementDraft]
    open_questions: list[QuestionDraft] = Field(default_factory=list)


class DesignStep(BaseModel):
    """One step of the solution architect's bounded tool loop.

    ``action == "search"`` -> code runs ``search_rfp(query)`` and feeds results back.
    ``action == "final"``  -> ``approach`` / ``assumptions`` are the final answer.
    """

    action: Literal["search", "final"]
    query: str = ""
    approach: list[ApproachItem] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)


class RiskDraft(BaseModel):
    title: str
    description: str
    category: RiskCategory
    likelihood: Level
    impact: Level
    mitigation: str
    related_requirement_ids: list[str] = Field(default_factory=list)
    source_quote: str | None = None


class RiskOutput(BaseModel):
    risks: list[RiskDraft]
    open_questions: list[QuestionDraft] = Field(default_factory=list)


class CriticLLMIssue(BaseModel):
    severity: Level
    target_node: NodeName
    feedback: str
    related_ids: list[str] = Field(default_factory=list)


class CriticLLMReview(BaseModel):
    issues: list[CriticLLMIssue] = Field(default_factory=list)


class ExecutiveSummaryOutput(BaseModel):
    executive_summary: str = Field(
        description="3-5 sentence summary of the client need and proposed response"
    )
