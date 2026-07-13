from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import SamplingMessage, TextContent

from .paper import parse_pdf
from .report import build_offline_report

mcp = FastMCP(
    "paper-report",
    instructions="解析指定的 PDF 学术论文，并生成结构化中文汇总报告。",
    json_response=True,
)


@mcp.tool()
def inspect_paper(pdf_path: str, max_pages: int = 100) -> dict[str, Any]:
    """解析本地 PDF，返回论文元数据、章节名与文本统计，不生成文件。"""
    paper = parse_pdf(pdf_path, max_pages)
    return {
        "title": paper.title,
        "authors": paper.authors,
        "total_pages": paper.pages,
        "parsed_pages": min(paper.pages, max_pages),
        "characters": len(paper.text),
        "sections": list(paper.sections),
    }


async def _llm_report(paper_text: str, title: str, ctx: Context) -> str:
    clipped = paper_text[:80_000]
    prompt = f"""请根据以下论文文本生成严谨的中文 Markdown 汇总报告。
必须包含：基本信息、研究问题、核心方法、数据/实验、主要结果、创新点、局限性、可复现性线索、结论。
不得编造文本中没有的信息，不确定处明确写“原文未明确说明”。论文标题：{title}

论文文本：
{clipped}"""
    result = await ctx.session.create_message(
        messages=[SamplingMessage(role="user", content=TextContent(type="text", text=prompt))],
        max_tokens=5000,
    )
    if getattr(result.content, "type", None) != "text":
        raise RuntimeError("MCP 客户端未返回文本类型的采样结果")
    return result.content.text


@mcp.tool()
async def generate_paper_report(
    pdf_path: str,
    ctx: Context,
    output_path: str | None = None,
    use_llm: bool = False,
    max_pages: int = 100,
) -> dict[str, Any]:
    """根据本地 PDF 生成中文 Markdown 汇总报告。use_llm=true 时请求 MCP 客户端模型深度总结。"""
    await ctx.info(f"正在解析论文: {pdf_path}")
    paper = parse_pdf(pdf_path, max_pages)
    await ctx.report_progress(progress=0.45, total=1.0, message="PDF 文本解析完成")
    report = await _llm_report(paper.text, paper.title, ctx) if use_llm else build_offline_report(paper)
    saved_to = None
    if output_path:
        target = Path(output_path).expanduser().resolve()
        if target.suffix.lower() not in {".md", ".markdown"}:
            raise ValueError("output_path 必须是 .md 或 .markdown 文件")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report, encoding="utf-8")
        saved_to = str(target)
    await ctx.report_progress(progress=1.0, total=1.0, message="汇总报告生成完成")
    return {"title": paper.title, "report": report, "saved_to": saved_to, "mode": "llm" if use_llm else "offline"}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

