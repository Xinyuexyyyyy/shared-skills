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
SCRIPT = SKILL_ROOT / "scripts" / "expand_formal_markdown.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "formal-expansion"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class FormalExpanderTest(unittest.TestCase):
    def test_direction_fixtures_match_formal_report_examples(self) -> None:
        from formal_expander import expand_formal_markdown

        cases = [
            (
                "too-short-input.md",
                [
                    "建设目的",
                    "现有问题",
                    "处理原则",
                    "结论与下一步",
                    "内容结构不足",
                    "表达不符合正式 docx 交付要求",
                    "扩写层不得新增未经提供的事实、数据、政策或结论",
                ],
            ),
            (
                "colloquial-input.md",
                [
                    "当前状态",
                    "主要问题",
                    "控制目标",
                    "输出边界",
                    "当前输出链路已具备基础运行能力",
                    "内容密度不足，缺少结构化展开",
                    "对用户前置条件存在重复复述",
                ],
            ),
            (
                "repetitive-input.md",
                [
                    "明确对象",
                    "处理原则与方案",
                    "扩写、检查、修订、再输出",
                    "可渲染、需修订或需补事实",
                ],
            ),
        ]

        for fixture_name, expected_fragments in cases:
            result = expand_formal_markdown(FIXTURES_DIR / fixture_name)
            text = result["expanded_markdown"]
            for fragment in expected_fragments:
                self.assertIn(fragment, text)

    def test_structured_short_input_builds_formal_skeleton_without_fabricating_facts(self) -> None:
        from formal_expander import expand_formal_markdown

        result = expand_formal_markdown(FIXTURES_DIR / "too-short-input.md")

        self.assertIn("# 输出层正式写作质量关建设说明", result["expanded_markdown"])
        self.assertIn("# 一、建设目的", result["expanded_markdown"])
        self.assertIn("# 二、现有问题", result["expanded_markdown"])
        self.assertIn("# 三、处理原则", result["expanded_markdown"])
        self.assertIn("不新增未经提供的事实、数据、政策或结论", result["expanded_markdown"])
        self.assertIn("待补充：", result["expanded_markdown"])
        self.assertNotIn("数据显示", result["expanded_markdown"])
        self.assertEqual(result["report"]["status"], "expanded")
        self.assertTrue(result["report"]["blocked_expansions"])
        revision_actions = {item["action"] for item in result["report"]["revision_plan"]}
        self.assertIn("补充事实依据", revision_actions)
        action_codes = {item["code"] for item in result["report"]["actions"]}
        self.assertIn("build_formal_skeleton", action_codes)

    def test_conservative_colloquial_input_formalizes_expression(self) -> None:
        from formal_expander import expand_formal_markdown

        result = expand_formal_markdown(FIXTURES_DIR / "colloquial-input.md")

        text = result["expanded_markdown"]
        self.assertIn("当前输出链路已具备基础运行能力", text)
        self.assertIn("内容密度不足", text)
        self.assertIn("正式文档输出前的质量门控", text)
        self.assertNotIn("这个东西", text)
        self.assertNotIn("挺烦的", text)
        self.assertIn("待补充：", text)
        action_codes = {item["code"] for item in result["report"]["actions"]}
        self.assertIn("formalize_colloquial_expression", action_codes)

    def test_structured_repetitive_input_merges_low_information_claims(self) -> None:
        from formal_expander import expand_formal_markdown

        result = expand_formal_markdown(FIXTURES_DIR / "repetitive-input.md")

        text = result["expanded_markdown"]
        self.assertLessEqual(text.count("提升质量"), 1)
        self.assertIn("扩写、检查、修订、再输出", text)
        self.assertIn("可渲染、需修订或需补事实", text)
        action_codes = {item["code"] for item in result["report"]["actions"]}
        self.assertIn("merge_repeated_claims", action_codes)
        self.assertIn("complete_action_item_shape", action_codes)
        revision_actions = {item["action"] for item in result["report"]["revision_plan"]}
        self.assertIn("合并重复表达", revision_actions)
        self.assertIn("补齐行动项", revision_actions)
        self.assertEqual(
            len(result["report"]["revision_plan"]),
            len(revision_actions),
            "revision_plan should merge duplicate action types into one actionable item",
        )

    def test_supported_doc_types_get_mvp_templates(self) -> None:
        from formal_expander import expand_formal_markdown

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)

        cases = [
            ("proposal", "需要做一个项目申请，先把为什么做和研究基础理清楚。", ["## 一、立项依据", "## 五、可行性与研究基础"]),
            (
                "technical_disclosure",
                "这个方案想解决现有流程不稳定的问题，但技术效果还没验证。",
                ["## 一、技术问题、目的与背景", "## 三、技术效果与验证需求"],
            ),
            ("abstract", "准备写摘要，先整理对象、方法和结果边界。", ["## 一、对象与问题", "## 三、结果与发现"]),
            ("manual", "想整理成使用说明，但目前只有零散步骤描述。", ["## 一、适用对象", "## 五、异常处理"]),
        ]

        for doc_type, body, headings in cases:
            source = temp_dir / f"{doc_type}.md"
            source.write_text(
                f"---\ndoc_type: {doc_type}\nexpansion_mode: structured\n---\n# 输入\n\n{body}\n",
                encoding="utf-8",
            )
            result = expand_formal_markdown(source)
            self.assertEqual(result["report"]["doc_type"], doc_type)
            for heading in headings:
                self.assertIn(heading, result["expanded_markdown"])

    def test_existing_meeting_note_keeps_original_topic_when_structured(self) -> None:
        from formal_expander import expand_formal_markdown

        result = expand_formal_markdown(SKILL_ROOT / "samples" / "meeting-note.md", "structured")

        text = result["expanded_markdown"]
        self.assertIn("# 会议纪要样例", text)
        self.assertIn("讨论结果", text)
        self.assertIn("后续动作", text)
        self.assertIn("已确认输出层主链", text)
        self.assertNotIn("输出层正式写作质量关建设说明", text)
        self.assertNotIn("原始输入可归纳为", text)

    def test_structured_existing_report_does_not_add_default_fact_placeholders(self) -> None:
        from formal_expander import expand_formal_markdown

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        source = temp_dir / "existing-report.md"
        source.write_text(
            "# 系统运行记录\n\n"
            "## 一、系统概况\n\n"
            "当前链路已完成状态核对。\n\n"
            "## 二、处理方案\n\n"
            "优化后比较结果，确认输出格式稳定。\n\n"
            "## 三、结论与下一步\n\n"
            "后续保留复核记录。\n",
            encoding="utf-8",
        )

        result = expand_formal_markdown(source, "structured")

        action_codes = {item["code"] for item in result["report"]["actions"]}
        self.assertIn("preserve_source_topic", action_codes)
        self.assertNotIn("complete_action_item_shape", action_codes)
        self.assertEqual(result["report"]["blocked_expansions"], [])
        self.assertEqual(result["report"]["revision_plan"], [])

    def test_very_short_input_requests_more_user_facts(self) -> None:
        from formal_expander import expand_formal_markdown

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        source = temp_dir / "short.md"
        source.write_text("---\ndoc_type: formal_report\n---\n要正式一点。\n", encoding="utf-8")

        result = expand_formal_markdown(source)

        self.assertEqual(result["report"]["status"], "needs_user_input")
        self.assertEqual(result["report"]["next_action"], "fill_missing_facts")
        self.assertIn("待补充：", result["expanded_markdown"])

    def test_off_mode_skips_expansion_and_keeps_body(self) -> None:
        from formal_expander import expand_formal_markdown

        result = expand_formal_markdown(FIXTURES_DIR / "too-short-input.md", "off")

        self.assertEqual(result["report"]["status"], "skipped")
        self.assertEqual(result["report"]["next_action"], "render_or_review")
        self.assertIn("这个输出层现在太薄了", result["expanded_markdown"])
        self.assertNotIn("建设目的", result["expanded_markdown"])

    def test_unsupported_claims_are_downgraded_and_human_gated(self) -> None:
        from formal_expander import expand_formal_markdown

        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        source = temp_dir / "claims.md"
        source.write_text(
            (
                "---\n"
                "doc_type: technical_disclosure\n"
                "expansion_mode: structured\n"
                "---\n"
                "# 输入\n\n"
                "实践证明这个方案显著提升效率，已经证明完全解决问题，并且符合申报要求。\n"
            ),
            encoding="utf-8",
        )

        result = expand_formal_markdown(source)

        text = result["expanded_markdown"]
        self.assertNotIn("实践证明", text)
        self.assertNotIn("显著提升", text)
        self.assertNotIn("完全解决", text)
        self.assertIn("待验证", text)
        blocked_reasons = {item["reason"] for item in result["report"]["blocked_expansions"]}
        action_codes = {item["code"] for item in result["report"]["actions"]}
        self.assertIn("缺少事实依据", blocked_reasons)
        self.assertIn("需人工确认", blocked_reasons)
        self.assertIn("downgrade_unsupported_claim", action_codes)
        self.assertIn("mark_human_confirmation", action_codes)
        revision_actions = {item["action"] for item in result["report"]["revision_plan"]}
        self.assertIn("降级结论", revision_actions)
        self.assertIn("人工确认", revision_actions)

    def test_cli_writes_expanded_markdown_and_reports(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(FIXTURES_DIR / "too-short-input.md"),
                "--outdir",
                str(temp_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertIn("status=expanded", result.stdout)
        expanded_path = temp_dir / "output.expanded.md"
        json_path = temp_dir / "formal_expansion_report.json"
        md_path = temp_dir / "formal_expansion_report.md"
        self.assertTrue(expanded_path.exists())
        self.assertTrue(json_path.exists())
        self.assertTrue(md_path.exists())
        expanded_text = expanded_path.read_text(encoding="utf-8")
        self.assertIn("doc_type: formal_report", expanded_text)
        self.assertIn("# 输出层正式写作质量关建设说明", expanded_text)
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "expanded")
        report_text = md_path.read_text(encoding="utf-8")
        self.assertIn("Formal Expansion Report", report_text)
        self.assertIn("Revision Plan", report_text)


if __name__ == "__main__":
    unittest.main()
