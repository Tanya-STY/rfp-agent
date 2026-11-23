"""Tiny local review app for Tanya: label judge verdicts and review the gold sets.

    python evals/review/server.py      # then open http://localhost:8765

* Judgments: answers are written straight into the ``human`` field of the judgments
  file, which is what ``python -m rfp_agent eval --calibrate`` reads.
* Gold sets: answers are saved to ``evals/review/gold_review.json``; Claude applies them
  to the YAML files afterwards (so the YAML comments and layout are kept).
Standard library + PyYAML only; nothing leaves the machine.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
JUDGMENTS = ROOT / "evals/results/baseline-qwen7b-x3.judgments.jsonl"
GOLD_DIR = ROOT / "evals/gold"
GOLD_REVIEW = HERE / "gold_review.json"
SAMPLE_RUN = "eval-20261121-184341-1"
N_REQ, N_APP, N_RISK = 12, 4, 4


def _rows() -> list[dict]:
    return [json.loads(l) for l in JUDGMENTS.read_text().splitlines() if l.strip()]


def _write_rows(rows: list[dict]) -> None:
    JUDGMENTS.write_text("".join(json.dumps(r) + "\n" for r in rows))


def judgments_payload() -> dict:
    """Pick 20 judgments from one run (mixing yes and no verdicts) with the text judged."""
    rows = _rows()
    summary = json.loads((ROOT / "runs" / SAMPLE_RUN / "summary.json").read_text())
    reqs = {r["id"]: r for r in summary["requirements"]}
    risks = {r["id"]: r for r in summary["risks"]}
    gold = yaml.safe_load((GOLD_DIR / "rfp_synthetic_main.yaml").read_text())
    idx = [(i, r) for i, r in enumerate(rows) if r["run"] == SAMPLE_RUN]

    req = [x for x in idx if x[1]["kind"] == "requirement"]
    neg = [x for x in req if not all(x[1]["judge"].get(k, True) for k in ("faithful", "priority_ok"))]
    pos = [x for x in req if x not in neg]
    picked = sorted((neg[: N_REQ // 2] + pos)[:N_REQ], key=lambda x: x[0])
    picked += [x for x in idx if x[1]["kind"] == "approach"][:N_APP]
    picked += [x for x in idx if x[1]["kind"] == "risk"][:N_RISK]

    items = []
    for i, r in picked:
        if r["kind"] == "requirement":
            ctx = reqs.get(r["item"], {})
        elif r["kind"] == "approach":
            a = summary["approach"][int(r["item"][1:]) - 1]
            ctx = {**a, "constraints": gold.get("constraints", []),
                   "requirements": {k: reqs[k]["title"] for k in a["requirement_ids"] if k in reqs}}
        else:
            ctx = risks.get(r["item"], {})
        items.append({"index": i, "kind": r["kind"], "item": r["item"], "judge": r["judge"],
                      "human": r["human"], "ctx": ctx})
    return {"items": items, "file": str(JUDGMENTS.relative_to(ROOT))}


def gold_payload() -> dict:
    review = json.loads(GOLD_REVIEW.read_text()) if GOLD_REVIEW.exists() else {}
    files = []
    for p in sorted(GOLD_DIR.glob("*.yaml")):
        g = yaml.safe_load(p.read_text())
        files.append({"file": p.name, "document": g["document"],
                      "requirements": g["requirements"], "risks": g.get("risks", []),
                      "review": review.get(p.name, {})})
    return {"files": files}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj) -> None:
        self._send(200, json.dumps(obj).encode(), "application/json")

    def do_GET(self):  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/judgments":
            self._json(judgments_payload())
        elif self.path == "/api/gold":
            self._json(gold_payload())
        elif self.path.startswith("/rfp/"):
            p = (ROOT / self.path[5:]).resolve()
            if p.is_relative_to(ROOT) and p.suffix == ".md" and p.exists():
                self._send(200, p.read_bytes(), "text/plain; charset=utf-8")
            else:
                self._send(404, b"not found", "text/plain")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):  # noqa: N802
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/judgments":
            rows = _rows()
            rows[data["index"]]["human"] = data["human"]
            _write_rows(rows)
            self._json({"ok": True})
        elif self.path == "/api/gold":
            review = json.loads(GOLD_REVIEW.read_text()) if GOLD_REVIEW.exists() else {}
            f = review.setdefault(data["file"], {})
            if data["value"] is None:
                f.pop(data["key"], None)
            else:
                f[data["key"]] = data["value"]
            GOLD_REVIEW.write_text(json.dumps(review, indent=2) + "\n")
            self._json({"ok": True})
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, *args):  # keep the console quiet
        pass


if __name__ == "__main__":
    print("Review app on http://localhost:8765")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
