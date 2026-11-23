"""Gold label sets: hand-labelled requirements and planted risks for one RFP.

The file format is documented at the top of ``evals/gold/rfp_synthetic_main.yaml``.
Every gold requirement is a verbatim quote, so predictions are matched to gold by
*where their quotes sit in the RFP*, not by embedding similarity: deterministic, free,
and easy to explain ("these two quotes overlap by 80% of the shorter one").
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from ..schemas import Priority, RequirementCategory


class GoldRequirement(BaseModel):
    id: str
    kind: Literal["core", "optional"]
    priority: Priority
    alt_priority: list[Priority] = Field(default_factory=list)
    category: RequirementCategory
    quote: str
    aliases: list[str] = Field(default_factory=list)

    @property
    def spans(self) -> list[str]:
        return [self.quote, *self.aliases]

    def priority_ok(self, p: str) -> bool:
        return p == self.priority or p in self.alt_priority


class GoldRisk(BaseModel):
    id: str
    kind: Literal["trap", "expected"]
    description: str
    where: Literal["risks", "risks_or_questions"] = "risks"
    all_of: list[str]
    cites: list[str] = Field(default_factory=list)


class GoldSet(BaseModel):
    document: str
    status: str = "draft"
    requirements: list[GoldRequirement]
    risks: list[GoldRisk] = Field(default_factory=list)
    priority_traps: dict[str, Priority] = Field(default_factory=dict)
    buried: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)  # for the LLM judge
    # Regexes that must not appear in any requirement or approach item (injection check).
    forbidden: list[str] = Field(default_factory=list)

    def by_id(self) -> dict[str, GoldRequirement]:
        return {g.id: g for g in self.requirements}


def load_gold(path: str | Path) -> GoldSet:
    gold = GoldSet.model_validate(yaml.safe_load(Path(path).read_text()))
    ids = [g.id for g in gold.requirements]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"duplicate gold ids: {sorted(dupes)}")
    known = set(ids)
    for ref in [*gold.priority_traps, *gold.buried, *(c for r in gold.risks for c in r.cites)]:
        if ref not in known:
            raise ValueError(f"gold file references unknown requirement id {ref!r}")
    return gold


def gold_path_for(input_file: str, gold_dir: Path) -> Path:
    """Default gold file for an input: evals/gold/<input stem>.yaml."""
    return gold_dir / f"{Path(input_file).stem}.yaml"
