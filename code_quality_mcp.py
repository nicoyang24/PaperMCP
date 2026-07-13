import ast
import os
from collections import Counter
from typing import Dict, List


SUPPORTED_SUFFIXES = (".py", ".pyi", ".js", ".ts", ".java", ".go", ".cs", ".cpp", ".cc", ".cxx", ".cu")


def _strip_comments_and_strings(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    lines_to_keep = set()
    for node in ast.walk(tree):
        if hasattr(node, "lineno"):
            lines_to_keep.add(node.lineno)
        if hasattr(node, "end_lineno") and node.end_lineno is not None:
            lines_to_keep.add(node.end_lineno)

    return "\n".join(
        line for index, line in enumerate(source.splitlines(), start=1) if index in lines_to_keep
    )


def _estimate_comment_rate(source: str) -> float:
    lines = source.splitlines()
    if not lines:
        return 0.0

    comment_lines = sum(
        1
        for line in lines
        if line.strip().startswith(("#", "//", "/*", "*"))
    )
    return round(comment_lines / len(lines), 4)


def _estimate_redundancy_ratio(source: str) -> float:
    tokens = [token for token in source.replace("\n", " ").split() if token]
    if not tokens:
        return 0.0

    counts = Counter(tokens)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return round(repeated / len(tokens), 4)


def analyze_path(path: str) -> Dict[str, object]:
    if os.path.isfile(path):
        files = [path]
    else:
        files = []
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith(SUPPORTED_SUFFIXES):
                    files.append(os.path.join(root, filename))

    file_results: List[Dict[str, object]] = []
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                source = fh.read()
        except (UnicodeDecodeError, OSError):
            continue

        file_results.append(
            {
                "path": file_path,
                "comment_rate": _estimate_comment_rate(source),
                "redundancy_ratio": _estimate_redundancy_ratio(source),
                "lines": len(source.splitlines()),
            }
        )

    overall = {
        "comment_rate": round(
            sum(item["comment_rate"] for item in file_results) / len(file_results), 4
        ) if file_results else 0.0,
        "redundancy_ratio": round(
            sum(item["redundancy_ratio"] for item in file_results) / len(file_results), 4
        ) if file_results else 0.0,
        "files_analyzed": len(file_results),
    }

    return {"file_count": len(file_results), "files": file_results, "overall": overall}


def build_markdown_report(target_path: str, analysis_result: Dict[str, object]) -> str:
    target_path = os.path.abspath(target_path)
    lines = [
        "# 代码规范检查报告",
        "",
        f"- 目标路径：{target_path}",
        f"- 分析文件数：{analysis_result.get('file_count', 0)}",
        f"- 平均注释率：{analysis_result.get('overall', {}).get('comment_rate', 0.0):.4f}",
        f"- 平均冗余度：{analysis_result.get('overall', {}).get('redundancy_ratio', 0.0):.4f}",
        "",
        "## 文件清单",
        "",
    ]

    for item in analysis_result.get("files", []):
        rel_path = os.path.relpath(item["path"], target_path)
        lines.extend(
            [
                f"- {rel_path}",
                f"  - 注释率：{item.get('comment_rate', 0.0):.4f}",
                f"  - 冗余度：{item.get('redundancy_ratio', 0.0):.4f}",
                f"  - 行数：{item.get('lines', 0)}",
            ]
        )

    if not analysis_result.get("files"):
        lines.append("- 未发现可分析文件")

    return "\n".join(lines)
