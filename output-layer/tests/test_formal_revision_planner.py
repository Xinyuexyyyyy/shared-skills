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
SCRIPT = SKILL_ROOT / "scripts" / "revise_formal_markdown.py"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class FormalRevisionPlannerTest(unittest.TestCase):
    def test_revision_adds_missing_sections_and_reference_placeholder_without_fabricating_facts(self) -> None:
        from docx_quality_checker import check_docx_quality
        from formal_revision_planner import revise_formal_markdown

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        source = temp_dir / "thin.md"
        source.write_text(
            "# 产品调研总报告\n\n"
            "## 1. 先说结论\n\n"
            "当前建议先补真实用户和验证计划。参考 https://example.com/a 和 https://example.com/b。\n",
            encoding="utf-8",
        )
        quality_report = check_docx_quality(source)

        result = revise_formal_markdown(source, docx_quality_report=quality_report)

        revised = result["revised_markdown"]
        self.assertIn("## 待补充：背景", revised)
        self.assertIn("## 待补充：目的", revised)
        self.assertIn("## 参考资料", revised)
        self.assertIn("待补充：集中列出标准、链接或文献线索。", revised)
        self.assertIn("https://example.com/a", revised)
        self.assertNotIn("数据显示", revised)
        self.assertNotIn("根据相关政策", revised)
        action_codes = {item["code"] for item in result["report"]["actions"]}
        self.assertIn("add_missing_section_placeholders", action_codes)
        self.assertIn("add_reference_placeholder", action_codes)

    def test_revision_consumes_assisted_report_and_expansion_plan_without_fabricating_facts(self) -> None:
        from formal_revision_planner import revise_formal_markdown

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
        assisted_report = {
            "status": "needs_revision",
            "findings": [
                {
                    "code": "abstract_four_elements_incomplete",
                    "evidence": {"missing_elements": ["方法/材料", "结果/发现"]},
                    "fix": "按对象/问题、方法/材料、结果/发现、意义/边界重排摘要；不得新增未提供的事实。",
                }
            ],
        }
        formal_expansion_report = {
            "revision_plan": [
                {
                    "action": "补充事实依据",
                    "target": "结果或发现的可复核表述。",
                    "instruction": "补充可复核的真实样例、抽样结果、验证记录、来源或责任人口径。",
                },
                {
                    "action": "人工确认",
                    "target": "摘要结论边界。",
                    "instruction": "由负责人确认结论口径，不由扩写层代替判断。",
                },
            ],
        }

        result = revise_formal_markdown(
            source,
            docx_quality_report={"status": "pass", "warnings": [], "blockers": []},
            assisted_quality_report=assisted_report,
            formal_expansion_report=formal_expansion_report,
        )

        revised = result["revised_markdown"]
        self.assertIn("## 待补充：方法/材料", revised)
        self.assertIn("## 待补充：结果/发现", revised)
        self.assertIn("## 人工修订清单", revised)
        self.assertIn("补充事实依据：补充可复核的真实样例", revised)
        self.assertIn("人工确认：由负责人确认结论口径", revised)
        self.assertNotIn("数据显示", revised)
        self.assertNotIn("根据相关政策", revised)
        action_codes = {item["code"] for item in result["report"]["actions"]}
        self.assertIn("add_assisted_missing_element_placeholders", action_codes)
        self.assertIn("add_revision_plan_checklist", action_codes)

    def test_revision_keeps_blocked_documents_unchanged_except_report(self) -> None:
        from docx_quality_checker import check_docx_quality
        from formal_revision_planner import revise_formal_markdown

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        source = temp_dir / "blocked.md"
        source.write_text("# A\n\n# B\n\n<div>raw</div>\n\n```text\nunclosed\n", encoding="utf-8")
        quality_report = check_docx_quality(source)

        result = revise_formal_markdown(source, docx_quality_report=quality_report)

        self.assertEqual(result["report"]["status"], "blocked")
        self.assertEqual(result["revised_markdown"], source.read_text(encoding="utf-8"))
        self.assertTrue(result["report"]["blocked_reasons"])

    def test_cli_writes_revised_markdown_and_reports(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        source = temp_dir / "thin.md"
        source.write_text("# 产品调研总报告\n\n## 1. 先说结论\n\n当前建议先补真实用户和验证计划。\n", encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(source),
                "--outdir",
                str(temp_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertIn("status=revised", result.stdout)
        revised_path = temp_dir / "output.revised.md"
        json_path = temp_dir / "formal_revision_report.json"
        md_path = temp_dir / "formal_revision_report.md"
        self.assertTrue(revised_path.exists())
        self.assertTrue(json_path.exists())
        self.assertTrue(md_path.exists())
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "revised")
        self.assertIn("Formal Revision Report", md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
