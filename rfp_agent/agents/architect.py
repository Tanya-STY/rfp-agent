"""Solution-architect agent with a bounded retrieval tool loop.

Instead of native function-calling (unreliable on 7B local models), each turn the model
returns a ``DesignStep`` JSON object whose ``action`` is either ``search`` (we run
``search_rfp`` and append the results) or ``final``. Searches share a budget of
``max_tool_calls`` across the whole node; once it is spent the model is told to answer.
Every step is a normal traced ``chat_structured`` call.

Requirements are designed in workstream groups (functional / platform qualities /
security+integration / delivery+commercial), one bounded loop per group, because a 7B
model asked to place 80+ ids in one answer produces a single catch-all item or runs out
of output tokens (failure log F6, F9, F12).
"""

from __future__ import annotations

import logging
import re

from ..context import RunContext
from ..dates import unsupported_dates
from ..llm import OutputTruncatedError, StructuredOutputError
from ..schemas import ApproachItem, Assumption, DesignStep, Requirement

log = logging.getLogger("rfp_agent")
NODE = "design_approach"


def search_rfp(ctx: RunContext, query: str, k: int = 3) -> str:
    """The tool: top-k RFP chunks for a query, formatted for the model."""
    hits = ctx.search(query, k=k, node=NODE)
    ctx.tracer.event("tool_call", tool="search_rfp", query=query,
                     hits=[(c.id, round(s, 3)) for c, s in hits])
    body = "\n\n".join(f"[{c.section_id}] {c.section_title}\n{c.text}" for c, _ in hits)
    return f"<search_results query={query!r}>\n{body}\n</search_results>"


# Workstream groups (failure log F6/F12): a 7B model cannot hold 80+ ids in one answer,
# so the architect designs one group at a time and the results are concatenated.
GROUPS: list[tuple[str, tuple[str, ...]]] = [
    ("Core functional capabilities", ("functional",)),
    ("Platform qualities: performance, availability, scalability, operations",
     ("non_functional",)),
    ("Security, compliance, hosting and integration", ("security_compliance", "integration")),
    ("Delivery, team, timeline and commercials", ("commercial", "timeline")),
]


def group_requirements(requirements: list[Requirement], max_per_group: int
                       ) -> list[tuple[str, list[Requirement]]]:
    groups = []
    for name, cats in GROUPS:
        members = [r for r in requirements if r.category in cats]
        for i in range(0, len(members), max_per_group):  # very large groups are chunked
            part = members[i:i + max_per_group]
            suffix = f" (part {i // max_per_group + 1})" if len(members) > max_per_group else ""
            groups.append((name + suffix, part))
    return [(n, m) for n, m in groups if m]


def design(ctx: RunContext, requirements: list[Requirement], feedback: list[str] | None = None
           ) -> tuple[list[ApproachItem], list[Assumption]]:
    valid = {r.id for r in requirements}
    budget = [ctx.settings.max_tool_calls]  # shared search budget across all groups
    approach: list[ApproachItem] = []
    assumptions: list[Assumption] = []
    groups = group_requirements(requirements, ctx.settings.max_requirements_per_design_call)
    for i, (name, members) in enumerate(groups, 1):
        log.info("  architect group %d/%d: %s (%d requirements)", i, len(groups), name,
                 len(members))
        items, assumed = _design_group(ctx, name, members,
                                       feedback_for_group(feedback or [], members), budget, valid)
        approach += items
        assumptions += assumed
    seen: set[str] = set()
    unique_assumptions = []
    for a in assumptions:
        if a.statement.lower() not in seen:
            seen.add(a.statement.lower())
            unique_assumptions.append(a)
    return approach, unique_assumptions[:8]


_ID = r"[A-Z]{2,5}-\d{1,3}"
_ID_LIST = re.compile(rf"{_ID}(?:,\s*{_ID})*")


def feedback_for_group(feedback: list[str], requirements: list[Requirement]) -> list[str]:
    """Critic feedback relevant to one workstream group (failure log F16).

    Feedback naming requirement ids is kept only if it names ids of this group, and id
    lists are cut down to this group's ids. Passing the whole node's feedback to every
    group made each group stuff all ~30 missing ids into one catch-all item.
    """
    mine = {r.id for r in requirements}
    out = []
    for f in feedback:
        ids = set(re.findall(_ID, f))
        if not ids:
            out.append(f)
        elif ids & mine:
            out.append(_ID_LIST.sub(
                lambda m: ", ".join(i for i in re.findall(_ID, m.group(0)) if i in mine) or "-", f))
    return out


def check_group_answer(items: list[ApproachItem], requirements: list[Requirement],
                       valid: set[str], max_ids: int, source: str | None = None) -> list[str]:
    """Deterministic per-group checks, so problems are fixed inside the group's loop
    instead of costing a whole critic revision (failure log F16).

    With ``source`` (the RFP text), dates in an item must be supported by the RFP
    (phase 4: the model invented "pilot go-live on October 15, 2024")."""
    problems = []
    covered = {i for a in items for i in a.requirement_ids}
    missing = [r.id for r in requirements if r.priority == "must" and r.id not in covered]
    if missing:
        problems.append(f"These must ids are not in any item: {', '.join(missing)}. "
                        "Add each to the item it belongs to.")
    for n, a in enumerate(items, 1):
        if len(a.requirement_ids) > max_ids:
            problems.append(f"Item {n} lists {len(a.requirement_ids)} ids; split it into "
                            f"focused items of at most {max_ids} ids.")
    unknown = sorted({i for i in covered if i not in valid})
    if unknown:
        problems.append(f"Unknown ids {', '.join(unknown)}: use only ids from the list.")
    if source is not None:
        for n, a in enumerate(items, 1):
            bad = unsupported_dates(f"{a.summary} {a.rationale}", source)
            if bad:
                problems.append(f"Item {n} uses dates the RFP does not state ({', '.join(bad)}). "
                                "Use the RFP's own dates, or describe timing without a date.")
    return problems


def _design_group(ctx: RunContext, group: str, requirements: list[Requirement],
                  feedback: list[str], budget: list[int], valid: set[str] | None = None
                  ) -> tuple[list[ApproachItem], list[Assumption]]:
    """Bounded tool loop for one workstream group."""
    valid = valid if valid is not None else {r.id for r in requirements}
    max_ids = ctx.settings.max_ids_per_approach_item
    prompt = ctx.prompt(NODE)
    must_ids = [r.id for r in requirements if r.priority == "must"]
    other_groups = [n for n, _ in GROUPS if not group.startswith(n)]
    messages = prompt.render(group=group, other_groups=other_groups, requirements=requirements,
                             feedback=feedback, must_ids=must_ids,
                             searches_left=budget[0],
                             max_ids_per_item=ctx.settings.max_ids_per_approach_item)
    step = None
    truncated_once = False
    corrected_once = False
    # searches + final + grace turn + one correction turn
    for _turn in range(ctx.settings.max_tool_calls + 3):
        try:
            step = ctx.client.chat_structured(messages, DesignStep, node_name=NODE,
                                              temperature=ctx.settings.temperature_design,
                                              prompt_version=prompt.version)
        except OutputTruncatedError:
            if truncated_once:
                break
            truncated_once = True
            # Answer too long (failure log F9): ask once more for a tighter answer.
            ctx.warn(f"architect answer for '{group}' truncated; asking for a shorter one")
            messages = messages + [{"role": "user", "content": (
                "Your answer was too long and was cut off. Reply with action \"final\" "
                f"and at most 3 items, each with at most {ctx.settings.max_ids_per_approach_item} "
                "requirement ids, a one-sentence summary and at most 3 components.")}]
            continue
        except StructuredOutputError as exc:
            ctx.warn(f"architect step for '{group}' failed: {exc}")
            break
        if step.action == "final":
            step = step.model_copy(update={"approach": [
                a.model_copy(update={"requirement_ids": normalize_ids(a.requirement_ids, valid)})
                for a in step.approach]})
            problems = check_group_answer(step.approach, requirements, valid, max_ids,
                                          ctx.doc.text if ctx.doc else None)
            if not problems or corrected_once or not step.approach:
                break
            corrected_once = True
            ctx.tracer.event("architect_correction", group=group, problems=problems)
            log.info("  architect correction for '%s': %s", group, "; ".join(problems))
            messages = messages + [
                {"role": "assistant", "content": step.model_dump_json()},
                {"role": "user", "content": "Fix these problems and reply with action \"final\" "
                 "and the complete corrected approach:\n- " + "\n- ".join(problems)}]
            continue
        messages = messages + [{"role": "assistant", "content": step.model_dump_json()}]
        if budget[0] > 0 and step.query.strip():
            budget[0] -= 1
            log.info("  architect search (%d left): %s", budget[0], step.query)
            messages.append({"role": "user", "content": search_rfp(ctx, step.query)
                             + "\nReply with your next step."})
        else:
            messages.append({"role": "user", "content": (
                "No searches left. Reply now with action \"final\" and the approach items.")})
    if step is None or step.action != "final" or not step.approach:
        ctx.warn(f"architect returned no approach for '{group}'")
        return [], []
    # Ids still unknown after the correction turn are dropped here, with a warning.
    # (Leaving them for the critic cost whole revisions and never got them fixed.)
    items = []
    for a in step.approach:
        unknown = [i for i in a.requirement_ids if i not in valid]
        if unknown:
            ctx.warn(f"architect used unknown requirement ids {unknown} in '{group}'; dropped")
        kept = [i for i in a.requirement_ids if i in valid]
        if kept:
            items.append(a.model_copy(update={"requirement_ids": kept}))
    return items, step.assumptions


def normalize_ids(ids: list[str], valid: set[str]) -> list[str]:
    """Repair unambiguous formatting variants ("fr-3", "FR3" -> "FR-03").

    Unknown ids are kept as-is on purpose: the critic flags them and routes feedback
    back to the agent, rather than code silently deleting the model's references.
    """
    out: list[str] = []
    for raw in ids:
        m = re.match(r"^\s*([A-Za-z]+)[\s_-]*0*(\d+)\s*$", raw)
        cand = f"{m.group(1).upper()}-{int(m.group(2)):02d}" if m else raw.strip()
        fixed = cand if cand in valid else raw.strip()
        if fixed not in out:
            out.append(fixed)
    return out
