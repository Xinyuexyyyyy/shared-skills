from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SKILL_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class DocumentClassifierTest(unittest.TestCase):
    def test_frontmatter_doc_type_wins_over_heuristics(self) -> None:
        from document_classifier import infer_document_type

        result = infer_document_type(
            {"doc_type": "proposal"},
            "# 标题备选\n\n## 正文\n\n我想写一篇文章。\n",
        )

        self.assertEqual(result["doc_type"], "proposal")
        self.assertEqual(result["source"], "frontmatter")

    def test_detects_content_article_from_article_structure(self) -> None:
        from document_classifier import infer_document_type

        result = infer_document_type(
            {},
            "# 标题备选\n\n## 核心命题\n\n我想讨论一个问题。\n\n## 正文\n\n我们经常把关系说得太简单。\n",
        )

        self.assertEqual(result["doc_type"], "content_article")
        self.assertIn("标题备选", result["signals"])

    def test_detects_runtime_record_from_operational_facts(self) -> None:
        from document_classifier import infer_document_type

        result = infer_document_type(
            {},
            "# OpenClaw 全景扫描报告\n\n## 一、系统概况\n\n版本：2026.4.11，PID 1470，监听端口 127.0.0.1:18789。\n",
        )

        self.assertEqual(result["doc_type"], "runtime_record")
        self.assertIn("运行事实", result["signals"])

    def test_detects_meeting_note_from_meeting_sections(self) -> None:
        from document_classifier import infer_document_type

        result = infer_document_type(
            {},
            "# 会议纪要样例\n\n## 讨论结果\n\n已确认主链。\n\n## 后续动作\n\n继续回放。\n",
        )

        self.assertEqual(result["doc_type"], "meeting_note")
        self.assertIn("会议纪要", result["signals"])

    def test_content_article_quality_gate_does_not_apply_formal_report_subject_warning(self) -> None:
        from docx_quality_checker import check_docx_quality

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp_dir, ignore_errors=True))
        source = temp_dir / "article.md"
        source.write_text(
            "# 标题备选\n\n"
            "1. 孝是孝，顺是顺\n\n"
            "## 核心命题\n\n"
            "我想重新审视孝顺这个词。\n\n"
            "## 正文\n\n"
            "我们经常把爱和服从绑在一起，这会让关系变得含混。\n",
            encoding="utf-8",
        )

        report = check_docx_quality(source)

        self.assertEqual(report["doc_type"], "content_article")
        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertNotIn("mixed_subject_terms", warning_codes)
        self.assertNotIn("missing_required_section", warning_codes)


if __name__ == "__main__":
    unittest.main()
