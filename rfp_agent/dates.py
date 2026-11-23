"""Check that dates the model writes are supported by the RFP.

Approach items have no verbatim quote to check, so a model can invent a date that looks
plausible (main RFP run: "Schedule a pilot go-live on October 15, 2024" when the RFP fixes
the pilot at 30 June 2027 and awards the contract in March 2027). This catches that kind
of error in code, the same way quotes are checked for requirements.

Rule, kept loose so that legitimate planning is not blocked:
* a date's **year** must appear in the RFP ("Q4 2027" or "August 2027" is fine if the RFP
  mentions 2027);
* a date with a **day** ("15 October 2024", "October 15, 2024") must match a full date in
  the RFP, because a specific day is a fact, not a plan.
"""

from __future__ import annotations

import re

_MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
           "september", "october", "november", "december"]
_MON = {m[:3]: i + 1 for i, m in enumerate(_MONTHS)}
_M = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|" \
     r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
_YEAR = r"((?:19|20)\d{2})"
_DMY = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{_M},?\s+{_YEAR}\b", re.I)
_MDY = re.compile(rf"\b{_M}\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+{_YEAR}\b", re.I)
_ISO = re.compile(rf"\b{_YEAR}-(\d{{2}})-(\d{{2}})\b")
_YEAR_ONLY = re.compile(rf"\b{_YEAR}\b")


def _full_dates(text: str) -> list[tuple[str, tuple[int, int, int]]]:
    """(as written, (year, month, day)) for every day-precise date."""
    out = []
    for m in _DMY.finditer(text):
        out.append((m.group(0), (int(m.group(3)), _MON[m.group(2)[:3].lower()], int(m.group(1)))))
    for m in _MDY.finditer(text):
        out.append((m.group(0), (int(m.group(3)), _MON[m.group(1)[:3].lower()], int(m.group(2)))))
    for m in _ISO.finditer(text):
        out.append((m.group(0), (int(m.group(1)), int(m.group(2)), int(m.group(3)))))
    return out


def unsupported_dates(text: str, source: str) -> list[str]:
    """Dates in ``text`` that the RFP ``source`` does not support, as written."""
    src_full = {d for _, d in _full_dates(source)}
    src_years = {int(y) for y in _YEAR_ONLY.findall(source)}
    bad: list[str] = []
    for written, (y, mo, d) in _full_dates(text):
        if (y, mo, d) not in src_full and written not in bad:
            bad.append(written)
    covered = " ".join(w for w, _ in _full_dates(text))
    for y in _YEAR_ONLY.findall(text):
        if int(y) not in src_years and y not in covered and y not in bad:
            bad.append(y)
    return bad
