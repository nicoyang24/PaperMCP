from pathlib import Path

from paper_mcp.paper import Paper, important_sentences, split_sections
from paper_mcp.report import build_offline_report


def test_split_sections() -> None:
    text = "Title\n\nAbstract\nThis is a sufficiently long abstract sentence for extraction.\n\n1 Introduction\nThis introduction sentence explains the research problem in enough detail."
    sections = split_sections(text)
    assert "Abstract" in sections
    assert "Introduction" in sections


def test_sentence_limit() -> None:
    text = "First sufficiently descriptive sentence about a scientific method. Second sufficiently descriptive sentence about its experimental result."
    assert len(important_sentences(text, 1)) == 1


def test_report_contains_metadata() -> None:
    paper = Paper(Path("paper.pdf"), "Test Paper", "A. Author", 3, "A sufficiently long sentence describing the main result of this paper.", {"正文": "A sufficiently long sentence describing the main result of this paper."})
    report = build_offline_report(paper)
    assert "Test Paper" in report
    assert "A. Author" in report
    assert "分章节要点" in report

