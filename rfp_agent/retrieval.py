"""Tiny local vector index + deterministic grounding check.

* ``VectorIndex``: embeddings from ``nomic-embed-text`` (via the LLMClient), stored as a
  normalised numpy matrix, cached to ``.cache/<doc-sha>-<model>.npz``; cosine top-k.
  A few hundred chunks need no vector DB - numpy keeps it inspectable and dependency-light.
* ``quote_in_source``: checks a model-supplied "verbatim" quote really appears in the
  RFP. Exact match after normalisation (case, whitespace, punctuation, smart quotes)
  scores 100; otherwise a rapidfuzz ``partial_ratio`` fallback scores the best-aligned
  window. ``snap_quote`` returns the exact source span so near-misses (a dropped comma,
  "shall" vs "should" is NOT a near-miss at 90+) can be repaired deterministically.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rapidfuzz import fuzz

from .ingest import Chunk

# nomic-embed-text is trained with task prefixes; using them measurably helps retrieval.
DOC_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "
CLUSTER_PREFIX = "clustering: "


def _unit(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.clip(norms, 1e-12, None)


class VectorIndex:
    def __init__(self, chunks: list[Chunk], matrix: np.ndarray):
        self.chunks = chunks
        self.matrix = _unit(matrix.astype(np.float32))

    @classmethod
    def build(cls, chunks: list[Chunk], client, cache_dir: Path | None = None,
              doc_sha: str = "", model: str = "") -> "VectorIndex":
        cache = None
        if cache_dir is not None and doc_sha:
            safe_model = re.sub(r"[^A-Za-z0-9_.-]", "_", model)
            cache = Path(cache_dir) / f"{doc_sha}-{safe_model}.npz"
            if cache.exists():
                data = np.load(cache, allow_pickle=False)
                cached_ids = json.loads(str(data["ids"]))
                if cached_ids == [c.id for c in chunks]:
                    return cls(chunks, data["matrix"])
        vectors = client.embed([DOC_PREFIX + f"{c.section_title}\n{c.text}" for c in chunks],
                               node_name="ingest")
        matrix = np.asarray(vectors, dtype=np.float32)
        if cache is not None:
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, matrix=matrix, ids=json.dumps([c.id for c in chunks]))
        return cls(chunks, matrix)

    def search(self, query: str, client, k: int = 4, node_name: str = "retrieval"
               ) -> list[tuple[Chunk, float]]:
        return self.search_many([query], client, k, node_name)[0]

    def search_many(self, queries: list[str], client, k: int = 4, node_name: str = "retrieval"
                    ) -> list[list[tuple[Chunk, float]]]:
        """Top-k per query, with all queries embedded in a single call."""
        q = _unit(np.asarray(client.embed([QUERY_PREFIX + x for x in queries],
                                          node_name=node_name), dtype=np.float32))
        scores = q @ self.matrix.T  # (n_queries, n_chunks)
        return [[(self.chunks[i], float(row[i])) for i in np.argsort(-row)[:k]]
                for row in scores]


def cosine_matrix(vectors: list[list[float]]) -> np.ndarray:
    m = _unit(np.asarray(vectors, dtype=np.float32))
    return m @ m.T


# ------------------------------------------------------------------------------------------
# Grounding check
# ------------------------------------------------------------------------------------------

_PUNCT_MAP = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                            "–": "-", "—": "-"})


def normalize_for_match(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).translate(_PUNCT_MAP).lower()
    s = re.sub(r"[*_`#>|]", " ", s)  # markdown decoration
    s = re.sub(r"[^\w\s]", " ", s)  # punctuation -> space
    return re.sub(r"\s+", " ", s).strip()


MIN_QUOTE_WORDS = 4


@dataclass
class QuoteMatch:
    score: float  # 0-100
    exact: bool  # exact match after normalisation
    matched_text: str | None = None  # best-aligned span of the ORIGINAL source text

    def ok(self, threshold: float = 90.0) -> bool:
        return self.score >= threshold


def quote_in_source(quote: str, source: str, threshold: float = 90.0) -> QuoteMatch:
    """Is ``quote`` (approximately) a verbatim substring of ``source``?"""
    nq, ns = normalize_for_match(quote), normalize_for_match(source)
    if not nq:
        return QuoteMatch(0.0, False)
    # A 1-3 word "quote" ("the solution shall") proves nothing even if it matches.
    too_short = len(nq.split()) < MIN_QUOTE_WORDS
    if nq in ns:
        return QuoteMatch(80.0 if too_short else 100.0, True, _locate(quote, source))
    # Fuzzy fallback: best partial alignment of the quote against the source.
    score = float(fuzz.partial_ratio(nq, ns))
    # partial_ratio over-rewards short strings, which align somewhere by chance.
    if too_short or len(nq) < 25:
        score = min(score, 80.0)
    return QuoteMatch(score, False, _locate(quote, source) if score >= threshold else None)


def _locate(quote: str, source: str) -> str | None:
    """Return the exact span of ``source`` that best aligns with ``quote``."""
    res = fuzz.partial_ratio_alignment(quote, source)
    if res is None:
        return None
    start, end = res.dest_start, res.dest_end
    # widen to whole words so we never return "he solution" for "The solution"
    while start > 0 and source[start - 1].isalnum():
        start -= 1
    while end < len(source) and source[end].isalnum():
        end += 1
    span = source[start:end].strip()
    return span or None


def snap_quote(quote: str, source: str, threshold: float = 90.0) -> tuple[str, QuoteMatch]:
    """If the quote is a near-verbatim match, replace it with the exact source span."""
    m = quote_in_source(quote, source, threshold)
    if m.ok(threshold) and m.matched_text and m.matched_text != quote.strip():
        # Only snap when the snapped span itself verifies (guards bad alignments).
        if quote_in_source(m.matched_text, source).exact:
            return m.matched_text, m
    return quote, m
