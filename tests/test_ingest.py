from pathlib import Path

import pytest

from rfp_agent.ingest import (
    chunk_for_retrieval,
    find_input,
    load_document,
    load_text,
    normalize_text,
    split_sections,
)

FIXTURES = Path(__file__).parent / "fixtures"
REPO = Path(__file__).parent.parent


def test_markdown_sections_by_heading():
    doc = load_document(FIXTURES / "mini_rfp.md")
    titles = [s.title for s in doc.sections]
    # The H1 has no body text, so it is skipped rather than producing an empty section.
    assert titles == ["1. Functional Requirements", "2. Security", "3. Timeline"]
    assert [s.id for s in doc.sections] == ["S01", "S02", "S03"]
    assert "FR-2 Search" in doc.sections[0].text


def test_subsection_titles_include_parent():
    text = "# T\n\n## 3. Scope\n\n### 3.1 In scope\n\nA.\n\n### 3.2 Out of scope\n\nB."
    secs = split_sections(text)
    assert [s.title for s in secs] == ["3. Scope > 3.1 In scope", "3. Scope > 3.2 Out of scope"]


def test_long_section_is_split_with_overlap():
    body = "\n\n".join(f"Paragraph {i} " + "word " * 60 for i in range(20))
    secs = split_sections(f"## Big\n\n{body}", max_chars=1000, overlap=100)
    assert len(secs) > 1
    assert all(s.id.startswith("S01.") for s in secs)
    assert all(len(s.text) <= 1100 for s in secs)


def test_fallback_chunks_when_no_headings():
    text = "\n\n".join("plain text " * 40 for _ in range(10))
    secs = split_sections(text, max_chars=800, overlap=100)
    assert len(secs) > 1 and secs[0].title == "Chunk 1"


def test_normalize_text():
    assert normalize_text("a\r\nb c  \n\n\n\nd") == "a\nb c\n\nd"


def test_docx_loading_maps_headings(tmp_path):
    docx = pytest.importorskip("docx")
    d = docx.Document()
    d.add_heading("Scope", level=1)
    d.add_paragraph("The system shall do X.")
    d.add_heading("Security", level=1)
    d.add_paragraph("Data must stay on-prem.")
    path = tmp_path / "rfp.docx"
    d.save(str(path))
    doc = load_document(path)
    assert [s.title for s in doc.sections] == ["Scope", "Security"]
    assert "on-prem" in load_text(path)


def test_find_input_directory_ignores_readme():
    assert find_input(REPO / "inputs").name == "rfp_synthetic_main.md"


def test_retrieval_chunks_keep_section_ids():
    doc = load_document(REPO / "inputs" / "rfp_synthetic_main.md")
    chunks = chunk_for_retrieval(doc.sections, size=900)
    assert {c.section_id for c in chunks} == {s.id for s in doc.sections}
    assert all(c.id.startswith(c.section_id + "#") for c in chunks)
