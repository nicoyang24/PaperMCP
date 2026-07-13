from __future__ import annotations

from datetime import datetime

from .paper import Paper, important_sentences


def build_offline_report(paper: Paper, summary_sentences: int = 4) -> str:
    lines = [
        f"# {paper.title}：论文汇总报告",
        "",
        "## 基本信息",
        "",
        f"- 标题：{paper.title}",
        f"- 作者：{paper.authors or 'PDF 元数据未提供'}",
        f"- 页数：{paper.pages}",
        f"- 文件：{paper.path}",
        f"- 生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "## 核心摘要（离线抽取式）",
        "",
    ]
    lines.extend(f"- {sentence}" for sentence in important_sentences(paper.text, summary_sentences))
    lines.extend(["", "## 分章节要点", ""])
    for name, content in paper.sections.items():
        if name.lower() in {"references", "参考文献"}:
            continue
        lines.extend([f"### {name}", ""])
        lines.extend(f"- {sentence}" for sentence in important_sentences(content, 3))
        lines.append("")
    lines.extend([
        "## 阅读提示",
        "",
        "此报告由 PDF 文本自动抽取生成，公式、图表和多栏排版可能无法完整还原；重要结论请回查原文。",
    ])
    return "\n".join(lines)

