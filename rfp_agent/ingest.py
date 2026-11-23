"""Document loading, normalisation and sectioning.

Any ``.md``/``.txt``, ``.pdf`` or ``.docx`` file is converted to normalised
markdown-ish text, then split into sections by headings. If no headings are found
(e.g. a flat PDF), we fall back to fixed-size chunks with overlap. Sections longer than
``max_chars`` are split into overlapping parts so each fits a small context window.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

from pydantic import BaseModel

SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt", ".pdf", ".docx"}


class Section(BaseModel):
    id: str  # e.g. "S05" or "S05.2" for the 2nd part of a long section
    title: str  # heading text, including parent heading for sub-sections
    level: int
    text: str  # body text (without the heading line)

    def render(self) -> str:
        return f"[{self.id}] {self.title}\n{self.text}"


class Chunk(BaseModel):
    id: str
    section_id: str
    section_title: str
    text: str


class Document(BaseModel):
    path: str
    text: str
    sections: list[Section]

    @property
    def sha(self) -> str:
        return hashlib.sha256(self.text.encode()).hexdigest()[:16]

    def section(self, section_id: str) -> Section | None:
        return next((s for s in self.sections if s.id == section_id), None)


# ------------------------------------------------------------------------------------------
# Loading
# ------------------------------------------------------------------------------------------


def find_input(path: str | Path) -> Path:
    """Accept a file, or a directory containing exactly one supported (non-README) file."""
    p = Path(path)
    if p.is_file():
        return p
    if p.is_dir():
        cands = sorted(f for f in p.iterdir()
                       if f.suffix.lower() in SUPPORTED_SUFFIXES and f.stem.lower() != "readme")
        if len(cands) == 1:
            return cands[0]
        raise ValueError(f"{p} contains {len(cands)} candidate inputs; pass one with --input")
    raise FileNotFoundError(p)


def load_text(path: str | Path) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in {".md", ".markdown", ".txt"}:
        raw = p.read_text(encoding="utf-8", errors="replace")
    elif suffix == ".pdf":
        raw = _load_pdf(p)
    elif suffix == ".docx":
        raw = _load_docx(p)
    else:
        raise ValueError(f"Unsupported input type: {suffix} (supported: {SUPPORTED_SUFFIXES})")
    return normalize_text(raw)


def _load_pdf(p: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(p))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(pages)
    # PDFs have no heading markup; promote lines that look like numbered headings
    # ("3. Scope of Work", "8.2 Data Residency") to markdown headings.
    out = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+(?:\.\d+)*)\.?\s+([A-Z][^.:;]{2,70})\s*$", line)
        if m and len(line.split()) <= 10:
            depth = m.group(1).count(".") + 2
            out.append(f"{'#' * min(depth, 4)} {line.strip()}")
        else:
            out.append(line)
    return "\n".join(out)


def _load_docx(p: Path) -> str:
    import docx  # python-docx

    d = docx.Document(str(p))
    lines: list[str] = []
    for para in d.paragraphs:
        style = (para.style.name or "").lower() if para.style is not None else ""
        txt = para.text.strip()
        if not txt:
            continue
        m = re.match(r"heading (\d)", style)
        if style == "title":
            lines.append(f"# {txt}")
        elif m:
            lines.append(f"{'#' * (int(m.group(1)) + 1)} {txt}")
        else:
            lines.append(txt)
    for table in d.tables:
        for row in table.rows:
            lines.append(" | ".join(c.text.strip() for c in row.cells))
    return "\n\n".join(lines)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ------------------------------------------------------------------------------------------
# Sectioning
# ------------------------------------------------------------------------------------------

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_RULE = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")


def split_sections(text: str, max_chars: int = 3500, overlap: int = 300) -> list[Section]:
    raw: list[tuple[int, str, list[str]]] = []  # (level, title, body lines)
    stack: list[tuple[int, str]] = []  # heading ancestry for titles like "3 > 3.1"
    preamble: list[str] = []
    for line in text.splitlines():
        if _RULE.match(line):
            continue
        m = _HEADING.match(line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            parent = stack[-1][1] if stack and level > 2 else None
            stack.append((level, title))
            raw.append((level, f"{parent} > {title}" if parent else title, []))
        elif raw:
            raw[-1][2].append(line)
        else:
            preamble.append(line)

    if not raw:  # no headings at all -> fixed-size fallback
        return [Section(id=f"S{i + 1:02d}", title=f"Chunk {i + 1}", level=1, text=t)
                for i, t in enumerate(_window(text, max_chars, overlap))]

    if "".join(preamble).strip():
        raw.insert(0, (1, "Preamble", preamble))

    sections: list[Section] = []
    n = 0
    for level, title, body_lines in raw:
        body = "\n".join(body_lines).strip()
        if not body:  # heading-only (e.g. "## 3. Scope" directly followed by "### 3.1")
            continue
        n += 1
        parts = _window(body, max_chars, overlap) if len(body) > max_chars else [body]
        for j, part in enumerate(parts):
            sid = f"S{n:02d}" if len(parts) == 1 else f"S{n:02d}.{j + 1}"
            sections.append(Section(id=sid, title=title, level=level, text=part))
    return sections


def _window(text: str, size: int, overlap: int) -> list[str]:
    """Split on paragraph boundaries into ~size-char windows with ~overlap carry-over."""
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    cur = ""
    for para in paras:
        while len(para) > size:  # a single giant paragraph: hard split
            head, para = para[:size], para[size - overlap:]
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(head)
        if cur and len(cur) + len(para) + 2 > size:
            chunks.append(cur)
            tail = cur[-overlap:] if overlap else ""
            # start the overlap at a word boundary
            cur = (tail[tail.find(" ") + 1:] + "\n\n" if " " in tail else "") + para
        else:
            cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        chunks.append(cur)
    return chunks


def chunk_for_retrieval(sections: list[Section], size: int = 900, overlap: int = 150) -> list[Chunk]:
    """Smaller, overlapping chunks for the vector index (more precise hits)."""
    chunks: list[Chunk] = []
    for s in sections:
        for i, t in enumerate(_window(s.text, size, overlap)):
            chunks.append(Chunk(id=f"{s.id}#{i + 1}", section_id=s.id, section_title=s.title,
                                text=t))
    return chunks


def load_document(path: str | Path, max_chars: int = 3500, overlap: int = 300) -> Document:
    p = find_input(path)
    text = load_text(p)
    return Document(path=str(p), text=text, sections=split_sections(text, max_chars, overlap))
