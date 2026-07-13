from __future__ import annotations

import json
import subprocess
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


SKILL_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path.cwd()
SCRIPT = SKILL_ROOT / "scripts" / "render_markdown_output.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
RULES = "总标题黑体小二，正文仿宋GB2312小四，一级标题依赖正文，字体加粗，一级标题字号三号，段落规则固定28磅，非标题正文首行缩进2字符，标题段前空10磅段后空14磅，一级标题用一、二、三、，二级标题用1. 2. 3.，页码启用"
WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _docx_rows(docx_path: Path) -> list[dict[str, str | int | None]]:
    rows: list[dict[str, str | int | None]] = []
    with ZipFile(docx_path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    for paragraph in root.findall(".//w:body/w:p", WORD_NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", WORD_NS)).strip()
        ppr = paragraph.find("w:pPr", WORD_NS)
        style = None
        level: int | None = None
        if ppr is not None:
            pstyle = ppr.find("w:pStyle", WORD_NS)
            if pstyle is not None:
                style = pstyle.attrib.get(f"{{{WORD_NS['w']}}}val")
            numpr = ppr.find("w:numPr", WORD_NS)
            if numpr is not None:
                ilvl = numpr.find("w:ilvl", WORD_NS)
                if ilvl is not None:
                    level = int(ilvl.attrib.get(f"{{{WORD_NS['w']}}}val", "0"))
        rows.append({"text": text, "style": style, "level": level})
    return rows


def _docx_table_count(docx_path: Path) -> int:
    with ZipFile(docx_path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    return len(root.findall(".//w:tbl", WORD_NS))


class RenderMarkdownOutputRegressionTest(unittest.TestCase):
    def _run_renderer(self, input_path: Path, outputs: str = "markdown,docx") -> Path:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(input_path),
                "--profile",
                "formal-zh",
                "--to",
                outputs,
                "--rules",
                RULES,
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)
        return run_dir

    def test_sample_source_smoke(self) -> None:
        run_dir = self._run_renderer(SKILL_ROOT / "samples" / "source.md")
        self.assertTrue((run_dir / "output.clean.md").exists())
        self.assertTrue((run_dir / "output.docx").exists())
        self.assertTrue((run_dir / "index.md").exists())

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["statuses"]["markdown"]["status"], "written")
        self.assertEqual(payload["statuses"]["docx"]["status"], "written")
        self.assertEqual(payload["docx_reference"]["mode"], "generated")
        self.assertTrue((run_dir / "formal-zh-reference.docx").exists())

        index_text = (run_dir / "index.md").read_text(encoding="utf-8")
        self.assertIn("clean markdown", index_text)
        self.assertIn("manifest.json", index_text)

        rows = _docx_rows(run_dir / "output.docx")
        self.assertEqual(rows[0]["style"], "Title")
        self.assertTrue(any(row["style"] == "Heading2" and row["text"] == "1. 二级标题样例" for row in rows))

    def test_core_fixture_docx_matches_formal_rules(self) -> None:
        run_dir = self._run_renderer(FIXTURES_DIR / "formal-zh-core.md")
        clean_text = (run_dir / "output.clean.md").read_text(encoding="utf-8")
        self.assertIn("# 一、系统概况", clean_text)
        self.assertIn("# 二、Agents (3 个活跃)", clean_text)
        self.assertIn("\n\n- 默认 agent 使用 `kimi-coding` 为主模型", clean_text)
        self.assertIn("\n\n> 生成时间：2026-04-29", clean_text)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("总标题改为黑体小二", payload["rule_override_notes"])
        self.assertIn("首行缩进改为两字符", payload["rule_override_notes"])

        rows = _docx_rows(run_dir / "output.docx")
        self.assertIn({"text": "生成时间：2026-04-29", "style": "BlockText", "level": None}, rows)
        self.assertIn({"text": "扫描目标：userysys@100.113.27.115 (Tailscale)", "style": "BlockText", "level": None}, rows)
        self.assertTrue(any(row["text"].endswith("系统概况") and row["style"] == "Heading1" for row in rows))
        self.assertTrue(any(row["text"] == "模型路由配置：" and row["style"] == "BodyText" for row in rows))
        self.assertTrue(any(row["text"] == "默认 agent 使用 kimi-coding 为主模型" and row["style"] == "Compact" and row["level"] == 0 for row in rows))
        self.assertTrue(any(row["style"] == "SourceCode" and "storage:" in row["text"] for row in rows))

    def test_structure_fixture_covers_nested_lists_tables_quotes_and_code(self) -> None:
        run_dir = self._run_renderer(FIXTURES_DIR / "formal-zh-structure.md")
        clean_text = (run_dir / "output.clean.md").read_text(encoding="utf-8")
        self.assertIn("# 一、一级结构", clean_text)
        self.assertIn("# 二、二级结构", clean_text)
        self.assertIn("## 1. 三级标题样例", clean_text)
        self.assertIn("  - 二级列表 A1", clean_text)
        self.assertIn("    - 三级列表 A1a", clean_text)
        self.assertIn("\n> 引用一\n\n> 引用二", clean_text)
        self.assertIn("```text", clean_text)

        rows = _docx_rows(run_dir / "output.docx")
        self.assertEqual(_docx_table_count(run_dir / "output.docx"), 1)
        levels = sorted({row["level"] for row in rows if row["level"] is not None})
        self.assertIn(0, levels)
        self.assertIn(1, levels)
        self.assertTrue(any(row["style"] in {"BlockText", "Quote"} and row["text"] == "引用一" for row in rows))
        self.assertTrue(any(row["style"] == "SourceCode" and row["text"].startswith("line 1") for row in rows))

    def test_formal_report_sample_uses_all_default_outputs(self) -> None:
        run_dir = self._run_renderer(SKILL_ROOT / "samples" / "formal-report.md", "markdown,obsidian,docx,pdf")
        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["statuses"]["markdown"]["status"], "written")
        self.assertEqual(payload["statuses"]["docx"]["status"], "written")
        self.assertEqual(payload["statuses"]["pdf"]["status"], "written")
        self.assertTrue((run_dir / "output.pdf").exists())
        self.assertTrue((run_dir / "output.docx").exists())

    def test_default_docx_uses_shared_reference_template(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(SKILL_ROOT / "samples" / "formal-report.md"),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["docx_reference"]["mode"], "template")
        self.assertTrue(payload["docx_reference"]["path"].endswith("templates/docx/formal-zh-reference.docx"))
        self.assertTrue((run_dir / "formal-zh-reference.docx").exists())
        self.assertTrue((run_dir / "output.docx").exists())

    def test_meeting_note_sample_keeps_short_form_readable(self) -> None:
        run_dir = self._run_renderer(SKILL_ROOT / "samples" / "meeting-note.md")
        clean_text = (run_dir / "output.clean.md").read_text(encoding="utf-8")
        self.assertIn("# 会议纪要样例", clean_text)
        self.assertIn("已确认输出层主链", clean_text)
        self.assertIn("已确认 PDF 后端使用本机 weasyprint", clean_text)

    def test_docx_quality_check_auto_writes_report_without_blocking_docx(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(SKILL_ROOT / "tests" / "fixtures" / "docx-quality" / "draft-proposal.md"),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--docx-quality-check",
                "auto",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["docx_quality_check"]["mode"], "auto")
        self.assertEqual(payload["docx_quality_check"]["status"], "draft_only")
        self.assertEqual(payload["statuses"]["docx_quality_check"]["status"], "written")
        self.assertEqual(payload["statuses"]["docx"]["status"], "written")
        self.assertTrue((run_dir / "docx_quality_report.json").exists())
        self.assertTrue((run_dir / "docx_quality_report.md").exists())

    def test_docx_quality_check_strict_skips_docx_when_blocked(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(SKILL_ROOT / "tests" / "fixtures" / "docx-quality" / "blocked-structure.md"),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--docx-quality-check",
                "strict",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["docx_quality_check"]["mode"], "strict")
        self.assertEqual(payload["docx_quality_check"]["status"], "blocked")
        self.assertEqual(payload["statuses"]["docx_quality_check"]["status"], "written")
        self.assertEqual(payload["statuses"]["docx"]["status"], "skipped")
        self.assertEqual(payload["statuses"]["docx"]["reason"], "docx_quality_check_blocked")
        self.assertFalse((run_dir / "output.docx").exists())
        self.assertTrue((run_dir / "docx_quality_report.json").exists())

    def test_docx_quality_auto_allows_renderable_table_fixture_to_write_docx(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(SKILL_ROOT / "tests" / "fixtures" / "docx-quality" / "renderable-table-caption.md"),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--docx-quality-check",
                "auto",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["statuses"]["docx_quality_check"]["status"], "written")
        self.assertEqual(payload["statuses"]["docx"]["status"], "written")
        self.assertTrue((run_dir / "output.docx").exists())

    def test_assisted_quality_review_auto_writes_report_without_blocking_docx(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(SKILL_ROOT / "tests" / "fixtures" / "docx-quality" / "assisted-proposal-incomplete.md"),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--assisted-quality-review",
                "auto",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["assisted_quality_review"]["mode"], "auto")
        self.assertEqual(payload["assisted_quality_review"]["status"], "needs_revision")
        self.assertEqual(payload["statuses"]["assisted_quality_review"]["status"], "written")
        self.assertEqual(payload["statuses"]["docx"]["status"], "written")
        self.assertTrue((run_dir / "assisted_quality_report.json").exists())
        self.assertTrue((run_dir / "assisted_quality_report.md").exists())

    def test_assisted_quality_review_strict_skips_docx_when_revision_needed(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(SKILL_ROOT / "tests" / "fixtures" / "docx-quality" / "assisted-proposal-incomplete.md"),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--assisted-quality-review",
                "strict",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["assisted_quality_review"]["mode"], "strict")
        self.assertEqual(payload["assisted_quality_review"]["status"], "needs_revision")
        self.assertEqual(payload["statuses"]["assisted_quality_review"]["status"], "written")
        self.assertEqual(payload["statuses"]["docx"]["status"], "skipped")
        self.assertEqual(payload["statuses"]["docx"]["reason"], "assisted_quality_review_needs_revision")
        self.assertFalse((run_dir / "output.docx").exists())

    def test_formal_expansion_structured_writes_expanded_markdown_and_report(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(SKILL_ROOT / "tests" / "fixtures" / "formal-expansion" / "too-short-input.md"),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--formal-expansion",
                "structured",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["formal_expansion"]["mode"], "structured")
        self.assertEqual(payload["formal_expansion"]["status"], "expanded")
        self.assertEqual(payload["statuses"]["formal_expansion"]["status"], "written")
        self.assertEqual(payload["statuses"]["docx"]["status"], "written")
        self.assertEqual(payload["statuses"]["formal_expansion_input"]["status"], "written")
        self.assertTrue((run_dir / "output.expanded.md").exists())
        self.assertTrue((run_dir / "formal_expansion_report.json").exists())
        self.assertTrue((run_dir / "formal_expansion_report.md").exists())
        self.assertTrue((run_dir / "formal-expansion-input.md").exists())
        clean_text = (run_dir / "output.clean.md").read_text(encoding="utf-8")
        self.assertIn("输出层正式写作质量关建设说明", clean_text)
        self.assertIn("不新增未经提供的事实、数据、政策或结论", clean_text)
        index_text = (run_dir / "index.md").read_text(encoding="utf-8")
        self.assertIn("formal expansion input", index_text)
        self.assertIn("formal expansion report json", index_text)
        self.assertIn("formal expansion report markdown", index_text)

    def test_quality_gates_use_expanded_markdown_when_formal_expansion_is_enabled(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(SKILL_ROOT / "tests" / "fixtures" / "formal-expansion" / "too-short-input.md"),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--formal-expansion",
                "structured",
                "--docx-quality-check",
                "auto",
                "--assisted-quality-review",
                "auto",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["formal_expansion"]["status"], "expanded")
        self.assertEqual(payload["statuses"]["docx_quality_check"]["status"], "written")
        self.assertEqual(payload["statuses"]["assisted_quality_review"]["status"], "written")
        self.assertEqual(payload["statuses"]["docx"]["status"], "written")
        self.assertEqual(payload["delivery_recommendation"]["status"], "needs_input")
        self.assertTrue(payload["delivery_recommendation"]["priority_actions"])
        self.assertEqual(payload["statuses"]["docx_quality_input"]["status"], "written")
        self.assertEqual(payload["statuses"]["assisted_quality_input"]["status"], "written")
        quality_input = (run_dir / "docx-quality-input.md").read_text(encoding="utf-8")
        assisted_input = (run_dir / "assisted-quality-input.md").read_text(encoding="utf-8")
        self.assertIn("输出层正式写作质量关建设说明", quality_input)
        self.assertIn("输出层正式写作质量关建设说明", assisted_input)
        index_text = (run_dir / "index.md").read_text(encoding="utf-8")
        self.assertIn("docx quality report json", index_text)
        self.assertIn("assisted quality report json", index_text)
        self.assertIn("## Delivery Recommendation", index_text)
        self.assertIn("- Status: needs_input", index_text)
        self.assertIn("补充事实依据", index_text)

    def test_delivery_recommendation_warns_on_human_review_items(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        source = Path(temp_dir) / "runtime-report.md"
        source.write_text(
            "# 系统运行记录\n\n"
            "## 一、系统概况\n\n"
            "当前版本号为 v1.2.3，服务监听 127.0.0.1:18789，主进程 PID 1470。\n\n"
            "## 二、文档目的\n\n"
            "本记录用于说明当前系统运行状态。\n\n"
            "## 三、处理依据\n\n"
            "本记录依据当前运行日志和状态输出整理。\n\n"
            "## 四、处理方案\n\n"
            "已完成状态核对并保留验证路径。\n\n"
            "## 五、结论与下一步\n\n"
            "后续按运行记录继续复核。\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(source),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--assisted-quality-review",
                "auto",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["assisted_quality_review"]["status"], "needs_human_review")
        self.assertEqual(payload["delivery_recommendation"]["status"], "deliverable_with_review")
        self.assertIn(
            "人工复核事实、版本、端口、PID、政策或机构口径后再正式交付。",
            payload["delivery_recommendation"]["priority_actions"],
        )
        index_text = (run_dir / "index.md").read_text(encoding="utf-8")
        self.assertIn("需人工复核", index_text)

    def test_delivery_recommendation_uses_content_revision_for_quality_warnings(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        source = Path(temp_dir) / "thin-report.md"
        source.write_text("# 产品调研总报告\n\n## 1. 先说结论\n\n当前建议先补真实用户和验证计划。\n", encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(source),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--docx-quality-check",
                "auto",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["docx_quality_check"]["status"], "draft_only")
        self.assertEqual(payload["delivery_recommendation"]["status"], "needs_content_revision")

    def test_formal_revision_auto_writes_revised_markdown_and_uses_it_for_rendering(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        source = Path(temp_dir) / "thin-report.md"
        source.write_text("# 产品调研总报告\n\n## 1. 先说结论\n\n当前建议先补真实用户和验证计划。\n", encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(source),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--docx-quality-check",
                "auto",
                "--formal-revision",
                "auto",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["formal_revision"]["status"], "revised")
        self.assertEqual(payload["statuses"]["formal_revision"]["status"], "written")
        self.assertTrue((run_dir / "output.revised.md").exists())
        self.assertTrue((run_dir / "formal_revision_report.json").exists())
        clean_text = (run_dir / "output.clean.md").read_text(encoding="utf-8")
        self.assertIn("待补充：背景", clean_text)
        self.assertIn("formal revision", (run_dir / "index.md").read_text(encoding="utf-8"))

    def test_formal_revision_auto_consumes_assisted_and_expansion_reports(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(SKILL_ROOT / "tests" / "fixtures" / "docx-quality" / "assisted-manual-incomplete.md"),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--formal-expansion",
                "structured",
                "--docx-quality-check",
                "auto",
                "--assisted-quality-review",
                "auto",
                "--formal-revision",
                "auto",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["formal_revision"]["status"], "revised")
        revised = (run_dir / "output.revised.md").read_text(encoding="utf-8")
        self.assertIn("## 待补充：前置条件", revised)
        self.assertIn("## 待补充：异常处理", revised)
        self.assertIn("## 人工修订清单", revised)
        self.assertIn("补充事实依据：补充可复核的真实样例", revised)
        self.assertNotIn("数据显示", revised)
        report = json.loads((run_dir / "formal_revision_report.json").read_text(encoding="utf-8"))
        action_codes = {item["code"] for item in report["actions"]}
        self.assertIn("add_assisted_missing_element_placeholders", action_codes)
        self.assertIn("add_revision_plan_checklist", action_codes)

    def test_report_only_skips_formal_expansion_and_quality_layers(self) -> None:
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outdir = Path(temp_dir) / "runs"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(SKILL_ROOT / "tests" / "fixtures" / "formal-expansion" / "too-short-input.md"),
                "--profile",
                "formal-zh",
                "--to",
                "markdown,docx",
                "--style-correction-report",
                "only",
                "--formal-expansion",
                "structured",
                "--docx-quality-check",
                "auto",
                "--assisted-quality-review",
                "auto",
                "--outdir",
                str(outdir),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        run_dir = None
        for line in result.stdout.splitlines():
            if line.startswith("run_dir="):
                run_dir = Path(line.split("=", 1)[1].strip())
                break
        self.assertIsNotNone(run_dir, result.stdout)

        payload = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["formal_expansion"]["status"], "not_run")
        self.assertEqual(payload["statuses"]["formal_expansion"]["status"], "skipped")
        self.assertEqual(payload["statuses"]["docx_quality_check"]["status"], "skipped")
        self.assertEqual(payload["statuses"]["assisted_quality_review"]["status"], "skipped")
        self.assertFalse((run_dir / "formal_expansion_report.json").exists())
        self.assertFalse((run_dir / "docx_quality_report.json").exists())
        self.assertFalse((run_dir / "assisted_quality_report.json").exists())
