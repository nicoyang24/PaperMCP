from __future__ import annotations

from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import SamplingMessage, TextContent

from .paper import Paper, parse_pdf
from .report import build_offline_report
from .config import LLMConfig, load_llm_config

mcp = FastMCP(
    "paper-report",
    instructions="解析指定的 PDF 学术论文，并生成易懂、完整的中文汇总报告。",
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


def _chunks(paper: Paper, size: int = 12_000, maximum: int = 10) -> list[str]:
    """尽量按章节切分，避免只总结论文开头。"""
    chunks: list[str] = []
    for section, content in paper.sections.items():
        if section.lower() in {"references", "参考文献"}:
            continue
        for start in range(0, len(content), size):
            chunks.append(f"章节：{section}\n{content[start:start + size]}")
            if len(chunks) >= maximum:
                return chunks
    return chunks or [paper.text[:size]]


async def _sample(prompt: str, ctx: Context, max_tokens: int) -> str:
    result = await ctx.session.create_message(
        messages=[SamplingMessage(role="user", content=TextContent(type="text", text=prompt))],
        max_tokens=max_tokens,
    )
    if getattr(result.content, "type", None) != "text":
        raise RuntimeError("MCP 客户端未返回文本类型的模型结果")
    return result.content.text


async def _openai_compatible(prompt: str, max_tokens: int, config: LLMConfig) -> str:
    if not config.api_key:
        raise RuntimeError("配置文件中未设置 llm.api_key")
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{config.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {config.api_key}"},
            json={
                "model": config.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def _llm_report(paper: Paper, ctx: Context) -> tuple[str, str]:
    call: Callable[[str, int], Awaitable[str]]
    config = load_llm_config()
    if config.api_key:
        call = lambda prompt, tokens: _openai_compatible(prompt, tokens, config)
        provider = "openai-compatible"
    else:
        call = lambda prompt, tokens: _sample(prompt, ctx, tokens)
        provider = "mcp-sampling"

    notes: list[str] = []
    parts = _chunks(paper)
    for index, chunk in enumerate(parts, 1):
        await ctx.report_progress(
            progress=0.15 + 0.55 * index / len(parts),
            total=1.0,
            message=f"正在理解论文内容 {index}/{len(parts)}",
        )
        prompt = f"""你是严谨的论文阅读助手。阅读下面的论文片段，用中文记录事实性笔记。

要求：
1. 将英文内容翻译、改写成自然中文，不要大段保留英文原句。
2. 用通俗语言解释专业概念；必要时可用“也就是说”补充一句解释。
3. 提取研究问题、方法步骤、数据集、对比方法、指标、带数字的结果、作者承认的局限。
4. 区分作者主张和实验事实。没有提到的信息不要猜测。
5. 公式用文字解释其作用，不必照抄公式。

论文标题：{paper.title}
片段 {index}/{len(parts)}：
{chunk}"""
        notes.append(await call(prompt, 1800))

    synthesis = f"""请根据下列分段阅读笔记，撰写一份完整、易懂的中文论文汇总报告。

写作要求：
- 全文使用中文；首次出现的必要英文术语可在中文后用括号标注。
- 让没有读过原论文的人也能理解“为什么研究、怎么做、发现了什么、有什么用”。
- 先说结论，再解释细节。避免空泛措辞和逐段复述。
- 所有数字、比较结果和结论必须来自笔记；信息缺失时写“原文未明确说明”。
- 不要把推测写成事实，不要编造作者、机构、数据或实验结果。
- 方法部分按步骤解释，并说明每一步解决什么问题。
- 结果部分说明比较对象、指标、数值以及该数值意味着什么。

严格使用以下 Markdown 结构：
# {paper.title}：论文中文解读
## 一句话总结
## 论文要解决什么问题
## 为什么这个问题重要
## 作者提出了什么方法
## 方法是怎样工作的
## 实验是怎么做的
## 得到了什么结果
## 主要创新点
## 局限与需要注意的地方
## 这项工作有什么价值
## 关键术语通俗解释
## 给读者的最终结论

已知元数据：作者={paper.authors or '未提供'}；PDF页数={paper.pages}

分段笔记：
{chr(10).join(f'### 笔记 {i + 1}{chr(10)}{note}' for i, note in enumerate(notes))}"""
    return await call(synthesis, 5000), provider


@mcp.tool()
async def generate_paper_report(
    pdf_path: str,
    ctx: Context,
    output_path: str | None = None,
    use_llm: bool = True,
    max_pages: int = 100,
) -> dict[str, Any]:
    """生成易懂的中文论文报告。默认使用模型理解和翻译；use_llm=false 仅生成离线抽取版。"""
    await ctx.info(f"正在解析论文: {pdf_path}")
    paper = parse_pdf(pdf_path, max_pages)
    await ctx.report_progress(progress=0.1, total=1.0, message="PDF 文本解析完成")
    if use_llm:
        try:
            report, mode = await _llm_report(paper, ctx)
        except Exception as exc:
            raise RuntimeError(
                "中文深度总结需要支持 MCP Sampling 的客户端，或在 paper_mcp.config.json 中"
                "配置 llm.api_key、llm.model 和 llm.base_url。"
                f" 模型调用失败：{exc}"
            ) from exc
    else:
        report, mode = build_offline_report(paper), "offline-extractive"

    saved_to = None
    if output_path:
        target = Path(output_path).expanduser().resolve()
        if target.suffix.lower() not in {".md", ".markdown"}:
            raise ValueError("output_path 必须是 .md 或 .markdown 文件")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report, encoding="utf-8")
        saved_to = str(target)
    await ctx.report_progress(progress=1.0, total=1.0, message="中文汇总报告生成完成")
    return {"title": paper.title, "report": report, "saved_to": saved_to, "mode": mode}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
