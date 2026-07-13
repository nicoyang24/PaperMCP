import argparse
import json
import os
import sys

from code_quality_mcp import analyze_path, build_markdown_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze code comment rate and redundancy for a file or directory")
    parser.add_argument("path", help="The file or directory to analyze")
    parser.add_argument("--markdown", action="store_true", help="Output a Chinese Markdown report")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    parser.add_argument("--output", help="Optional path to write the Markdown report to a file")
    args = parser.parse_args()

    target_path = os.path.abspath(args.path)
    if not os.path.exists(target_path):
        print(f"Path does not exist: {target_path}", file=sys.stderr)
        return 1

    result = analyze_path(target_path)
    report = build_markdown_report(target_path, result)

    if args.output:
        output_path = os.path.abspath(args.output)
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"Report written to: {output_path}")

    if args.markdown or not args.json:
        print(report)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
