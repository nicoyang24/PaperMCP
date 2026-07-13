from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class Paper:
    path: Path
    title: str
    authors: str
    pages: int
    text: str
    sections: dict[str, str]


SECTION_RE = re.compile(
    r"(?im)^(?:\d+(?:\.\d+)*[.\s]+)?(abstract|摘要|introduction|引言|背景|"
    r"related work|相关工作|method(?:ology)?|方法|experiment(?:s)?|实验|results?|结果|"
    r"discussion|讨论|conclusion(?:s)?|结论|references|参考文献)\s*$"
)


def _clean(text: str) -> str:
    text = text.replace("\x00", "").replace("\r", "\n")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def split_sections(text: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(text))
    if not matches:
        return {"正文": text}
    result: dict[str, str] = {}
    if matches[0].start() > 0:
        result["文首信息"] = text[: matches[0].start()].strip()
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        if body:
            name = match.group(1).strip()
            result[name] = body
    return result or {"正文": text}


def parse_pdf(pdf_path: str, max_pages: int = 100) -> Paper:
    path = Path(pdf_path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise ValueError(f"PDF 文件不存在或格式不正确: {path}")
    if max_pages < 1 or max_pages > 1000:
        raise ValueError("max_pages 必须在 1 到 1000 之间")
    try:
        reader = PdfReader(path)
        page_count = len(reader.pages)
        texts = [(page.extract_text() or "") for page in reader.pages[:max_pages]]
    except Exception as exc:
        raise ValueError(f"无法解析 PDF（可能已加密或文件损坏）: {exc}") from exc
    text = _clean("\n\n".join(texts))
    if not text:
        raise ValueError("PDF 中未提取到文字；扫描版论文请先进行 OCR")
    metadata = reader.metadata or {}
    title = str(metadata.get("/Title") or "").strip()
    authors = str(metadata.get("/Author") or "").strip()
    first_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not title and first_lines:
        title = first_lines[0][:200]
    return Paper(path, title or path.stem, authors, page_count, text, split_sections(text))


def important_sentences(text: str, limit: int = 5) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[。！？.!?])\s+|\n+", text) if 30 <= len(s.strip()) <= 500]
    if not sentences:
        return [text[:500].strip()] if text.strip() else []
    words = re.findall(r"[A-Za-z]{3,}|[\u4e00-\u9fff]{2,}", text.lower())
    stop = {"the", "and", "that", "with", "this", "from", "for", "are", "was", "were", "本文", "我们", "研究"}
    frequencies = Counter(word for word in words if word not in stop)
    scored = []
    for pos, sentence in enumerate(sentences):
        tokens = re.findall(r"[A-Za-z]{3,}|[\u4e00-\u9fff]{2,}", sentence.lower())
        score = sum(frequencies[token] for token in tokens) / max(len(tokens), 1)
        scored.append((score, pos, sentence))
    chosen = sorted(sorted(scored, reverse=True)[:limit], key=lambda item: item[1])
    return [item[2] for item in chosen]

