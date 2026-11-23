"""Approach items must not invent dates (phase 4: "pilot go-live on October 15, 2024")."""

from pathlib import Path

from rfp_agent.agents import architect
from rfp_agent.agents.critic import deterministic_checks
from rfp_agent.dates import unsupported_dates
from rfp_agent.ingest import load_document
from rfp_agent.schemas import ApproachItem, Requirement, Risk

RFP = ("| Contract award | 31 March 2027 |\n"
       "The pilot go-live date of 30 June 2027 is fixed. Handover by 31 March 2028.")


def test_invented_dates_are_flagged():
    # The real failure from run eval-20261121-233403-1, item A50.
    assert unsupported_dates("Schedule a pilot go-live on October 15, 2024.", RFP) \
        == ["October 15, 2024"]
    # Earlier run eval-20261121-184341-1: a year the RFP never mentions.
    assert unsupported_dates("starting with a pilot go-live on March 2024", RFP) == ["2024"]
    # Right year, but a specific day the RFP does not state.
    assert unsupported_dates("Go live on 1 July 2027.", RFP) == ["1 July 2027"]


def test_rfp_dates_and_planning_language_pass():
    # Same date, different format.
    assert unsupported_dates("Pilot live by June 30, 2027.", RFP) == []
    assert unsupported_dates("Pilot live on 2027-06-30.", RFP) == []
    # Coarser planning within years the RFP covers is a plan, not a fact.
    assert unsupported_dates("Phased handover starting in Q4 2027, complete by March 2028.",
                             RFP) == []
    assert unsupported_dates("Rollout in August 2027.", RFP) == []
    # Numbers that are not dates.
    assert unsupported_dates("Sustain 2500 claims per day with 99.5% availability.", RFP) == []


def _req(id, priority="must"):
    return Requirement(id=id, title=id, description=id, category="timeline", priority=priority,
                       source_section="S03", source_quote="q", confidence=0.9)


def test_architect_group_check_asks_for_a_fix():
    reqs = [_req("TL-01")]
    item = ApproachItem(requirement_ids=["TL-01"], summary="Pilot go-live on October 15, 2024.",
                        rationale="r")
    problems = architect.check_group_answer([item], reqs, {"TL-01"}, 12, RFP)
    assert any("October 15, 2024" in p for p in problems)
    # Without the RFP text the check is skipped (backwards compatible).
    assert architect.check_group_answer([item], reqs, {"TL-01"}, 12) == []


def test_critic_blocks_invented_dates_and_routes_to_design():
    doc = load_document(Path(__file__).parent / "fixtures" / "mini_rfp.md")
    reqs = [Requirement(id="TL-01", title="t", description="d", category="timeline",
                        priority="must", source_section="S03",
                        source_quote="The pilot must go live by 30 June.", confidence=0.9)]
    risks = [Risk(id="R-01", title="t", description="d", category="ambiguity",
                  likelihood="low", impact="low", mitigation="m", related_requirement_ids=[])]
    bad = [ApproachItem(requirement_ids=["TL-01"], summary="Go live on 15 October 2024.",
                        rationale="r")]
    issues = [i for i in deterministic_checks(doc, reqs, bad, risks)
              if i.check == "approach_dates"]
    assert len(issues) == 1
    assert issues[0].severity == "high" and issues[0].target_node == "design_approach"
    assert "TL-01" in issues[0].feedback  # so feedback reaches the right workstream group
