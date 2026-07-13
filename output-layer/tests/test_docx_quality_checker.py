from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SKILL_ROOT / "src"
SCRIPT = SKILL_ROOT / "scripts" / "check_docx_quality.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "docx-quality"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class DocxQualityCheckerTest(unittest.TestCase):
    def test_passes_well_structured_formal_report(self) -> None:
        from docx_quality_checker import check_docx_quality

        report = check_docx_quality(FIXTURES_DIR / "pass-formal-report.md")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["doc_type"], "formal_report")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["next_action"], "render_docx")

    def test_marks_proposal_with_missing_required_sections_as_draft_only(self) -> None:
        from docx_quality_checker import check_docx_quality

        report = check_docx_quality(FIXTURES_DIR / "draft-proposal.md")

        self.assertEqual(report["status"], "draft_only")
        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertIn("missing_required_section", warning_codes)
        self.assertIn("weak_opener", warning_codes)
        self.assertEqual(report["next_action"], "revise_text")

    def test_blocks_structural_and_docx_readiness_failures(self) -> None:
        from docx_quality_checker import check_docx_quality

        report = check_docx_quality(FIXTURES_DIR / "blocked-structure.md")

        self.assertEqual(report["status"], "blocked")
        blocker_codes = {item["code"] for item in report["blockers"]}
        self.assertIn("multiple_h1", blocker_codes)
        self.assertIn("raw_html", blocker_codes)
        self.assertIn("unclosed_code_fence", blocker_codes)
        self.assertEqual(report["next_action"], "revise_text")

    def test_detects_second_wave_deterministic_quality_warnings(self) -> None:
        from docx_quality_checker import check_docx_quality

        report = check_docx_quality(FIXTURES_DIR / "deterministic-second-wave.md")

        self.assertEqual(report["status"], "draft_only")
        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertIn("empty_section_after_heading", warning_codes)
        self.assertIn("mixed_subject_terms", warning_codes)
        self.assertIn("figure_or_table_missing_caption", warning_codes)

    def test_detects_missing_reference_section_when_external_sources_exist(self) -> None:
        from docx_quality_checker import check_docx_quality

        report = check_docx_quality(FIXTURES_DIR / "missing-reference-section.md")

        self.assertEqual(report["status"], "draft_only")
        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertIn("missing_reference_section", warning_codes)

    def test_captioned_table_does_not_trigger_missing_caption_warning(self) -> None:
        from docx_quality_checker import check_docx_quality

        report = check_docx_quality(FIXTURES_DIR / "renderable-table-caption.md")

        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertNotIn("figure_or_table_missing_caption", warning_codes)

    def test_low_risk_docx_warnings_do_not_force_draft_only_status(self) -> None:
        from docx_quality_checker import check_docx_quality

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        source = temp_dir / "low-risk.md"
        source.write_text(
            "# 系统运行记录\n\n"
            "## 一、系统概况\n\n"
            "| 项目 | 内容 |\n"
            "|---|---|\n"
            "| 端口 | 127.0.0.1:18789 |\n\n"
            "详见 https://example.com/status\n\n"
            "## 二、文档目的\n\n"
            "本记录用于说明当前运行状态。\n\n"
            "## 三、处理依据\n\n"
            "本记录依据当前运行日志和状态输出整理。\n\n"
            "## 四、处理方案\n\n"
            "已完成状态核对并保留验证路径。\n\n"
            "## 五、结论与下一步\n\n"
            "后续按运行记录继续复核。\n",
            encoding="utf-8",
        )

        report = check_docx_quality(source)

        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertIn("figure_or_table_missing_caption", warning_codes)
        self.assertIn("bare_url", warning_codes)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["next_action"], "render_docx")

    def test_runtime_record_requires_verification_or_followup(self) -> None:
        from docx_quality_checker import check_docx_quality

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        source = temp_dir / "runtime.md"
        source.write_text(
            "# 系统运行记录\n\n"
            "## 一、系统概况\n\n"
            "版本：v1.2.3，PID 1470，监听端口 127.0.0.1:18789。\n",
            encoding="utf-8",
        )

        report = check_docx_quality(source)

        self.assertEqual(report["doc_type"], "runtime_record")
        self.assertEqual(report["status"], "draft_only")
        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertIn("runtime_record_missing_verification", warning_codes)

    def test_meeting_note_requires_discussion_and_followup(self) -> None:
        from docx_quality_checker import check_docx_quality

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        source = temp_dir / "meeting.md"
        source.write_text(
            "# 会议纪要\n\n"
            "## 讨论结果\n\n"
            "已确认输出方向。\n",
            encoding="utf-8",
        )

        report = check_docx_quality(source)

        self.assertEqual(report["doc_type"], "meeting_note")
        self.assertEqual(report["status"], "draft_only")
        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertIn("missing_required_section", warning_codes)

    def test_content_article_ignores_reference_section_requirement_but_keeps_style_warnings(self) -> None:
        from docx_quality_checker import check_docx_quality

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        source = temp_dir / "article.md"
        source.write_text(
            "# 标题备选\n\n"
            "1. 我们为什么总是被困住\n\n"
            "## 核心命题\n\n"
            "我想讨论一个关系问题。https://example.com/a https://example.com/b\n\n"
            "## 正文\n\n"
            "需要注意的是，这件事不是简单的对错。需要注意的是，很多时候我们只是在重复旧解释。\n",
            encoding="utf-8",
        )

        report = check_docx_quality(source)

        self.assertEqual(report["doc_type"], "content_article")
        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertNotIn("missing_reference_section", warning_codes)
        self.assertIn("repeated_template_phrase", warning_codes)
        self.assertEqual(report["status"], "draft_only")

    def test_numbered_h1_sections_after_title_do_not_count_as_multiple_titles(self) -> None:
        from docx_quality_checker import check_docx_quality

        report = check_docx_quality(FIXTURES_DIR / "numbered-h1-sections.md")

        blocker_codes = {item["code"] for item in report["blockers"]}
        self.assertNotIn("multiple_h1", blocker_codes)

    def test_structural_blocks_do_not_create_long_sentence_suggestions(self) -> None:
        from docx_quality_checker import check_docx_quality

        report = check_docx_quality(FIXTURES_DIR / "structural-blocks-not-long-sentence.md")

        suggestion_codes = {item["code"] for item in report["suggestions"]}
        self.assertNotIn("long_sentence", suggestion_codes)

    def test_formal_report_required_sections_accept_equivalent_headings(self) -> None:
        from docx_quality_checker import check_docx_quality

        report = check_docx_quality(FIXTURES_DIR / "formal-report-equivalent-headings.md")

        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertNotIn("missing_required_section", warning_codes)

    def test_cli_writes_json_and_markdown_reports(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(FIXTURES_DIR / "draft-proposal.md"),
                "--outdir",
                str(temp_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertIn("status=draft_only", result.stdout)
        json_path = temp_dir / "docx_quality_report.json"
        md_path = temp_dir / "docx_quality_report.md"
        self.assertTrue(json_path.exists())
        self.assertTrue(md_path.exists())
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "draft_only")
        self.assertIn("Docx Quality Report", md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
