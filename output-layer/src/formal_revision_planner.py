from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from docx_quality_checker import check_docx_quality
from source_loader import load_markdown


def _make_action(code: str, description: str, evidence: str) -> dict[str, str]:
    return {"code": code, "description": description, "evidence": evidence}


def _has_heading(body: str, heading: str) -> bool:
    return bool(re.search(rf"^#{{1,6}}\s+{re.escape(heading)}\s*$", body, re.MULTILINE))


def _append_missing_section_placeholders(body: str, warnings: list[dict[str, Any]], actions: list[dict[str, str]]) -> str:
    missing = []
    for item in warnings:
        if item.get("code") != "missing_required_section":
            continue
        name = str(item.get("evidence") or "").strip()
        if name and name not in missing:
            missing.append(name)
    if not missing:
        return body

    additions: list[str] = []
    for name in missing:
        heading = f"待补充：{name}"
        if _has_heading(body, heading):
            continue
        additions.extend([f"## {heading}", "", f"待补充：补充“{name}”相关真实信息、依据或边界。", ""])
    if not additions:
        return body

    actions.append(
        _make_action(
            "add_missing_section_placeholders",
            "为缺失的必要章节追加待补充占位。",
            "、".join(missing),
        )
    )
    return body.rstrip() + "\n\n" + "\n".join(additions).rstrip() + "\n"


def _append_reference_placeholder(body: str, warnings: list[dict[str, Any]], actions: list[dict[str, str]]) -> str:
    if not any(item.get("code") == "missing_reference_section" for item in warnings):
        return body
    if re.search(r"^#{1,6}\s*(?:参考资料|参考文献|资料来源|来源|References)\s*$", body, re.MULTILINE | re.IGNORECASE):
        return body
    actions.append(
        _make_action(
            "add_reference_placeholder",
            "追加参考资料占位，不编造具体来源。",
            "质量门提示存在多个外部来源线索但缺少集中资料区。",
        )
    )
    return (
        body.rstrip()
        + "\n\n## 参考资料\n\n"
        + "待补充：集中列出标准、链接或文献线索。\n"
    )


def _append_assisted_missing_element_placeholders(
    body: str,
    assisted_report: dict[str, Any] | None,
    actions: list[dict[str, str]],
) -> str:
    if not assisted_report:
        return body
    missing: list[str] = []
    for finding in assisted_report.get("findings", []):
        if not isinstance(finding, dict):
            continue
        evidence = finding.get("evidence", {})
        if not isinstance(evidence, dict):
            continue
        for item in evidence.get("missing_elements", []):
            name = str(item).strip()
            if name and name not in missing:
                missing.append(name)
    if not missing:
        return body

    additions: list[str] = []
    for name in missing:
        heading = f"待补充：{name}"
        if _has_heading(body, heading):
            continue
        additions.extend([f"## {heading}", "", f"待补充：补充“{name}”对应的真实内容、依据或边界。", ""])
    if not additions:
        return body

    actions.append(
        _make_action(
            "add_assisted_missing_element_placeholders",
            "根据辅助审查报告追加缺失要素占位。",
            "、".join(missing),
        )
    )
    return body.rstrip() + "\n\n" + "\n".join(additions).rstrip() + "\n"


def _append_revision_plan_checklist(
    body: str,
    formal_expansion_report: dict[str, Any] | None,
    actions: list[dict[str, str]],
) -> str:
    if not formal_expansion_report:
        return body
    revision_plan = formal_expansion_report.get("revision_plan", [])
    if not isinstance(revision_plan, list) or not revision_plan:
        return body

    lines: list[str] = []
    seen: set[str] = set()
    for item in revision_plan:
        if not isinstance(item, dict):
            continue
        action = str(item.get("action", "")).strip()
        instruction = str(item.get("instruction", "")).strip()
        target = str(item.get("target", "")).strip()
        if not action:
            continue
        text = f"{action}：{instruction or target}".strip()
        if text.endswith("："):
            text = text[:-1]
        if text and text not in seen:
            lines.append(f"- {text}")
            seen.add(text)
    if not lines:
        return body

    heading = "人工修订清单"
    if _has_heading(body, heading):
        return body
    actions.append(
        _make_action(
            "add_revision_plan_checklist",
            "将正式扩写报告中的修订计划追加为人工修订清单。",
            f"{len(lines)} item(s)",
        )
    )
    return body.rstrip() + "\n\n## 人工修订清单\n\n" + "\n".join(lines) + "\n"


def revise_formal_markdown(
    source_path: str | Path,
    *,
    docx_quality_report: dict[str, Any] | None = None,
    assisted_quality_report: dict[str, Any] | None = None,
    formal_expansion_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    document = load_markdown(str(source_path))
    body = str(document["body"])
    quality_report = docx_quality_report or check_docx_quality(source_path)
    actions: list[dict[str, str]] = []

    blockers = list(quality_report.get("blockers", []))
    if blockers:
        report = {
            "status": "blocked",
            "summary": "存在阻断项，修订器不自动改写正文。",
            "actions": [],
            "blocked_reasons": [str(item.get("code", "unknown")) for item in blockers if isinstance(item, dict)],
            "source_path": str(Path(source_path).expanduser().resolve()),
        }
        return {"revised_markdown": body, "report": report}

    warnings = [item for item in quality_report.get("warnings", []) if isinstance(item, dict)]
    revised = body
    revised = _append_missing_section_placeholders(revised, warnings, actions)
    revised = _append_reference_placeholder(revised, warnings, actions)
    revised = _append_assisted_missing_element_placeholders(revised, assisted_quality_report, actions)
    revised = _append_revision_plan_checklist(revised, formal_expansion_report, actions)

    report = {
        "status": "revised" if actions else "unchanged",
        "summary": "已根据质量报告生成确定性修订稿。" if actions else "没有可自动处理的修订项。",
        "actions": actions,
        "blocked_reasons": [],
        "source_path": str(Path(source_path).expanduser().resolve()),
    }
    return {"revised_markdown": revised, "report": report}


def render_revision_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Formal Revision Report",
        "",
        f"- Status: {report.get('status', '')}",
        f"- Summary: {report.get('summary', '')}",
        f"- Source: {report.get('source_path', '')}",
        "",
        "## Actions",
        "",
    ]
    actions = report.get("actions", [])
    if not actions:
        lines.append("- None")
    else:
        for index, item in enumerate(actions, start=1):
            lines.append(f"### {index}. {item.get('code', 'unknown')}")
            lines.append("")
            lines.append(f"- Description: {item.get('description', '')}")
            lines.append(f"- Evidence: {item.get('evidence', '')}")
            lines.append("")
    blocked = report.get("blocked_reasons", [])
    if blocked:
        lines.extend(["", "## Blocked Reasons", ""])
        lines.extend(f"- {item}" for item in blocked)
    return "\n".join(lines).rstrip() + "\n"


def write_revision_outputs(result: dict[str, Any], outdir: str | Path) -> dict[str, str]:
    output_dir = Path(outdir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    revised_path = output_dir / "output.revised.md"
    json_path = output_dir / "formal_revision_report.json"
    md_path = output_dir / "formal_revision_report.md"
    revised_path.write_text(str(result["revised_markdown"]), encoding="utf-8")
    json_path.write_text(json.dumps(result["report"], ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_revision_report_markdown(result["report"]), encoding="utf-8")
    return {"revised": str(revised_path), "json": str(json_path), "markdown": str(md_path)}
