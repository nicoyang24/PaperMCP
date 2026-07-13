import os
import tempfile
import unittest

from code_quality_mcp import analyze_path, build_markdown_report


class CodeQualityAnalysisTests(unittest.TestCase):
    def test_comment_rate_and_redundancy_are_reported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "sample.py")
            with open(sample_path, "w", encoding="utf-8") as fh:
                fh.write(
                    "# This file is a sample\n"
                    "def foo():\n"
                    "    value = 1\n"
                    "    return value\n"
                    "\n"
                    "def bar():\n"
                    "    value = 1\n"
                    "    return value\n"
                )

            result = analyze_path(tmpdir)

            self.assertEqual(result["file_count"], 1)
            self.assertGreaterEqual(result["overall"]["comment_rate"], 0)
            self.assertGreaterEqual(result["overall"]["redundancy_ratio"], 0)
            self.assertIn("files", result)

    def test_cpp_and_cu_files_are_supported_and_report_is_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "sample.cu")
            with open(sample_path, "w", encoding="utf-8") as fh:
                fh.write("// CUDA comment\n"
                         "__global__ void kernel() {\n"
                         "    int x = 1;\n"
                         "    x = x + 1;\n"
                         "}\n")

            result = analyze_path(tmpdir)
            report = build_markdown_report(tmpdir, result)

            self.assertEqual(result["file_count"], 1)
            self.assertIn("代码规范检查报告", report)
            self.assertIn("sample.cu", report)


if __name__ == "__main__":
    unittest.main()
