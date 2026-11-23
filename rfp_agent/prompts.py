"""Prompt loader.

Each agent has one file in ``prompts/<name>.md``::

    ---
    name: extract_requirements
    version: "1.0.0"
    purpose: ...
    notes: ...why the prompt is shaped this way...
    ---
    ### SYSTEM
    ...jinja2 template...
    ### USER
    ...jinja2 template...

``version`` is recorded on every traced LLM call, so outputs are attributable to an
exact prompt revision. Templates use Jinja2 with ``StrictUndefined`` so a missing
variable fails loudly instead of silently rendering an empty string.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from jinja2 import Environment, StrictUndefined

_env = Environment(undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True,
                   keep_trailing_newline=False)
_SPLIT = re.compile(r"^###\s+(SYSTEM|USER)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    purpose: str
    system_template: str
    user_template: str

    def render(self, **kwargs) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": _env.from_string(self.system_template).render(**kwargs).strip()},
            {"role": "user", "content": _env.from_string(self.user_template).render(**kwargs).strip()},
        ]


def parse_prompt(text: str) -> Prompt:
    if not text.startswith("---"):
        raise ValueError("prompt file must start with YAML front-matter")
    _, fm, body = text.split("---", 2)
    meta = yaml.safe_load(fm)
    parts = _SPLIT.split(body)
    # parts = [preamble, "SYSTEM", system_body, "USER", user_body]
    blocks = {parts[i]: parts[i + 1] for i in range(1, len(parts) - 1, 2)}
    if set(blocks) != {"SYSTEM", "USER"}:
        raise ValueError(f"prompt {meta.get('name')} needs '### SYSTEM' and '### USER' blocks")
    return Prompt(name=meta["name"], version=str(meta["version"]), purpose=meta.get("purpose", ""),
                  system_template=blocks["SYSTEM"], user_template=blocks["USER"])


@lru_cache(maxsize=None)
def load_prompt(name: str, prompts_dir: str | Path) -> Prompt:
    path = Path(prompts_dir) / f"{name}.md"
    return parse_prompt(path.read_text(encoding="utf-8"))
