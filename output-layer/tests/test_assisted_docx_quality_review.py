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
SCRIPT = SKILL_ROOT / "scripts" / "assist_docx_quality_review.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "docx-quality"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class AssistedDocxQualityReviewTest(unittest.TestCase):
    def test_proposal_reports_three_question_gap_and_human_gate(self) -> None:
        from formal_assisted_reviewer import assist_docx_quality_review

        report = assist_docx_quality_review(FIXTURES_DIR / "assisted-proposal-incomplete.md")

        self.assertEqual(report["status"], "needs_revision")
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("proposal_three_questions_incomplete", codes)
        finding = next(item for item in report["findings"] if item["code"] == "proposal_three_questions_incomplete")
        self.assertEqual(finding["lesson_id"], "FWM-001")
        self.assertIn("研究基础/可行性", finding["evidence"]["missing_elements"])
        self.assertTrue(all(source_id.startswith("CN-SRC-") for source_id in finding["source_ids"]))
        gate_codes = {item["code"] for item in report["human_gates"]}
        self.assertIn("proposal_compliance_gate", gate_codes)

    def test_technical_document_reports_missing_effect_and_boundary(self) -> None:
        from formal_assisted_reviewer import assist_docx_quality_review

        report = assist_docx_quality_review(FIXTURES_DIR / "assisted-technical-incomplete.md")

        self.assertEqual(report["status"], "needs_revision")
        finding = next(item for item in report["findings"] if item["code"] == "technical_chain_incomplete")
        self.assertEqual(finding["lesson_id"], "FWM-002")
        self.assertIn("技术效果", finding["evidence"]["missing_elements"])
        self.assertIn("边界条件", finding["evidence"]["missing_elements"])

    def test_abstract_reports_missing_result_or_significance(self) -> None:
        from formal_assisted_reviewer import assist_docx_quality_review

        report = assist_docx_quality_review(FIXTURES_DIR / "assisted-abstract-incomplete.md")

        finding = next(item for item in report["findings"] if item["code"] == "abstract_four_elements_incomplete")
        self.assertEqual(finding["lesson_id"], "FWM-003")
        self.assertIn("结果/发现", finding["evidence"]["missing_elements"])
        self.assertIn("意义/边界", finding["evidence"]["missing_elements"])

    def test_abstract_with_placeholder_sections_still_requires_input(self) -> None:
        from formal_assisted_reviewer import assist_docx_quality_review

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        source = temp_dir / "expanded-abstract.md"
        source.write_text(
            "---\n"
            "doc_type: abstract\n"
            "---\n"
            "# 摘要扩写稿\n\n"
            "## 一、对象与问题\n\n"
            "本文面向中文正式文档输出质量控制问题。\n\n"
            "## 二、方法与材料\n\n"
            "- None\n\n"
            "## 三、结果与发现\n\n"
            "- 待补充：结果或发现的可复核表述。\n\n"
            "## 四、意义与边界\n\n"
            "意义表述应与原始证据强度一致。\n",
            encoding="utf-8",
        )

        report = assist_docx_quality_review(source)

        self.assertEqual(report["status"], "needs_revision")
        finding = next(item for item in report["findings"] if item["code"] == "abstract_four_elements_incomplete")
        self.assertIn("方法/材料", finding["evidence"]["missing_elements"])
        self.assertIn("结果/发现", finding["evidence"]["missing_elements"])

    def test_manual_reports_missing_preconditions_and_exception_handling(self) -> None:
        from formal_assisted_reviewer import assist_docx_quality_review

        report = assist_docx_quality_review(FIXTURES_DIR / "assisted-manual-incomplete.md")

        finding = next(item for item in report["findings"] if item["code"] == "manual_task_chain_incomplete")
        self.assertEqual(finding["lesson_id"], "FWM-005")
        self.assertIn("前置条件", finding["evidence"]["missing_elements"])
        self.assertIn("异常处理", finding["evidence"]["missing_elements"])

    def test_weak_action_items_are_reported_with_revision_action(self) -> None:
        from formal_assisted_reviewer import assist_docx_quality_review

        report = assist_docx_quality_review(FIXTURES_DIR / "assisted-actions-weak.md")

        finding = next(item for item in report["findings"] if item["code"] == "action_item_incomplete")
        self.assertEqual(finding["lesson_id"], "FWM-004")
        self.assertIn("加强管理", " ".join(finding["evidence"]["examples"]))
        self.assertIn("对象、动作、条件和结果", finding["fix"])

    def test_complete_abstract_passes_assisted_review(self) -> None:
        from formal_assisted_reviewer import assist_docx_quality_review

        report = assist_docx_quality_review(FIXTURES_DIR / "assisted-pass-abstract.md")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["next_action"], "render_or_deterministic_check")

    def test_generic_standardization_word_does_not_trigger_human_gate(self) -> None:
        from formal_assisted_reviewer import assist_docx_quality_review

        report = assist_docx_quality_review(FIXTURES_DIR / "assisted-standardization-no-gate.md")

        self.assertEqual(report["human_gates"], [])

    def test_operational_facts_trigger_human_gate(self) -> None:
        from formal_assisted_reviewer import assist_docx_quality_review

        report = assist_docx_quality_review(FIXTURES_DIR / "assisted-operational-facts-gate.md")

        gate_codes = {item["code"] for item in report["human_gates"]}
        self.assertIn("fact_and_institution_gate", gate_codes)

    def test_cli_writes_json_and_markdown_reports(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(FIXTURES_DIR / "assisted-proposal-incomplete.md"),
                "--outdir",
                str(temp_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertIn("status=needs_revision", result.stdout)
        json_path = temp_dir / "assisted_quality_report.json"
        md_path = temp_dir / "assisted_quality_report.md"
        self.assertTrue(json_path.exists())
        self.assertTrue(md_path.exists())
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "needs_revision")
        self.assertIn("Assisted Docx Quality Report", md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
