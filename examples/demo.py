"""端到端调用 Paper Report MCP 的演示客户端。"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="解析一篇 PDF，并通过 MCP 生成汇总报告")
    parser.add_argument("pdf_path", type=Path, help="待解析 PDF 的路径")
    parser.add_argument(
        "--output",
        type=Path,
        help="报告输出路径，默认写入 PDF 同目录的 <文件名>-report.md",
    )
    parser.add_argument("--max-pages", type=int, default=100, help="最多解析页数，默认 100")
    parser.add_argument("--offline", action="store_true", help="使用离线抽取模式，不进行中文翻译和深度解读")
    return parser.parse_args()


async def run_demo(args: argparse.Namespace) -> None:
    pdf_path = args.pdf_path.expanduser().resolve()
    if not pdf_path.is_file():
        raise SystemExit(f"PDF 文件不存在: {pdf_path}")
    output = (args.output or pdf_path.with_name(f"{pdf_path.stem}-report.md")).expanduser().resolve()
    use_llm = not args.offline and bool(os.environ.get("PAPER_LLM_API_KEY"))
    if not args.offline and not use_llm:
        print(
            "提示：当前独立演示客户端不提供 MCP Sampling，且未检测到 PAPER_LLM_API_KEY。\n"
            "本次将自动使用离线抽取模式。若要生成翻译后的中文深度报告，请先按 README 配置模型。\n"
        )

    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "paper_mcp.server"],
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            inspected = await session.call_tool(
                "inspect_paper",
                {"pdf_path": str(pdf_path), "max_pages": args.max_pages},
            )
            print("论文解析结果：")
            if inspected.structuredContent:
                print(json.dumps(inspected.structuredContent, ensure_ascii=False, indent=2))
            else:
                print("\n".join(getattr(item, "text", str(item)) for item in inspected.content))

            generated = await session.call_tool(
                "generate_paper_report",
                {
                    "pdf_path": str(pdf_path),
                    "output_path": str(output),
                    "use_llm": use_llm,
                    "max_pages": args.max_pages,
                },
            )
            if generated.isError:
                detail = "\n".join(getattr(item, "text", str(item)) for item in generated.content)
                print(f"\n报告生成失败：\n{detail}", file=sys.stderr)
                return
            print(f"\n报告已生成：{output}")


def main() -> None:
    asyncio.run(run_demo(parse_args()))


if __name__ == "__main__":
    main()
