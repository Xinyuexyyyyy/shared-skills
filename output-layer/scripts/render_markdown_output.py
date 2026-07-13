#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from artifact_writer import create_run_dir, write_manifest
from markdown_renderer import render_clean_markdown
from obsidian_renderer import render_obsidian
from pandoc_renderer import render_docx, render_pdf
from profile_resolver import resolve_profile, resolve_render_plan
from rule_overrides import apply_rule_overrides
from source_loader import load_markdown
from style_corrector import apply_style_correction
from version_hygiene import archive_artifact_dirs, enforce_single_version_names
from zhlint_processor import run_zhlint_fix
from docx_quality_checker import check_docx_quality, write_quality_reports
from formal_assisted_reviewer import assist_docx_quality_review, write_assisted_reports
from formal_expander import expand_formal_markdown, write_expansion_outputs
from formal_revision_planner import revise_formal_markdown, write_revision_outputs


def _render_style_correction_report_markdown(report_payload: dict) -> str:
    style = report_payload.get("style_correction", {}) if isinstance(report_payload.get("style_correction"), dict) else {}
    summary = style.get("summary", {}) if isinstance(style.get("summary"), dict) else {}
    findings = style.get("findings", []) if isinstance(style.get("findings"), list) else []
    next_actions = summary.get("next_actions", []) if isinstance(summary.get("next_actions"), list) else []

    lines: list[str] = [
        "# Style Correction Report",
        "",
        f"- Source: {report_payload.get('source_path', '')}",
        f"- Profile: {report_payload.get('profile', '')}",
        f"- Preset: {style.get('preset', '')}",
        f"- Enabled: {style.get('enabled', False)}",
        f"- Changed: {style.get('changed', False)}",
        "",
        "## Summary",
        "",
        f"- Findings: {summary.get('count', 0)}",
        f"- Top issue: {summary.get('top_kind', '') or 'none'}",
        f"- Top severity: {summary.get('top_severity', '') or 'none'}",
    ]

    if next_actions:
        lines.extend(["", "## Next Actions", ""])
        lines.extend(f"- {action}" for action in next_actions)

    lines.extend(["", "## Findings", ""])
    if findings:
        for index, finding in enumerate(findings, start=1):
            lines.append(f"### {index}. {finding.get('kind', 'unknown')}")
            lines.append("")
            lines.append(f"- Severity: {finding.get('severity', '')}")
            lines.append(f"- Message: {finding.get('message', '')}")
            if finding.get("sample"):
                lines.append(f"- Sample: {finding.get('sample')}")
            details = finding.get("details")
            if isinstance(details, list) and details:
                detail_text = ", ".join(
                    f"{item.get('phrase', '')} x{item.get('count', '')}" for item in details if isinstance(item, dict)
                )
                lines.append(f"- Details: {detail_text}")
            lines.append("")
    else:
        lines.append("- No findings.")
        lines.append("")

    lines.extend(["## Applied Rewrites", ""])
    notes = style.get("applied_notes", []) if isinstance(style.get("applied_notes"), list) else []
    if notes:
        lines.extend(f"- {note}" for note in notes)
    else:
        lines.append("- No rewrites applied.")

    return "\n".join(lines).rstrip() + "\n"


def _markdown_with_frontmatter(frontmatter: dict, body: str) -> str:
    if not frontmatter:
        return body
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"- {item}" for item in value)
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append(body)
    return "\n".join(lines)


NEXT_ACTION_LABELS = {
    "revise_text": "修订正文结构和表达后再正式交付。",
    "human_review": "人工复核事实、版本、端口、PID、政策或机构口径后再正式交付。",
    "fill_missing_facts": "补充缺失事实、样例、验证记录或来源依据。",
    "quality_check": "进入质量门检查。",
    "render_docx": "可以进入 docx 渲染。",
    "render_or_deterministic_check": "可继续渲染，或按需进行确定性质量检查。",
    "render_or_review": "可继续渲染，或先人工审阅。",
}


def _action_label(action: object) -> str:
    text = str(action).strip()
    return NEXT_ACTION_LABELS.get(text, text)


def _build_delivery_recommendation(
    *,
    requested_outputs: list[str],
    statuses: dict[str, dict[str, str]],
    formal_expansion: dict,
    docx_quality_check: dict,
    assisted_quality_review: dict,
    report_only: bool,
) -> dict[str, object]:
    if report_only:
        return {
            "status": "report_only",
            "summary": "本次仅生成诊断报告，未进入正式交付渲染。",
            "priority_actions": ["根据 style_correction_report.md 处理表达问题后再渲染正式文件。"],
        }

    priority_actions: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    needs_input = False
    needs_content_revision = False
    needs_human_review = False

    docx_status = statuses.get("docx", {})
    if "docx" in requested_outputs and docx_status.get("status") in {"skipped", "blocked", "failed"}:
        reason = docx_status.get("reason") or "docx_not_written"
        blockers.append(f"docx 未生成：{reason}")

    if docx_quality_check.get("status") == "blocked":
        blockers.append("docx 确定性质量门阻断。")
        if docx_quality_check.get("next_action"):
            priority_actions.append(_action_label(docx_quality_check["next_action"]))
    elif docx_quality_check.get("status") == "draft_only":
        needs_content_revision = True
        warnings.append("docx 确定性质量门提示当前稿件仍偏草稿。")
        if docx_quality_check.get("next_action"):
            priority_actions.append(_action_label(docx_quality_check["next_action"]))

    if assisted_quality_review.get("status") == "needs_revision":
        needs_content_revision = True
        if assisted_quality_review.get("mode") == "strict":
            blockers.append("方法论辅助审查要求先修订。")
        else:
            warnings.append("方法论辅助审查建议修订。")
        if assisted_quality_review.get("next_action"):
            priority_actions.append(_action_label(assisted_quality_review["next_action"]))
    elif assisted_quality_review.get("status") == "needs_human_review":
        needs_human_review = True
        warnings.append("方法论辅助审查提示存在需人工复核的事实、版本、接口或机构口径。")
        if assisted_quality_review.get("next_action"):
            priority_actions.append(_action_label(assisted_quality_review["next_action"]))

    if formal_expansion.get("status") == "needs_user_input":
        needs_input = True
        warnings.append("正式扩写层发现关键信息不足。")
    revision_plan = formal_expansion.get("revision_plan", [])
    if isinstance(revision_plan, list) and revision_plan:
        warnings.append("正式扩写层生成了人工修订计划。")
        for item in revision_plan:
            if not isinstance(item, dict):
                continue
            action = str(item.get("action", "")).strip()
            instruction = str(item.get("instruction", "")).strip()
            if action and instruction:
                priority_actions.append(f"{action}：{instruction}")
            elif action:
                priority_actions.append(action)
            if action in {"补充事实依据", "人工确认"}:
                needs_input = True
            elif action:
                needs_content_revision = True

    deduped_actions: list[str] = []
    for action in priority_actions:
        if action and action not in deduped_actions:
            deduped_actions.append(action)

    if blockers:
        status = "blocked"
        summary = "正式交付已阻断，需先处理质量门或渲染问题。"
    elif needs_input:
        status = "needs_input"
        summary = "文件已生成，但关键信息不足，需先补事实、依据或人工确认项。"
    elif needs_content_revision:
        status = "needs_content_revision"
        summary = "文件已生成，但正文结构或表达仍需修订后再正式交付。"
    elif needs_human_review:
        status = "deliverable_with_review"
        summary = "文件已生成，结构可交付，但正式交付前需人工复核事实口径。"
    else:
        status = "deliverable"
        summary = "本次输出未发现阻断项，可作为当前版本交付。"

    return {
        "status": status,
        "summary": summary,
        "blockers": blockers,
        "warnings": warnings,
        "priority_actions": deduped_actions[:8],
        "category": status,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render confirmed Markdown into output-layer artifacts.")
    parser.add_argument("input", help="Markdown source path")
    parser.add_argument("--profile", default="formal-zh", help="Profile name")
    parser.add_argument("--to", default="", help="Comma-separated outputs, e.g. markdown,obsidian,docx,pdf")
    parser.add_argument("--rules", default="", help="Natural-language rule overrides, e.g. '宋体小四，1.5倍行距，首行缩进两字符'")
    parser.add_argument("--style-correction", default="", help="Style correction preset override: auto/off/<preset>")
    parser.add_argument("--style-correction-report", default="", help="Style correction report mode: only")
    parser.add_argument(
        "--docx-quality-check",
        default="off",
        choices=["off", "auto", "strict"],
        help="Run docx quality check before rendering docx: off/auto/strict",
    )
    parser.add_argument(
        "--assisted-quality-review",
        default="off",
        choices=["off", "auto", "strict"],
        help="Run methodology-grounded assisted review before rendering docx: off/auto/strict",
    )
    parser.add_argument(
        "--formal-expansion",
        default="off",
        choices=["off", "conservative", "structured"],
        help="Expand short or informal Markdown before quality checks and rendering: off/conservative/structured",
    )
    parser.add_argument(
        "--formal-revision",
        default="off",
        choices=["off", "auto"],
        help="Create a deterministic revised draft from quality reports before rendering: off/auto",
    )
    parser.add_argument("--template", default="", help="Preset docx template: formal-zh, formal-zh-no-number, academic-zh, memo-zh")
    parser.add_argument("--outdir", default=str(ROOT / "output" / "output-layer"), help="Output base directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    document = load_markdown(args.input)
    profile = resolve_profile(args.profile, str(Path(__file__).resolve().parents[1] / "profiles"))
    plan = resolve_render_plan(document, profile, args.to or None)
    resolved_rules, rule_notes = apply_rule_overrides(plan["rules"], args.rules)
    plan["rules"] = resolved_rules
    run_dir = create_run_dir(args.outdir, document["source_path"])

    style_config = dict(plan.get("style_correction", {}) or {})
    if args.style_correction:
        override = args.style_correction.strip()
        if override.lower() == "off":
            style_config["enabled"] = "off"
        elif override.lower() == "auto":
            style_config["enabled"] = "on"
        else:
            style_config["enabled"] = "on"
            style_config["preset"] = override

    corrected_body, style_meta = apply_style_correction(
        document["body"],
        style_config,
        str(Path(__file__).resolve().parents[1] / "profiles" / "style-correction"),
    )

    source_copy = run_dir / "source.md"
    source_copy.write_text(document["raw_text"], encoding="utf-8")
    corrected_path = run_dir / "output.corrected.md"
    corrected_path.write_text(corrected_body, encoding="utf-8")

    # B path: zhlint auto-fix
    zhlint_body, zhlint_report = run_zhlint_fix(corrected_body, run_dir)
    zhlint_path = run_dir / "output.zhlint.md"
    zhlint_path.write_text(zhlint_body, encoding="utf-8")
    zhlint_report_path = run_dir / "zhlint_report.json"
    zhlint_report_path.write_text(json.dumps(zhlint_report, ensure_ascii=False, indent=2), encoding="utf-8")

    report_mode = args.style_correction_report.strip().lower()
    report_only = report_mode == "only"
    report_path = run_dir / "style_correction_report.json"
    report_payload = {
        "source_path": document["source_path"],
        "profile": plan["profile_name"],
        "style_correction": style_meta,
    }
    report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md_path = run_dir / "style_correction_report.md"
    report_md_path.write_text(_render_style_correction_report_markdown(report_payload), encoding="utf-8")

    artifacts: dict[str, str] = {}
    statuses: dict[str, dict[str, str]] = {}
    docx_reference_meta = {"mode": "none", "path": ""}
    artifacts["source"] = str(source_copy)
    artifacts["style_corrected"] = str(corrected_path)
    statuses["style_corrected"] = {"status": "written" if style_meta.get("enabled") else "skipped"}
    artifacts["style_correction_report"] = str(report_path)
    artifacts["style_correction_report_md"] = str(report_md_path)
    statuses["style_correction_report"] = {"status": "written"}
    statuses["style_correction_report_md"] = {"status": "written"}
    artifacts["zhlint"] = str(zhlint_path)
    artifacts["zhlint_report"] = str(zhlint_report_path)
    statuses["zhlint"] = {"status": zhlint_report.get("status", "unknown")}
    statuses["zhlint_report"] = {"status": "written"}
    formal_expansion_meta = {"mode": args.formal_expansion, "status": "not_run", "path": ""}
    content_body = zhlint_body
    content_frontmatter = document.get("frontmatter", {})

    if args.formal_expansion != "off" and not report_only:
        expansion_input = run_dir / "formal-expansion-input.md"
        expansion_input.write_text(_markdown_with_frontmatter(content_frontmatter, content_body), encoding="utf-8")
        artifacts["formal_expansion_input"] = str(expansion_input)
        statuses["formal_expansion_input"] = {"status": "written"}
        expansion_result = expand_formal_markdown(expansion_input, args.formal_expansion)
        expansion_paths = write_expansion_outputs(expansion_result, run_dir)
        content_body = str(expansion_result["expanded_markdown"])
        artifacts["formal_expansion"] = expansion_paths["expanded"]
        artifacts["formal_expansion_report"] = expansion_paths["json"]
        artifacts["formal_expansion_report_md"] = expansion_paths["markdown"]
        statuses["formal_expansion"] = {"status": "written"}
        expansion_report = expansion_result["report"]
        formal_expansion_meta = {
            "mode": args.formal_expansion,
            "status": expansion_report.get("status", "unknown"),
            "path": expansion_paths["json"],
            "markdown_path": expansion_paths["markdown"],
            "expanded_path": expansion_paths["expanded"],
            "summary": expansion_report.get("summary", ""),
            "next_action": expansion_report.get("next_action", ""),
            "revision_plan": expansion_report.get("revision_plan", []),
        }
    elif args.formal_expansion != "off" and report_only:
        statuses["formal_expansion"] = {"status": "skipped", "reason": "style_correction_report_only"}
    elif args.formal_expansion == "off":
        statuses["formal_expansion"] = {"status": "skipped", "reason": "off"}

    docx_quality_meta = {"mode": args.docx_quality_check, "status": "not_run", "path": ""}
    docx_quality_blocked = False
    quality_report = None
    assisted_quality_meta = {"mode": args.assisted_quality_review, "status": "not_run", "path": ""}
    assisted_quality_blocked = False
    assisted_report = None

    if args.docx_quality_check != "off" and "docx" in plan["requested_outputs"] and not report_only:
        quality_input = run_dir / "docx-quality-input.md"
        quality_input.write_text(_markdown_with_frontmatter(content_frontmatter, content_body), encoding="utf-8")
        artifacts["docx_quality_input"] = str(quality_input)
        statuses["docx_quality_input"] = {"status": "written"}
        quality_report = check_docx_quality(quality_input)
        quality_paths = write_quality_reports(quality_report, run_dir)
        artifacts["docx_quality_report"] = quality_paths["json"]
        artifacts["docx_quality_report_md"] = quality_paths["markdown"]
        statuses["docx_quality_check"] = {"status": "written"}
        docx_quality_meta = {
            "mode": args.docx_quality_check,
            "status": quality_report.get("status", "unknown"),
            "path": quality_paths["json"],
            "markdown_path": quality_paths["markdown"],
            "summary": quality_report.get("summary", ""),
            "next_action": quality_report.get("next_action", ""),
        }
        docx_quality_blocked = args.docx_quality_check == "strict" and quality_report.get("status") == "blocked"
    elif args.docx_quality_check != "off" and "docx" in plan["requested_outputs"] and report_only:
        statuses["docx_quality_check"] = {"status": "skipped", "reason": "style_correction_report_only"}
    elif args.docx_quality_check == "off":
        statuses["docx_quality_check"] = {"status": "skipped", "reason": "off"}

    if args.assisted_quality_review != "off" and "docx" in plan["requested_outputs"] and not report_only:
        assisted_input = run_dir / "assisted-quality-input.md"
        assisted_input.write_text(_markdown_with_frontmatter(content_frontmatter, content_body), encoding="utf-8")
        artifacts["assisted_quality_input"] = str(assisted_input)
        statuses["assisted_quality_input"] = {"status": "written"}
        assisted_report = assist_docx_quality_review(assisted_input)
        assisted_paths = write_assisted_reports(assisted_report, run_dir)
        artifacts["assisted_quality_report"] = assisted_paths["json"]
        artifacts["assisted_quality_report_md"] = assisted_paths["markdown"]
        statuses["assisted_quality_review"] = {"status": "written"}
        assisted_quality_meta = {
            "mode": args.assisted_quality_review,
            "status": assisted_report.get("status", "unknown"),
            "path": assisted_paths["json"],
            "markdown_path": assisted_paths["markdown"],
            "summary": assisted_report.get("summary", ""),
            "next_action": assisted_report.get("next_action", ""),
        }
        assisted_quality_blocked = (
            args.assisted_quality_review == "strict" and assisted_report.get("status") == "needs_revision"
        )
    elif args.assisted_quality_review != "off" and "docx" in plan["requested_outputs"] and report_only:
        statuses["assisted_quality_review"] = {"status": "skipped", "reason": "style_correction_report_only"}
    elif args.assisted_quality_review == "off":
        statuses["assisted_quality_review"] = {"status": "skipped", "reason": "off"}

    formal_revision_meta = {"mode": args.formal_revision, "status": "not_run", "path": ""}
    if args.formal_revision == "auto" and not report_only:
        revision_input = run_dir / "formal-revision-input.md"
        revision_input.write_text(_markdown_with_frontmatter(content_frontmatter, content_body), encoding="utf-8")
        artifacts["formal_revision_input"] = str(revision_input)
        statuses["formal_revision_input"] = {"status": "written"}
        expansion_report_for_revision = None
        if isinstance(formal_expansion_meta.get("path"), str) and formal_expansion_meta.get("path"):
            expansion_report_path = Path(str(formal_expansion_meta["path"]))
            if expansion_report_path.exists():
                expansion_report_for_revision = json.loads(expansion_report_path.read_text(encoding="utf-8"))
        revision_result = revise_formal_markdown(
            revision_input,
            docx_quality_report=quality_report,
            assisted_quality_report=assisted_report,
            formal_expansion_report=expansion_report_for_revision,
        )
        revision_paths = write_revision_outputs(revision_result, run_dir)
        artifacts["formal_revision"] = revision_paths["revised"]
        artifacts["formal_revision_report"] = revision_paths["json"]
        artifacts["formal_revision_report_md"] = revision_paths["markdown"]
        statuses["formal_revision"] = {"status": "written"}
        formal_revision_report = revision_result["report"]
        formal_revision_meta = {
            "mode": args.formal_revision,
            "status": formal_revision_report.get("status", "unknown"),
            "path": revision_paths["json"],
            "markdown_path": revision_paths["markdown"],
            "revised_path": revision_paths["revised"],
            "summary": formal_revision_report.get("summary", ""),
        }
        if formal_revision_report.get("status") == "revised":
            content_body = str(revision_result["revised_markdown"])
            clean_path = None
    elif args.formal_revision == "off":
        statuses["formal_revision"] = {"status": "skipped", "reason": "off"}

    clean_path = None
    if report_only:
        for output_name in ["markdown", "obsidian", "docx", "pdf"]:
            if output_name in plan["requested_outputs"]:
                statuses[output_name] = {"status": "skipped", "reason": "style_correction_report_only"}
    elif "markdown" in plan["requested_outputs"]:
        clean_path = render_clean_markdown(content_body, run_dir, plan["rules"])
        artifacts["markdown"] = str(clean_path)
        statuses["markdown"] = {"status": "written"}

    if not report_only and "obsidian" in plan["requested_outputs"]:
        input_for_obsidian = clean_path or render_clean_markdown(content_body, run_dir, plan["rules"])
        obsidian_path, err = render_obsidian(input_for_obsidian, run_dir, ROOT, plan["obsidian"].get("mode", "obsidian-enhanced"))
        if obsidian_path:
            artifacts["obsidian"] = str(obsidian_path)
            statuses["obsidian"] = {"status": "written"}
        else:
            statuses["obsidian"] = {"status": "failed", "reason": err or "unknown error"}

    if not report_only and "docx" in plan["requested_outputs"] and docx_quality_blocked:
        statuses["docx"] = {"status": "skipped", "reason": "docx_quality_check_blocked"}
    elif not report_only and "docx" in plan["requested_outputs"] and assisted_quality_blocked:
        statuses["docx"] = {"status": "skipped", "reason": "assisted_quality_review_needs_revision"}
    elif not report_only and "docx" in plan["requested_outputs"]:
        input_for_docx = clean_path or render_clean_markdown(content_body, run_dir, plan["rules"])
        reference_doc = None

        # A path: preset template selection
        template_override = args.template.strip()
        if template_override:
            preset_path = Path(__file__).resolve().parents[1] / "templates" / "docx" / f"{template_override}.docx"
            if preset_path.exists():
                reference_doc = run_dir / f"{template_override}-reference.docx"
                shutil.copy2(preset_path, reference_doc)
                docx_reference_meta = {"mode": "preset", "preset": template_override, "path": str(preset_path)}

        # Fallback to profile-based template
        if reference_doc is None:
            reference_name = plan.get("docx", {}).get("reference_doc")
            if reference_name:
                reference_doc = run_dir / reference_name
                template_reference = Path(__file__).resolve().parents[1] / "templates" / "docx" / reference_name
                if template_reference.exists() and not args.rules.strip():
                    shutil.copy2(template_reference, reference_doc)
                    docx_reference_meta = {"mode": "template", "path": str(template_reference)}
                else:
                    build_reference = [
                    "python3",
                    str(Path(__file__).resolve().parents[0] / "build_reference_doc.py"),
                    "--body-font",
                    plan["rules"].get("typography", {}).get("body_font", "宋体"),
                    "--body-size",
                    plan["rules"].get("typography", {}).get("body_size", "小四"),
                    "--title-font",
                    plan["rules"].get("typography", {}).get("title_font", "黑体"),
                    "--title-size",
                    plan["rules"].get("typography", {}).get("title_size", "小二"),
                    "--title-weight",
                    plan["rules"].get("typography", {}).get("title_weight", "bold"),
                    "--title-align",
                    plan["rules"].get("typography", {}).get("title_align", "center"),
                    "--heading-font",
                    plan["rules"].get("typography", {}).get("heading_font", "黑体"),
                    "--heading-weight",
                    plan["rules"].get("typography", {}).get("heading_weight", "bold"),
                    "--heading1-size",
                    str(plan["rules"].get("typography", {}).get("heading1_size", "16")),
                    "--heading2-size",
                    str(plan["rules"].get("typography", {}).get("heading2_size", "14")),
                    "--heading3-size",
                    str(plan["rules"].get("typography", {}).get("heading3_size", "12")),
                    "--line-spacing",
                    str(plan["rules"].get("paragraph", {}).get("line_spacing", "28")),
                    "--first-line-indent",
                    plan["rules"].get("paragraph", {}).get("first_line_indent", "2char"),
                    "--spacing-before",
                    str(plan["rules"].get("paragraph", {}).get("spacing_before", "0")),
                    "--spacing-after",
                    str(plan["rules"].get("paragraph", {}).get("spacing_after", "0")),
                    "--alignment",
                    str(plan["rules"].get("paragraph", {}).get("alignment", "justify")),
                    "--heading1-spacing-before",
                    str(plan["rules"].get("headings", {}).get("heading1_spacing_before", "12")),
                    "--heading1-spacing-after",
                    str(plan["rules"].get("headings", {}).get("heading1_spacing_after", "6")),
                    "--heading2-spacing-before",
                    str(plan["rules"].get("headings", {}).get("heading2_spacing_before", "10")),
                    "--heading2-spacing-after",
                    str(plan["rules"].get("headings", {}).get("heading2_spacing_after", "6")),
                    "--heading3-spacing-before",
                    str(plan["rules"].get("headings", {}).get("heading3_spacing_before", "8")),
                    "--heading3-spacing-after",
                    str(plan["rules"].get("headings", {}).get("heading3_spacing_after", "3")),
                    "--heading-align",
                    str(plan["rules"].get("headings", {}).get("heading_align", "left")),
                    "--margin",
                    plan["rules"].get("page", {}).get("margin", "normal"),
                    "--top-margin",
                    str(plan["rules"].get("page", {}).get("top_margin", "")),
                    "--bottom-margin",
                    str(plan["rules"].get("page", {}).get("bottom_margin", "")),
                    "--left-margin",
                    str(plan["rules"].get("page", {}).get("left_margin", "")),
                    "--right-margin",
                    str(plan["rules"].get("page", {}).get("right_margin", "")),
                    "--page-number",
                    plan["rules"].get("page", {}).get("page_number", "off"),
                    "--page-number-align",
                    plan["rules"].get("page", {}).get("page_number_align", "center"),
                    "--first-page-number",
                    plan["rules"].get("page", {}).get("first_page_number", "off"),
                    "--header-text",
                    plan["rules"].get("page", {}).get("header_text", ""),
                    "--footer-text",
                    plan["rules"].get("page", {}).get("footer_text", ""),
                    "--header-align",
                    plan["rules"].get("page", {}).get("header_align", "center"),
                    "--footer-align",
                    plan["rules"].get("page", {}).get("footer_align", "center"),
                    "--header-font",
                    plan["rules"].get("page", {}).get("header_font", "宋体"),
                    "--header-size",
                    str(plan["rules"].get("page", {}).get("header_size", "小五")),
                    "--footer-font",
                    plan["rules"].get("page", {}).get("footer_font", "宋体"),
                    "--footer-size",
                    str(plan["rules"].get("page", {}).get("footer_size", "小五")),
                    "--page-number-font",
                    plan["rules"].get("page", {}).get("page_number_font", "宋体"),
                    "--page-number-size",
                    str(plan["rules"].get("page", {}).get("page_number_size", "小五")),
                        "--output",
                        str(reference_doc),
                    ]
                    import subprocess
                    subprocess.run(build_reference, check=True, capture_output=True, text=True)
                    docx_reference_meta = {"mode": "generated", "path": str(reference_doc)}
        docx_path, err = render_docx(input_for_docx, run_dir, reference_doc)
        if docx_path:
            if reference_doc and reference_doc.exists():
                artifacts["docx_reference"] = str(reference_doc)
            artifacts["docx"] = str(docx_path)
            statuses["docx"] = {"status": "written"}
        else:
            statuses["docx"] = {"status": "blocked", "reason": err or "unknown error"}

    if not report_only and "pdf" in plan["requested_outputs"]:
        input_for_pdf = clean_path or render_clean_markdown(content_body, run_dir)
        pdf_path, err = render_pdf(input_for_pdf, run_dir)
        if pdf_path:
            artifacts["pdf"] = str(pdf_path)
            statuses["pdf"] = {"status": "written"}
        else:
            statuses["pdf"] = {"status": "blocked", "reason": err or "unknown error"}

    index_path = run_dir / "index.md"
    manifest_path = run_dir / "manifest.json"
    artifacts["index"] = str(index_path)
    artifacts["manifest"] = str(manifest_path)
    delivery_recommendation = _build_delivery_recommendation(
        requested_outputs=plan["requested_outputs"],
        statuses=statuses,
        formal_expansion=formal_expansion_meta,
        docx_quality_check=docx_quality_meta,
        assisted_quality_review=assisted_quality_meta,
        report_only=report_only,
    )

    manifest = {
        "source_path": document["source_path"],
        "profile": plan["profile_name"],
        "requested_outputs": plan["requested_outputs"],
        "artifacts": artifacts,
        "statuses": statuses,
        "rules": plan["rules"],
        "rule_override_notes": rule_notes,
        "style_correction": style_meta,
        "style_correction_report_mode": report_mode or "off",
        "formal_expansion": formal_expansion_meta,
        "docx_quality_check": docx_quality_meta,
        "assisted_quality_review": assisted_quality_meta,
        "formal_revision": formal_revision_meta,
        "delivery_recommendation": delivery_recommendation,
        "docx_reference": docx_reference_meta if "docx" in plan["requested_outputs"] else {"mode": "none", "path": ""},
        "obsidian_mode": plan["obsidian"].get("mode", "obsidian-enhanced"),
        "delivery_note": {
            "formal_artifacts": [key for key in ["docx", "obsidian", "markdown", "pdf"] if key in artifacts],
            "advice": "当前第一版正式主链是 markdown / obsidian / docx；如果某个格式失败，请以 statuses 中的具体 reason 为准。"
        },
    }
    manifest_path = write_manifest(run_dir, manifest)
    index_lines = [
        "# output-layer run index",
        "",
        f"- source: `source.md`",
        f"- style corrected: `output.corrected.md`",
    ]
    if "formal_expansion_input" in artifacts:
        index_lines.append("- formal expansion input: `formal-expansion-input.md`")
    if "markdown" in artifacts:
        index_lines.append("- clean markdown: `output.clean.md`")
    if "formal_expansion" in artifacts:
        index_lines.append("- formal expansion: `output.expanded.md`")
    if "formal_expansion_report" in artifacts:
        index_lines.append("- formal expansion report json: `formal_expansion_report.json`")
        index_lines.append("- formal expansion report markdown: `formal_expansion_report.md`")
    if "docx_quality_input" in artifacts:
        index_lines.append("- docx quality input: `docx-quality-input.md`")
    if "docx_quality_report" in artifacts:
        index_lines.append("- docx quality report json: `docx_quality_report.json`")
        index_lines.append("- docx quality report markdown: `docx_quality_report.md`")
    if "assisted_quality_input" in artifacts:
        index_lines.append("- assisted quality input: `assisted-quality-input.md`")
    if "assisted_quality_report" in artifacts:
        index_lines.append("- assisted quality report json: `assisted_quality_report.json`")
        index_lines.append("- assisted quality report markdown: `assisted_quality_report.md`")
    if "formal_revision_input" in artifacts:
        index_lines.append("- formal revision input: `formal-revision-input.md`")
    if "formal_revision" in artifacts:
        index_lines.append("- formal revision: `output.revised.md`")
    if "formal_revision_report" in artifacts:
        index_lines.append("- formal revision report json: `formal_revision_report.json`")
        index_lines.append("- formal revision report markdown: `formal_revision_report.md`")
    if "obsidian" in artifacts:
        index_lines.append("- obsidian: `output.obsidian.md`")
    if "docx" in artifacts:
        index_lines.append("- docx: `output.docx`")
    if "pdf" in artifacts:
        index_lines.append("- pdf: `output.pdf`")
    index_lines.extend(
        [
            "- style correction report json: `style_correction_report.json`",
            "- style correction report markdown: `style_correction_report.md`",
            "- manifest: `manifest.json`",
            "",
            "## Delivery Recommendation",
            "",
            f"- Status: {delivery_recommendation['status']}",
            f"- Summary: {delivery_recommendation['summary']}",
        ]
    )
    blockers = delivery_recommendation.get("blockers", [])
    if isinstance(blockers, list) and blockers:
        index_lines.extend(["", "### Blockers", ""])
        index_lines.extend(f"- {item}" for item in blockers)
    warnings = delivery_recommendation.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        index_lines.extend(["", "### Warnings", ""])
        index_lines.extend(f"- {item}" for item in warnings)
    priority_actions = delivery_recommendation.get("priority_actions", [])
    if isinstance(priority_actions, list) and priority_actions:
        index_lines.extend(["", "### Priority Actions", ""])
        index_lines.extend(f"- {item}" for item in priority_actions)
    index_lines.extend(
        [
            "",
            "## Statuses",
            "",
        ]
    )
    for name, info in statuses.items():
        reason = f" ({info['reason']})" if info.get("reason") else ""
        index_lines.append(f"- `{name}`: {info['status']}{reason}")
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    artifact_paths = [Path(path) for path in artifacts.values() if isinstance(path, str)]
    enforce_single_version_names(artifact_paths)
    archive_logs = archive_artifact_dirs([run_dir])

    print(f"run_dir={run_dir}")
    print(f"manifest={manifest_path}")
    for name, info in statuses.items():
        reason = f" ({info['reason']})" if info.get("reason") else ""
        print(f"{name}: {info['status']}{reason}")
    for log in archive_logs:
        print(f"archive: {log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
