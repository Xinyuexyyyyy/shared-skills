import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
import subprocess
from unittest.mock import patch

SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.consensus import save_consensus
from scripts.analyze import (
    build_analysis_summary,
    load_harvest_result,
    infer_repo_profile,
    assess_analysis_readiness,
    format_analysis_input,
    save_analysis_summary,
)
import skill as skill_module
from scripts.harvest import harvest_repo, format_harvest_output, fetch_key_files
from scripts.discover import search_github_repos
from scripts.compare import (
    build_comparison,
    build_consensus_seed,
    build_shortlist_summary,
    format_comparison,
    ensure_analysis_summary_for_repo,
    score_comparison_item,
    normalize_goal,
)
from scripts.utils import normalize_github_repo_url, check_gh_cli_ready


class GuardrailsTest(unittest.TestCase):
    def test_normalize_github_repo_url_accepts_common_forms(self) -> None:
        self.assertEqual(
            normalize_github_repo_url("github.com/openai/openai-python"),
            "https://github.com/openai/openai-python",
        )
        self.assertEqual(
            normalize_github_repo_url("git@github.com:openai/openai-python.git"),
            "https://github.com/openai/openai-python",
        )

    def test_normalize_github_repo_url_rejects_invalid_links(self) -> None:
        self.assertIsNone(normalize_github_repo_url("https://example.com/openai/openai-python"))
        self.assertIsNone(normalize_github_repo_url("https://github.com/openai"))

    def test_harvest_repo_rejects_invalid_repo_url(self) -> None:
        result = harvest_repo("not-a-github-url")
        self.assertTrue(result["errors"])
        self.assertEqual(result["status"], "invalid-input")

    def test_check_gh_cli_ready_reports_missing_binary(self) -> None:
        with patch("scripts.utils.subprocess.run", side_effect=FileNotFoundError()):
            ready, message = check_gh_cli_ready()
        self.assertFalse(ready)
        self.assertIn("gh CLI", message)

    def test_check_gh_cli_ready_reports_auth_failure(self) -> None:
        with patch(
            "scripts.utils.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["gh", "auth", "status"],
                returncode=1,
                stdout="",
                stderr="You are not logged into any GitHub hosts.",
            ),
        ):
            ready, message = check_gh_cli_ready()
        self.assertFalse(ready)
        self.assertIn("未登录", message)

    def test_format_harvest_output_surfaces_warnings(self) -> None:
        text = format_harvest_output(
            {
                "project": "openai/openai-python",
                "readme": {"raw": "hello"},
                "structure": {"root_files": ["README.md"], "directories": ["src"]},
                "code_files": {"files": []},
                "warnings": ["README 未抓到", "核心代码抓取失败"],
            }
        )
        self.assertIn("警告", text)
        self.assertIn("核心代码抓取失败", text)

    def test_format_harvest_output_surfaces_structured_issues(self) -> None:
        text = format_harvest_output(
            {
                "project": "openai/openai-python",
                "readme": {"raw": "hello"},
                "structure": {"root_files": ["README.md"], "directories": ["src"]},
                "code_files": {"files": []},
                "issues": [
                    {
                        "stage": "code_files",
                        "code": "source_samples_missing",
                        "target": "source",
                        "message": "没有抓到实现层源码样本。",
                    }
                ],
            }
        )
        self.assertIn("结构化告警", text)
        self.assertIn("source_samples_missing", text)

    def test_load_harvest_result_does_not_fall_back_when_repo_name_is_missing(self) -> None:
        result = load_harvest_result("missing/repo")
        self.assertIn("error", result)
        self.assertIn("missing/repo", result["error"])

    def test_search_github_repos_returns_structured_status_for_invalid_input(self) -> None:
        result = search_github_repos("", 3)
        self.assertEqual(result["status"], "invalid-input")
        self.assertEqual(result["repos"], [])

    def test_harvest_repo_returns_structured_status_for_invalid_input(self) -> None:
        result = harvest_repo("not-a-github-url")
        self.assertEqual(result["status"], "invalid-input")
        self.assertTrue(result["errors"])

    def test_save_consensus_normalizes_scalar_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            from scripts import consensus as consensus_module

            original_dir = consensus_module.CONSENSUS_OUTPUT_DIR
            consensus_module.CONSENSUS_OUTPUT_DIR = temp_dir
            try:
                result = save_consensus(
                    {
                        "做什么": "验证",
                        "目标": "稳定边界",
                        "从哪里抄": {"直接用": "repo-a", "只参考": "repo-b"},
                    }
                )
                self.assertEqual(result["目标"], ["稳定边界"])
                self.assertEqual(result["从哪里抄"]["直接用"], ["repo-a"])
                self.assertEqual(result["从哪里抄"]["借鉴用"], ["repo-b"])
                output_dir = Path(result["output_dir"])
                self.assertTrue(output_dir.exists())
                self.assertTrue((output_dir / "README.md").exists())
                self.assertTrue((output_dir / "consensus.md").exists())
                self.assertTrue((output_dir / "consensus.json").exists())
                self.assertTrue((Path(temp_dir) / "latest_consensus.json").exists())
            finally:
                consensus_module.CONSENSUS_OUTPUT_DIR = original_dir

    def test_save_consensus_preserves_source_context_and_extra_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            from scripts import consensus as consensus_module

            original_dir = consensus_module.CONSENSUS_OUTPUT_DIR
            consensus_module.CONSENSUS_OUTPUT_DIR = temp_dir
            try:
                result = save_consensus(
                    {
                        "title": "superpowers-harvest-consensus-20260515",
                        "harvest_target": {
                            "repo": "obra/superpowers",
                            "url": "https://github.com/obra/superpowers",
                        },
                        "sources": [
                            "https://github.com/obra/superpowers",
                            "data/harvest_obra_superpowers.json",
                        ],
                    }
                )
                self.assertEqual(result["title"], "superpowers-harvest-consensus-20260515")
                self.assertEqual(result["harvest_target"]["repo"], "obra/superpowers")
                self.assertEqual(result["source_context"]["primary_repo"], "obra/superpowers")
                self.assertIn("obra/superpowers", result["source_context"]["repo_names"])
                self.assertIn(
                    "data/harvest_obra_superpowers.json",
                    result["source_context"]["harvest_files"],
                )
                latest = json.loads((Path(temp_dir) / "latest_consensus.json").read_text(encoding="utf-8"))
                self.assertEqual(latest["source_context"]["primary_repo"], "obra/superpowers")
            finally:
                consensus_module.CONSENSUS_OUTPUT_DIR = original_dir

    def test_fetch_key_files_handles_optional_workflows_and_samples_skills(self) -> None:
        structure = {
            "root_files": ["package.json", "AGENTS.md"],
            "directories": ["skills", ".github", ".codex-plugin"],
        }

        def fake_run(args, capture_output=True, text=True, timeout=10):
            api_path = args[2]
            if api_path.endswith("/contents/skills"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"brainstorming","path":"skills/brainstorming","type":"dir","download_url":null}\n',
                    stderr="",
                )
            if api_path.endswith("/contents/.github/workflows"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=1,
                    stdout="",
                    stderr="gh: Not Found (HTTP 404)",
                )
            raise AssertionError(f"unexpected gh api call: {api_path}")

        with patch("scripts.harvest.subprocess.run", side_effect=fake_run), patch(
            "scripts.harvest.fetch_file_content",
            side_effect=lambda url: f"content for {url}",
        ):
            result = fetch_key_files("obra", "superpowers", structure)

        self.assertNotIn("error", result)
        names = [item["name"] for item in result["files"]]
        self.assertIn("package.json", names)
        self.assertIn("AGENTS.md", names)
        self.assertIn(".codex-plugin/plugin.json", names)
        self.assertIn("skills/brainstorming/SKILL.md", names)

    def test_fetch_key_files_samples_bucketed_skill_directories(self) -> None:
        structure = {
            "root_files": ["CLAUDE.md"],
            "directories": ["skills", ".claude-plugin"],
        }

        def fake_run(args, capture_output=True, text=True, timeout=10):
            api_path = args[2]
            if api_path.endswith("/contents/skills"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout=(
                        '{"name":"engineering","path":"skills/engineering","type":"dir","download_url":null}\n'
                        '{"name":"productivity","path":"skills/productivity","type":"dir","download_url":null}\n'
                    ),
                    stderr="",
                )
            if api_path.endswith("/contents/skills/engineering"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"grill-with-docs","path":"skills/engineering/grill-with-docs","type":"dir","download_url":null}\n',
                    stderr="",
                )
            if api_path.endswith("/contents/skills/productivity"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"handoff","path":"skills/productivity/handoff","type":"dir","download_url":null}\n',
                    stderr="",
                )
            raise AssertionError(f"unexpected gh api call: {api_path}")

        def fake_fetch_file_content(url):
            if url.endswith("/skills/engineering/SKILL.md") or url.endswith("/skills/productivity/SKILL.md"):
                return ""
            return f"content for {url}"

        with patch("scripts.harvest.subprocess.run", side_effect=fake_run), patch(
            "scripts.harvest.fetch_file_content",
            side_effect=fake_fetch_file_content,
        ):
            result = fetch_key_files("mattpocock", "skills", structure)

        sample_names = [item["name"] for item in result["skill_samples"]]
        file_names = [item["name"] for item in result["files"]]
        self.assertIn("skills/engineering/grill-with-docs/SKILL.md", sample_names)
        self.assertIn("skills/productivity/handoff/SKILL.md", sample_names)
        self.assertIn("skills/engineering/grill-with-docs/SKILL.md", file_names)

    def test_fetch_key_files_prioritizes_promoted_skill_buckets(self) -> None:
        structure = {
            "root_files": ["CLAUDE.md"],
            "directories": ["skills"],
        }

        def fake_run(args, capture_output=True, text=True, timeout=10):
            api_path = args[2]
            if api_path.endswith("/contents/skills"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout=(
                        '{"name":"deprecated","path":"skills/deprecated","type":"dir","download_url":null}\n'
                        '{"name":"engineering","path":"skills/engineering","type":"dir","download_url":null}\n'
                        '{"name":"productivity","path":"skills/productivity","type":"dir","download_url":null}\n'
                    ),
                    stderr="",
                )
            if api_path.endswith("/contents/skills/deprecated"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"old","path":"skills/deprecated/old","type":"dir","download_url":null}\n',
                    stderr="",
                )
            if api_path.endswith("/contents/skills/engineering"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"diagnose","path":"skills/engineering/diagnose","type":"dir","download_url":null}\n',
                    stderr="",
                )
            if api_path.endswith("/contents/skills/productivity"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"handoff","path":"skills/productivity/handoff","type":"dir","download_url":null}\n',
                    stderr="",
                )
            raise AssertionError(f"unexpected gh api call: {api_path}")

        def fake_fetch_file_content(url):
            if url.endswith("/skills/deprecated/SKILL.md") or url.endswith("/skills/engineering/SKILL.md") or url.endswith("/skills/productivity/SKILL.md"):
                return ""
            return f"content for {url}"

        with patch("scripts.harvest.subprocess.run", side_effect=fake_run), patch(
            "scripts.harvest.fetch_file_content",
            side_effect=fake_fetch_file_content,
        ):
            result = fetch_key_files("mattpocock", "skills", structure)

        sample_names = [item["name"] for item in result["skill_samples"]]
        self.assertEqual(sample_names[0], "skills/engineering/diagnose/SKILL.md")
        self.assertEqual(sample_names[1], "skills/productivity/handoff/SKILL.md")

    def test_fetch_key_files_reserves_slots_for_source_samples(self) -> None:
        structure = {
            "root_files": [
                "package.json",
                "setup.py",
                "pyproject.toml",
                "go.mod",
                "AGENTS.md",
                "CLAUDE.md",
                "GEMINI.md",
                "gemini-extension.json",
            ],
            "directories": ["skills", ".claude-plugin", ".codex-plugin", ".cursor-plugin"],
        }

        def fake_run(args, capture_output=True, text=True, timeout=10):
            api_path = args[2]
            if api_path.endswith("/contents/skills"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"brainstorming","path":"skills/brainstorming","type":"dir","download_url":null}\n',
                    stderr="",
                )
            raise AssertionError(f"unexpected gh api call: {api_path}")

        with patch("scripts.harvest.subprocess.run", side_effect=fake_run), patch(
            "scripts.harvest.fetch_file_content",
            side_effect=lambda url: f"content for {url}",
        ):
            result = fetch_key_files("obra", "superpowers", structure)

        names = [item["name"] for item in result["files"]]
        self.assertIn("skills/brainstorming/SKILL.md", names)

    def test_infer_repo_profile_detects_skills_framework(self) -> None:
        profile = infer_repo_profile(
            {
                "structure": {
                    "root_files": ["AGENTS.md", "CLAUDE.md"],
                    "directories": ["skills", ".codex-plugin"],
                },
                "code_files": {"files": [{"name": "skills/brainstorming/SKILL.md"}]},
            }
        )
        self.assertEqual(profile["type"], "skills-framework")

    def test_assess_analysis_readiness_marks_missing_material_as_low(self) -> None:
        readiness = assess_analysis_readiness(
            {
                "status": "partial",
                "readme": {"raw": ""},
                "code_files": {"files": []},
                "warnings": ["README 未抓到"],
            }
        )
        self.assertEqual(readiness["level"], "low")

    def test_format_analysis_input_includes_profile_and_readiness(self) -> None:
        text = format_analysis_input(
            {
                "project": "obra/superpowers",
                "status": "ok",
                "readme": {"raw": "Superpowers is a framework"},
                "structure": {
                    "root_files": ["AGENTS.md", "CLAUDE.md"],
                    "directories": ["skills", ".codex-plugin"],
                },
                "code_files": {"files": [{"name": "skills/brainstorming/SKILL.md", "content": "..." }]},
                "warnings": [],
            }
        )
        self.assertIn("仓库画像", text)
        self.assertIn("材料置信度", text)
        self.assertIn("技能/方法论框架仓库", text)

    def test_format_analysis_input_includes_skill_samples_section(self) -> None:
        text = format_analysis_input(
            {
                "project": "mattpocock/skills",
                "status": "ok",
                "readme": {"raw": "Skills for real engineers"},
                "structure": {
                    "root_files": ["CLAUDE.md"],
                    "directories": ["skills", ".claude-plugin"],
                },
                "code_files": {
                    "files": [
                        {
                            "name": "skills/engineering/grill-with-docs/SKILL.md",
                            "content": "---\nname: grill-with-docs\n---",
                        }
                    ],
                    "skill_samples": [
                        {
                            "name": "skills/engineering/grill-with-docs/SKILL.md",
                            "content": "---\nname: grill-with-docs\n---",
                        }
                    ],
                },
                "warnings": [],
            }
        )
        self.assertIn("Skill 样本文件", text)
        self.assertIn("skills/engineering/grill-with-docs/SKILL.md", text)

    def test_format_analysis_input_does_not_duplicate_skill_samples_as_core_files(self) -> None:
        text = format_analysis_input(
            {
                "project": "mattpocock/skills",
                "status": "ok",
                "readme": {"raw": "Skills for real engineers"},
                "structure": {
                    "root_files": ["CLAUDE.md"],
                    "directories": ["skills", ".claude-plugin"],
                },
                "code_files": {
                    "files": [
                        {
                            "name": "skills/engineering/diagnose/SKILL.md",
                            "content": "---\nname: diagnose\n---",
                        },
                        {"name": "scripts/list-skills.sh", "content": "find . -name SKILL.md"},
                    ],
                    "skill_samples": [
                        {
                            "name": "skills/engineering/diagnose/SKILL.md",
                            "content": "---\nname: diagnose\n---",
                        }
                    ],
                },
                "warnings": [],
            }
        )
        self.assertIn("Skill 样本文件", text)
        self.assertIn("核心代码文件（共 1 个）", text)
        self.assertIn("### scripts/list-skills.sh", text)

    def test_save_analysis_summary_writes_profile_and_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            from scripts import analyze as analyze_module

            original_dir = analyze_module.OUTPUT_DIR
            analyze_module.OUTPUT_DIR = temp_dir
            try:
                summary = save_analysis_summary(
                    {
                        "project": "obra/superpowers",
                        "repo_name": "obra/superpowers",
                        "status": "ok",
                        "readme": {"raw": "framework"},
                        "structure": {
                            "root_files": ["AGENTS.md"],
                            "directories": ["skills", ".codex-plugin"],
                        },
                        "code_files": {"files": [{"name": "skills/brainstorming/SKILL.md"}]},
                        "warnings": [],
                    }
                )
                self.assertEqual(summary["profile"]["type"], "skills-framework")
                saved = json.loads((Path(temp_dir) / "analysis_results.json").read_text())
                self.assertEqual(saved["analyses"][0]["readiness"]["level"], "medium")
            finally:
                analyze_module.OUTPUT_DIR = original_dir

    def test_build_analysis_summary_includes_source_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            from scripts import analyze as analyze_module

            original_dir = analyze_module.OUTPUT_DIR
            analyze_module.OUTPUT_DIR = temp_dir
            try:
                summary = build_analysis_summary(
                    {
                        "project": "obra/superpowers",
                        "repo_name": "obra/superpowers",
                        "url": "https://github.com/obra/superpowers",
                        "status": "ok",
                        "readme": {"raw": "framework"},
                        "structure": {
                            "root_files": ["AGENTS.md"],
                            "directories": ["skills", ".codex-plugin"],
                        },
                        "code_files": {"files": [{"name": "skills/brainstorming/SKILL.md"}]},
                    }
                )
                self.assertEqual(summary["source_context"]["project"], "obra/superpowers")
                self.assertTrue(summary["source_context"]["harvest_file"].endswith("harvest_obra_superpowers.json"))
                self.assertTrue(summary["generated_at"])
            finally:
                analyze_module.OUTPUT_DIR = original_dir

    def test_analyze_cmd_saves_analysis_summary(self) -> None:
        with patch("skill.load_harvest_result", return_value={"project": "obra/superpowers"}), patch(
            "skill.save_analysis_summary"
        ) as mock_save, patch("skill.format_analysis_input", return_value="ok"):
            rc = skill_module.analyze_cmd("obra_superpowers")
        self.assertEqual(rc, 0)
        mock_save.assert_called_once()

    def test_build_comparison_selects_requested_repos(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            from scripts import compare as compare_module

            original_dir = compare_module.OUTPUT_DIR
            compare_module.OUTPUT_DIR = temp_dir
            try:
                Path(temp_dir, "analysis_results.json").write_text(
                    json.dumps(
                        {
                            "analyses": [
                                {
                                    "project": "obra/superpowers",
                                    "profile": {"type": "skills-framework", "label": "技能/方法论框架仓库"},
                                    "readiness": {"level": "high"},
                                    "warnings": [],
                                },
                                {
                                    "project": "langchain-ai/open_deep_research",
                                    "profile": {"type": "application", "label": "应用型仓库"},
                                    "readiness": {"level": "medium"},
                                    "warnings": ["partial"],
                                },
                            ]
                        }
                    ),
                    encoding="utf-8",
                )
                payload = build_comparison(["obra/superpowers"])
                self.assertEqual(payload["selected_count"], 1)
                self.assertEqual(payload["comparisons"][0]["project"], "obra/superpowers")
                self.assertIn("score", payload["comparisons"][0])
                self.assertTrue((Path(temp_dir) / "compare_results.json").exists())
            finally:
                compare_module.OUTPUT_DIR = original_dir

    def test_format_comparison_renders_table(self) -> None:
        text = format_comparison(
            {
                "shortlist": {
                    "top_pick": "obra/superpowers",
                    "priority_deep_dive": ["obra/superpowers"],
                    "worth_reference": [],
                    "not_priority": [],
                },
                "consensus_seed": {
                    "从哪里抄": {
                        "直接用": ["obra/superpowers"],
                        "改动用": [],
                        "借鉴用": [],
                    }
                },
                "comparisons": [
                    {
                        "project": "obra/superpowers",
                        "profile_type": "skills-framework",
                        "profile_label": "技能/方法论框架仓库",
                        "readiness_level": "high",
                        "score": 78,
                        "warning_count": 0,
                        "suggested_focus": "优先拆 workflow、skills 分层、多端适配和触发机制",
                        "readiness_note": "这轮材料足够支撑一轮较强判断",
                        "score_reasons": ["置信度 high -> +50", "仓库类型 skills-framework -> +28", "无抓取警告 -> -0"],
                    }
                ]
            }
        )
        self.assertIn("批量比较结果", text)
        self.assertIn("| 排名 | 仓库 | 类型 | 置信度 | 分数 |", text)
        self.assertIn("## Shortlist", text)
        self.assertIn("## 共识草稿输入", text)

    def test_score_comparison_item_prefers_high_readiness_low_warning(self) -> None:
        high_score, _ = score_comparison_item(
            {
                "profile_type": "application",
                "readiness_level": "high",
                "warning_count": 0,
            }
        )
        low_score, _ = score_comparison_item(
            {
                "profile_type": "docs-heavy",
                "readiness_level": "low",
                "warning_count": 2,
            }
        )
        self.assertGreater(high_score, low_score)

    def test_normalize_goal_maps_aliases(self) -> None:
        self.assertEqual(normalize_goal("app"), "application")
        self.assertEqual(normalize_goal("workflow"), "skills-framework")

    def test_score_comparison_item_applies_goal_bonus(self) -> None:
        base_score, _ = score_comparison_item(
            {
                "profile_type": "skills-framework",
                "readiness_level": "high",
                "warning_count": 0,
            }
        )
        goal_score, reasons = score_comparison_item(
            {
                "profile_type": "skills-framework",
                "readiness_level": "high",
                "warning_count": 0,
            },
            goal="workflow",
        )
        self.assertGreater(goal_score, base_score)
        self.assertTrue(any("目标偏好" in reason for reason in reasons))

    def test_build_comparison_marks_missing_repos(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            from scripts import compare as compare_module

            original_dir = compare_module.OUTPUT_DIR
            compare_module.OUTPUT_DIR = temp_dir
            try:
                Path(temp_dir, "analysis_results.json").write_text(
                    json.dumps({"analyses": []}),
                    encoding="utf-8",
                )
                payload = build_comparison(["obra/superpowers"], auto_resolve_missing=False)
                self.assertEqual(payload["missing_repo_names"], ["obra/superpowers"])
            finally:
                compare_module.OUTPUT_DIR = original_dir

    def test_build_comparison_rejects_mismatched_summary_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            from scripts import compare as compare_module

            original_dir = compare_module.OUTPUT_DIR
            compare_module.OUTPUT_DIR = temp_dir
            try:
                Path(temp_dir, "analysis_results.json").write_text(
                    json.dumps(
                        {
                            "analyses": [
                                {
                                    "project": "obra/superpowers",
                                    "repo_name": "obra/superpowers",
                                    "harvest_file": str(Path(temp_dir) / "harvest_someone_else.json"),
                                    "source_context": {
                                        "project": "obra/superpowers",
                                        "repo_name": "obra/superpowers",
                                        "harvest_file": str(Path(temp_dir) / "harvest_someone_else.json"),
                                    },
                                    "profile": {"type": "skills-framework", "label": "技能/方法论框架仓库"},
                                    "readiness": {"level": "high"},
                                    "warnings": [],
                                }
                            ]
                        }
                    ),
                    encoding="utf-8",
                )
                payload = build_comparison(["obra/superpowers"], auto_resolve_missing=False)
                self.assertEqual(payload["selected_count"], 0)
                self.assertIn("obra/superpowers", payload["context_mismatch_repo_names"])
            finally:
                compare_module.OUTPUT_DIR = original_dir

    def test_build_comparison_sorts_by_score_desc(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            from scripts import compare as compare_module

            original_dir = compare_module.OUTPUT_DIR
            compare_module.OUTPUT_DIR = temp_dir
            try:
                Path(temp_dir, "analysis_results.json").write_text(
                    json.dumps(
                        {
                            "analyses": [
                                {
                                    "project": "repo/low",
                                    "profile": {"type": "docs-heavy", "label": "文档/知识仓库"},
                                    "readiness": {"level": "low"},
                                    "warnings": ["w1"],
                                },
                                {
                                    "project": "repo/high",
                                    "profile": {"type": "application", "label": "应用型仓库"},
                                    "readiness": {"level": "high"},
                                    "warnings": [],
                                },
                            ]
                        }
                    ),
                    encoding="utf-8",
                )
                payload = build_comparison(["repo/low", "repo/high"], auto_resolve_missing=False)
                self.assertEqual(payload["comparisons"][0]["project"], "repo/high")
                self.assertGreater(payload["comparisons"][0]["score"], payload["comparisons"][1]["score"])
                self.assertIn("consensus_seed", payload)
            finally:
                compare_module.OUTPUT_DIR = original_dir

    def test_build_shortlist_summary_groups_items(self) -> None:
        shortlist = build_shortlist_summary(
            [
                {"project": "repo/high", "score": 88, "readiness_level": "high", "warning_count": 0},
                {"project": "repo/medium", "score": 60, "readiness_level": "medium", "warning_count": 0},
                {"project": "repo/low", "score": 40, "readiness_level": "low", "warning_count": 2},
            ]
        )
        self.assertEqual(shortlist["top_pick"], "repo/high")
        self.assertIn("repo/high", shortlist["priority_deep_dive"])
        self.assertIn("repo/medium", shortlist["worth_reference"])
        self.assertIn("repo/low", shortlist["not_priority"])

    def test_build_consensus_seed_maps_shortlist_layers(self) -> None:
        seed = build_consensus_seed(
            {
                "goal": "application",
                "repo_names": ["repo/high", "repo/medium", "repo/low"],
                "shortlist": {
                    "top_pick": "repo/high",
                    "priority_deep_dive": ["repo/high"],
                    "worth_reference": ["repo/medium"],
                    "not_priority": ["repo/low"],
                },
                "comparisons": [
                    {"project": "repo/high", "score": 90, "shortlist_bucket": "priority-deep-dive", "shortlist_label": "优先深拆", "suggested_focus": "focus-a"},
                    {"project": "repo/medium", "score": 60, "shortlist_bucket": "worth-reference", "shortlist_label": "值得参考", "suggested_focus": "focus-b"},
                    {"project": "repo/low", "score": 30, "shortlist_bucket": "not-priority", "shortlist_label": "暂不主推", "suggested_focus": "focus-c"},
                ],
            }
        )
        copied_from = seed["从哪里抄"]
        self.assertEqual(copied_from["直接用"], ["repo/high"])
        self.assertEqual(copied_from["改动用"], ["repo/medium"])
        self.assertEqual(copied_from["借鉴用"], ["repo/low"])

    def test_ensure_analysis_summary_for_repo_backfills_legacy_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            from scripts import compare as compare_module

            original_dir = compare_module.OUTPUT_DIR
            compare_module.OUTPUT_DIR = temp_dir
            try:
                Path(temp_dir, "analysis_results.json").write_text(
                    json.dumps(
                        {
                            "analyses": [
                                {
                                    "project": "obra/superpowers",
                                    "repo_name": "obra/superpowers",
                                }
                            ]
                        }
                    ),
                    encoding="utf-8",
                )
                with patch("scripts.compare.load_harvest_result", return_value={"project": "obra/superpowers"}), patch(
                    "scripts.compare.save_analysis_summary",
                    return_value={
                        "project": "obra/superpowers",
                        "profile": {"type": "skills-framework"},
                        "readiness": {"level": "high"},
                    },
                ) as mock_save:
                    summary, error = ensure_analysis_summary_for_repo("obra/superpowers")
                self.assertIsNone(error)
                self.assertEqual(summary["project"], "obra/superpowers")
                mock_save.assert_called_once()
            finally:
                compare_module.OUTPUT_DIR = original_dir

    def test_ensure_analysis_summary_for_repo_backfills_mismatched_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            from scripts import compare as compare_module

            original_dir = compare_module.OUTPUT_DIR
            compare_module.OUTPUT_DIR = temp_dir
            try:
                Path(temp_dir, "analysis_results.json").write_text(
                    json.dumps(
                        {
                            "analyses": [
                                {
                                    "project": "obra/superpowers",
                                    "repo_name": "obra/superpowers",
                                    "harvest_file": str(Path(temp_dir) / "harvest_wrong_repo.json"),
                                    "source_context": {
                                        "project": "obra/superpowers",
                                        "repo_name": "obra/superpowers",
                                        "harvest_file": str(Path(temp_dir) / "harvest_wrong_repo.json"),
                                    },
                                    "profile": {"type": "skills-framework"},
                                    "readiness": {"level": "high"},
                                }
                            ]
                        }
                    ),
                    encoding="utf-8",
                )
                with patch("scripts.compare.load_harvest_result", return_value={"project": "obra/superpowers"}), patch(
                    "scripts.compare.save_analysis_summary",
                    return_value={
                        "project": "obra/superpowers",
                        "repo_name": "obra/superpowers",
                        "harvest_file": str(Path(temp_dir) / "harvest_obra_superpowers.json"),
                        "source_context": {
                            "project": "obra/superpowers",
                            "repo_name": "obra/superpowers",
                            "harvest_file": str(Path(temp_dir) / "harvest_obra_superpowers.json"),
                        },
                        "profile": {"type": "skills-framework"},
                        "readiness": {"level": "high"},
                    },
                ) as mock_save:
                    summary, error = ensure_analysis_summary_for_repo("obra/superpowers")
                self.assertIsNone(error)
                self.assertEqual(summary["project"], "obra/superpowers")
                mock_save.assert_called_once()
            finally:
                compare_module.OUTPUT_DIR = original_dir

    def test_build_comparison_auto_resolves_missing_repo(self) -> None:
        with patch(
            "scripts.compare.ensure_analysis_summary_for_repo",
            return_value=(
                {
                    "project": "langchain-ai/open_deep_research",
                    "repo_name": "langchain-ai/open_deep_research",
                    "profile": {"type": "application", "label": "应用型仓库"},
                    "readiness": {"level": "medium"},
                    "warnings": [],
                },
                None,
            ),
        ), patch(
            "scripts.compare.load_analysis_summaries",
            side_effect=[
                [],
                [
                    {
                        "project": "langchain-ai/open_deep_research",
                        "repo_name": "langchain-ai/open_deep_research",
                        "profile": {"type": "application", "label": "应用型仓库"},
                        "readiness": {"level": "medium"},
                        "warnings": [],
                    }
                ],
            ],
        ), patch("scripts.compare.save_json"):
            payload = build_comparison(["langchain-ai/open_deep_research"])

        self.assertEqual(payload["selected_count"], 1)
        self.assertIn("langchain-ai/open_deep_research", payload["auto_resolved_repo_names"])

    def test_compare_cmd_returns_success_when_comparisons_exist(self) -> None:
        with patch("skill.build_comparison", return_value={"comparisons": [{"project": "obra/superpowers"}]}), patch(
            "skill.format_comparison", return_value="ok"
        ):
            rc = skill_module.compare_cmd(["obra/superpowers"])
        self.assertEqual(rc, 0)

    def test_compare_consensus_cmd_saves_consensus_from_seed(self) -> None:
        payload = {
            "comparisons": [{"project": "obra/superpowers"}],
            "consensus_seed": {"title": "seed-title", "做什么": "验证"},
        }
        with patch("skill.build_comparison", return_value=payload), patch(
            "skill.save_consensus", return_value={"title": "seed-title"}
        ) as mock_save, patch("skill.format_comparison", return_value="compare"), patch(
            "skill.format_consensus_for_review", return_value="consensus"
        ):
            rc = skill_module.compare_consensus_cmd(["obra/superpowers"], "workflow")
        self.assertEqual(rc, 0)
        mock_save.assert_called_once()

    def test_parse_compare_args_extracts_goal(self) -> None:
        repo_names, goal = skill_module._parse_compare_args(
            ["obra/superpowers", "langchain-ai/open_deep_research", "--goal", "application"]
        )
        self.assertEqual(repo_names, ["obra/superpowers", "langchain-ai/open_deep_research"])
        self.assertEqual(goal, "application")

    def test_build_comparison_goal_changes_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            from scripts import compare as compare_module

            original_dir = compare_module.OUTPUT_DIR
            compare_module.OUTPUT_DIR = temp_dir
            try:
                Path(temp_dir, "analysis_results.json").write_text(
                    json.dumps(
                        {
                            "analyses": [
                                {
                                    "project": "repo/app",
                                    "profile": {"type": "application", "label": "应用型仓库"},
                                    "readiness": {"level": "high"},
                                    "warnings": [],
                                },
                                {
                                    "project": "repo/workflow",
                                    "profile": {"type": "skills-framework", "label": "技能/方法论框架仓库"},
                                    "readiness": {"level": "high"},
                                    "warnings": [],
                                },
                            ]
                        }
                    ),
                    encoding="utf-8",
                )
                payload = build_comparison(["repo/app", "repo/workflow"], auto_resolve_missing=False, goal="workflow")
                self.assertEqual(payload["comparisons"][0]["project"], "repo/workflow")
                self.assertEqual(payload["goal"], "skills-framework")
            finally:
                compare_module.OUTPUT_DIR = original_dir

    def test_fetch_key_files_preserves_implementation_samples_when_configs_are_many(self) -> None:
        structure = {
            "root_files": [
                "package.json",
                "setup.py",
                "pyproject.toml",
                "go.mod",
                "AGENTS.md",
                "CLAUDE.md",
                "GEMINI.md",
                "gemini-extension.json",
            ],
            "directories": ["skills", "scripts", ".claude-plugin", ".codex-plugin", ".cursor-plugin"],
        }

        def fake_run(args, capture_output=True, text=True, timeout=10):
            api_path = args[2]
            if api_path.endswith("/contents/skills"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"brainstorming","path":"skills/brainstorming","type":"dir","download_url":null}\n',
                    stderr="",
                )
            if api_path.endswith("/contents/scripts"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"main.py","path":"scripts/main.py","type":"file","download_url":null}\n',
                    stderr="",
                )
            raise AssertionError(f"unexpected gh api call: {api_path}")

        with patch("scripts.harvest.subprocess.run", side_effect=fake_run), patch(
            "scripts.harvest.fetch_file_content",
            side_effect=lambda url: f"content for {url}",
        ):
            result = fetch_key_files("obra", "superpowers", structure)

        names = [item["name"] for item in result["files"]]
        self.assertIn("skills/brainstorming/SKILL.md", names)
        self.assertIn("scripts/main.py", names)

    def test_fetch_key_files_reports_structured_issue_when_directory_listing_fails(self) -> None:
        structure = {
            "root_files": ["package.json"],
            "directories": ["src"],
        }

        def fake_run(args, capture_output=True, text=True, timeout=10):
            api_path = args[2]
            if api_path.endswith("/contents/src"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=1,
                    stdout="",
                    stderr="gh: API rate limit exceeded",
                )
            raise AssertionError(f"unexpected gh api call: {api_path}")

        with patch("scripts.harvest.subprocess.run", side_effect=fake_run), patch(
            "scripts.harvest.fetch_file_content",
            side_effect=lambda url: f"content for {url}",
        ):
            result = fetch_key_files("obra", "superpowers", structure)

        self.assertIn("issues", result)
        self.assertTrue(
            any(
                issue.get("code") == "directory_listing_failed"
                and issue.get("target") == "src"
                for issue in result["issues"]
            )
        )

    def test_fetch_key_files_descends_one_level_for_nested_source_samples(self) -> None:
        structure = {
            "root_files": ["package.json"],
            "directories": ["src", "tests"],
        }

        def fake_run(args, capture_output=True, text=True, timeout=10):
            api_path = args[2]
            if api_path.endswith("/contents/src"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"cli","path":"src/cli","type":"dir","download_url":null}\n',
                    stderr="",
                )
            if api_path.endswith("/contents/src/cli"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"main.ts","path":"src/cli/main.ts","type":"file","download_url":null}\n',
                    stderr="",
                )
            if api_path.endswith("/contents/tests"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"unit","path":"tests/unit","type":"dir","download_url":null}\n',
                    stderr="",
                )
            if api_path.endswith("/contents/tests/unit"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"test_parser.py","path":"tests/unit/test_parser.py","type":"file","download_url":null}\n',
                    stderr="",
                )
            raise AssertionError(f"unexpected gh api call: {api_path}")

        with patch("scripts.harvest.subprocess.run", side_effect=fake_run), patch(
            "scripts.harvest.fetch_file_content",
            side_effect=lambda url: f"content for {url}",
        ):
            result = fetch_key_files("obra", "superpowers", structure)

        names = [item["name"] for item in result["files"]]
        self.assertIn("src/cli/main.ts", names)
        self.assertIn("tests/unit/test_parser.py", names)

    def test_fetch_key_files_descends_one_level_for_nested_docs_samples(self) -> None:
        structure = {
            "root_files": [],
            "directories": ["docs"],
        }

        def fake_run(args, capture_output=True, text=True, timeout=10):
            api_path = args[2]
            if api_path.endswith("/contents/docs"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout=(
                        '{"name":"spec","path":"docs/spec","type":"dir","download_url":null}\n'
                        '{"name":"guides","path":"docs/guides","type":"dir","download_url":null}\n'
                    ),
                    stderr="",
                )
            if api_path.endswith("/contents/docs/spec"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"ARCHITECTURE.md","path":"docs/spec/ARCHITECTURE.md","type":"file","download_url":null}\n',
                    stderr="",
                )
            if api_path.endswith("/contents/docs/guides"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout='{"name":"QUICKSTART.md","path":"docs/guides/QUICKSTART.md","type":"file","download_url":null}\n',
                    stderr="",
                )
            raise AssertionError(f"unexpected gh api call: {api_path}")

        with patch("scripts.harvest.subprocess.run", side_effect=fake_run), patch(
            "scripts.harvest.fetch_file_content",
            side_effect=lambda url: f"content for {url}",
        ):
            result = fetch_key_files("obra", "superpowers", structure)

        names = [item["name"] for item in result["files"]]
        self.assertIn("docs/spec/ARCHITECTURE.md", names)
        self.assertIn("docs/guides/QUICKSTART.md", names)


if __name__ == "__main__":
    unittest.main()
