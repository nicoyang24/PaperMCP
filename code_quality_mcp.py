import ast
import os
import re
from collections import Counter
from typing import Dict, List


SUPPORTED_SUFFIXES = (".py", ".pyi", ".js", ".ts", ".java", ".go", ".cs", ".cpp", ".cc", ".cxx", ".cu")


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
    tokens = [token for token in re.split(r"[^A-Za-z0-9_]+", source) if token]
    if not tokens:
        return 0.0

    counts = Counter(tokens)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return round(repeated / len(tokens), 4)


def _find_redundant_patterns(source: str) -> List[str]:
    lines = source.splitlines()
    if not lines:
        return []

    repeats: List[tuple[str, int]] = []
    for line in lines:
        stripped = line.strip()
        if len(stripped) < 8 or stripped.startswith(("#", "//", "/*", "*")):
            continue
        repeats.append((stripped, 1))

    counts = Counter(stripped for stripped, _ in repeats)
    repeated_lines = [line for line, count in counts.items() if count > 1]
    return repeated_lines[:5]


def _find_long_structures(source: str) -> List[Dict[str, object]]:
    lines = source.splitlines()
    results: List[Dict[str, object]] = []
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^(def|class|struct|function|__global__|void|int|float|double|std::|template)\b", stripped):
            if len(stripped) > 70:
                results.append({"line": idx, "snippet": stripped[:100]})
    return results[:5]


def _find_naming_warnings(source: str) -> List[str]:
    warnings: List[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.search(r"\b([a-z]+_[a-z]+_[a-z]+)\b", stripped):
            warnings.append(stripped[:120])
        if re.search(r"\b([A-Za-z]+[A-Z][A-Za-z]+)\b", stripped) and "class " not in stripped and "struct " not in stripped:
            warnings.append(stripped[:120])
    return warnings[:5]


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
                "redundant_patterns": _find_redundant_patterns(source),
                "long_structures": _find_long_structures(source),
                "naming_warnings": _find_naming_warnings(source),
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
                f"### {rel_path}",
                "",
                f"- 注释率：{item.get('comment_rate', 0.0):.4f}",
                f"- 冗余度：{item.get('redundancy_ratio', 0.0):.4f}",
                f"- 行数：{item.get('lines', 0)}",
                "",
                "#### 可能冗余的代码片段",
                "",
            ]
        )

        for pattern in item.get("redundant_patterns", []) or []:
            lines.append(f"- {pattern}")
        if not item.get("redundant_patterns"):
            lines.append("- 未发现明显重复行")

        lines.extend(["", "#### 复杂度与结构提示", ""])
        for structure in item.get("long_structures", []) or []:
            lines.append(f"- 第 {structure['line']} 行可能过长或过于复杂：{structure['snippet']}")
        if not item.get("long_structures"):
            lines.append("- 未发现明显的长函数/长类/长模板提示")

        lines.extend(["", "#### 命名规范提示", ""])
        for warning in item.get("naming_warnings", []) or []:
            lines.append(f"- {warning}")
        if not item.get("naming_warnings"):
            lines.append("- 未发现明显命名问题")

        lines.append("")

    if not analysis_result.get("files"):
        lines.append("- 未发现可分析文件")

    return "\n".join(lines)
