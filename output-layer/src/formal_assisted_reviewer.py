from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from document_classifier import infer_document_type
from source_loader import load_markdown


DOC_TYPE_ALIASES = {
    "technical_disclosure": "technical",
    "patent_like": "technical",
    "project_report": "proposal",
    "paper_like": "abstract",
}

ELEMENT_GROUPS: dict[str, dict[str, tuple[str, ...]]] = {
    "proposal": {
        "为什么做": ("立项依据", "研究背景", "问题", "价值", "意义"),
        "做什么": ("研究内容", "研究目标", "任务", "技术路线", "指标"),
        "研究基础/可行性": ("研究基础", "可行性", "条件", "团队", "数据基础", "前期工作"),
    },
    "technical": {
        "技术问题": ("技术问题", "现有问题", "痛点", "不足"),
        "技术方案": ("技术方案", "方案", "组成", "步骤", "机制", "实施方式"),
        "技术效果": ("技术效果", "效果", "收益", "对比", "指标"),
        "边界条件": ("边界", "适用条件", "限制", "未验证", "风险", "前提"),
    },
    "abstract": {
        "对象/问题": ("对象", "问题", "面向", "针对", "研究"),
        "方法/材料": ("方法", "采用", "基于", "数据", "材料", "样本", "构建"),
        "结果/发现": ("结果", "发现", "显示", "表明", "形成", "得到", "识别"),
        "意义/边界": ("意义", "适用", "边界", "局限", "不替代", "用于"),
    },
    "manual": {
        "适用对象": ("适用", "对象", "用户", "范围"),
        "前置条件": ("前置", "准备事项", "条件", "依赖", "权限", "材料"),
        "操作步骤": ("步骤", "操作", "执行", "打开", "输入", "查看"),
        "注意事项": ("注意", "警告", "提示", "限制"),
        "异常处理": ("异常", "失败", "错误", "回退", "处理", "求助"),
    },
}

METHOD_META: dict[str, dict[str, Any]] = {
    "proposal": {
        "code": "proposal_three_questions_incomplete",
        "lesson_id": "FWM-001",
        "lesson_name": "申请类三问结构",
        "dimension": "completeness",
        "source_ids": ["CN-SRC-004", "CN-SRC-006"],
        "review_question": "申请类材料是否说明为什么做、做什么、凭什么能做。",
        "fix": "删除套路化铺垫，把研究对象、路径和基础前移；补齐立项依据、研究内容、研究基础/可行性。",
    },
    "technical": {
        "code": "technical_chain_incomplete",
        "lesson_id": "FWM-002",
        "lesson_name": "技术说明的问题-方案-效果链",
        "dimension": "logic",
        "source_ids": ["CN-SRC-007", "CN-SRC-009"],
        "review_question": "技术说明是否形成技术问题、技术方案、技术效果和边界条件链条。",
        "fix": "把宣传性优势改成问题-方案-效果链，并补充适用条件、限制或未验证内容。",
    },
    "abstract": {
        "code": "abstract_four_elements_incomplete",
        "lesson_id": "FWM-003",
        "lesson_name": "摘要四要素",
        "dimension": "completeness",
        "source_ids": ["CN-SRC-010", "CN-SRC-012", "CN-SRC-013", "CN-SRC-014", "CN-SRC-015"],
        "review_question": "摘要是否交代对象/问题、方法/材料、结果/发现、意义/边界。",
        "fix": "按对象/问题、方法/材料、结果/发现、意义/边界重排摘要；不得新增未提供的事实。",
    },
    "manual": {
        "code": "manual_task_chain_incomplete",
        "lesson_id": "FWM-005",
        "lesson_name": "说明书任务链",
        "dimension": "completeness",
        "source_ids": ["CN-SRC-008", "CN-SRC-011"],
        "review_question": "说明书是否包含适用对象、前置条件、操作步骤、注意事项和异常处理。",
        "fix": "在步骤前补适用对象和前置条件，把注意事项和异常处理单列。",
    },
}

WEAK_ACTION_VERBS = ("加强", "推动", "完善", "提升", "促进")
ACTION_REQUIRED_HINTS = ("面向", "由", "对", "在", "通过", "达到", "输出", "提交", "归档", "完成")
PROPOSAL_GATE_TERMS = ("预算", "附件", "签章", "合作单位", "伦理", "申报", "指南", "提交")
GENERIC_HUMAN_GATE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("政策依据", r"(?:政策|规定|办法|通知|意见|指南)"),
    ("标准编号", r"(?:GB/T|GB|ISO|IEC|IEEE|RFC)\s*[-A-Z0-9./]*\d"),
    ("版本号", r"(?:版本|Version|v)\s*[:：为]?\s*\d+(?:\.\d+){1,3}"),
    ("端口/IP", r"(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?|端口\s*[:：为]?\s*\d{2,5}"),
    ("进程/PID", r"(?:PID|进程)\s*[:：为]?\s*\d+"),
    ("运行数据", r"(?:运行时间|占用|内存|磁盘|成本|预算|附件|签章|合作单位|伦理|申报)"),
)


def _doc_type(frontmatter: dict[str, Any]) -> str:
    raw = str(frontmatter.get("doc_type") or frontmatter.get("type") or "formal_report").strip()
    return DOC_TYPE_ALIASES.get(raw, raw)


def _classify_doc_type(frontmatter: dict[str, Any], body: str) -> str:
    return str(infer_document_type(frontmatter, body)["doc_type"])


def _strip_markdown(body: str) -> str:
    text = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    return text


def _has_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


PLACEHOLDER_SIGNAL_RE = re.compile(r"(?:待补充|None|暂无|缺失|未提供|需补充)")


def _section_blocks(markdown: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []
    for line in markdown.splitlines():
        match = re.match(r"^#{1,6}\s+(.*\S)\s*$", line.strip())
        if match:
            if current_heading:
                blocks.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
            current_heading = match.group(1).strip()
            current_lines = []
        elif current_heading:
            current_lines.append(line)
    if current_heading:
        blocks.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
    return blocks


def _meaningful_section_text(body: str) -> str:
    lines: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^(?:[-*+]|\d+[.)、])\s+", "", line).strip()
        if not line:
            continue
        if PLACEHOLDER_SIGNAL_RE.search(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def _present_missing_from_markdown(markdown: str, groups: dict[str, tuple[str, ...]]) -> tuple[list[str], list[str]]:
    present: list[str] = []
    missing: list[str] = []
    blocks = _section_blocks(markdown)
    for label, keywords in groups.items():
        matched = False
        for block in blocks:
            block_text = f"{block['heading']}\n{block['body']}"
            if not _has_any(block_text, keywords):
                continue
            meaningful_body = _meaningful_section_text(block["body"])
            if meaningful_body:
                matched = True
                break
        if matched:
            present.append(label)
        else:
            missing.append(label)
    return present, missing


def _present_missing(text: str, groups: dict[str, tuple[str, ...]]) -> tuple[list[str], list[str]]:
    present: list[str] = []
    missing: list[str] = []
    for label, keywords in groups.items():
        if _has_any(text, keywords):
            present.append(label)
        else:
            missing.append(label)
    return present, missing


def _finding(
    *,
    meta: dict[str, Any],
    severity: str,
    present: list[str],
    missing: list[str],
    examples: list[str] | None = None,
) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "present_elements": present,
        "missing_elements": missing,
    }
    if examples:
        evidence["examples"] = examples[:5]
    return {
        "rule_type": "assisted",
        "code": str(meta["code"]),
        "severity": severity,
        "dimension": str(meta["dimension"]),
        "lesson_id": str(meta["lesson_id"]),
        "lesson_name": str(meta["lesson_name"]),
        "source_ids": list(meta["source_ids"]),
        "review_question": str(meta["review_question"]),
        "evidence": evidence,
        "fix": str(meta["fix"]),
    }


def _review_element_chain(doc_type: str, text: str) -> dict[str, Any] | None:
    groups = ELEMENT_GROUPS.get(doc_type)
    meta = METHOD_META.get(doc_type)
    if not groups or not meta:
        return None
    present, missing = _present_missing(text, groups)
    if not missing:
        return None
    severity = "warning"
    if doc_type == "abstract" and len(missing) <= 1:
        severity = "suggestion"
    return _finding(meta=meta, severity=severity, present=present, missing=missing)


def _review_element_chain_markdown(doc_type: str, body: str) -> dict[str, Any] | None:
    groups = ELEMENT_GROUPS.get(doc_type)
    meta = METHOD_META.get(doc_type)
    if not groups or not meta:
        return None
    present, missing = _present_missing_from_markdown(body, groups)
    if not missing:
        return None
    severity = "warning"
    if doc_type == "abstract" and len(missing) <= 1:
        severity = "suggestion"
    return _finding(meta=meta, severity=severity, present=present, missing=missing)


def _list_items(body: str) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if re.match(r"^(?:[-*+]|\d+[.)、])\s+", stripped):
            items.append(re.sub(r"^(?:[-*+]|\d+[.)、])\s+", "", stripped).strip())
    return items


def _review_action_items(body: str) -> dict[str, Any] | None:
    weak_examples: list[str] = []
    for item in _list_items(body):
        if item.startswith(WEAK_ACTION_VERBS) and not _has_any(item, ACTION_REQUIRED_HINTS):
            weak_examples.append(item)
    if not weak_examples:
        return None
    return {
        "rule_type": "assisted",
        "code": "action_item_incomplete",
        "severity": "warning",
        "dimension": "logic",
        "lesson_id": "FWM-004",
        "lesson_name": "行动项四件套",
        "source_ids": ["CN-SRC-002", "CN-SRC-003", "CN-SRC-006"],
        "review_question": "建议、措施或任务是否包含对象、动作、条件和结果。",
        "evidence": {
            "examples": weak_examples[:5],
            "missing_elements": ["对象", "条件/范围", "结果/完成标准"],
        },
        "fix": "给每条行动项补齐对象、动作、条件和结果；避免只写“加强、推动、完善、提升”。",
    }


def _human_gates(doc_type: str, text: str) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    proposal_hits = [term for term in PROPOSAL_GATE_TERMS if term in text]
    if doc_type == "proposal" and proposal_hits:
        gates.append(
            {
                "rule_type": "human_gate",
                "code": "proposal_compliance_gate",
                "dimension": "completeness",
                "source_ids": ["CN-SRC-005", "CN-SRC-006", "CN-SRC-010", "CN-SRC-011"],
                "trigger": "、".join(proposal_hits),
                "question": "是否符合当年指南、项目类型、附件、预算、伦理和提交系统要求。",
                "automation_boundary": "只能提示人工确认，不能给出合规结论。",
            }
        )
    generic_hits = [label for label, pattern in GENERIC_HUMAN_GATE_PATTERNS if re.search(pattern, text, re.IGNORECASE)]
    if generic_hits:
        gates.append(
            {
                "rule_type": "human_gate",
                "code": "fact_and_institution_gate",
                "dimension": "logic",
                "source_ids": ["CN-SRC-001", "CN-SRC-009", "CN-SRC-010"],
                "trigger": "、".join(generic_hits[:8]),
                "question": "涉及事实、数据、政策、标准或机构口径的内容是否已有真实来源和负责人确认。",
                "automation_boundary": "辅助审阅只检查文内线索，不能判断事实真伪或机构口径。",
            }
        )
    return gates


def assist_docx_quality_review(source_path: str | Path) -> dict[str, Any]:
    document = load_markdown(str(source_path))
    body = str(document["body"])
    doc_type = _classify_doc_type(document.get("frontmatter", {}), body)
    text = _strip_markdown(body)

    findings: list[dict[str, Any]] = []
    chain_finding = _review_element_chain_markdown(doc_type, body)
    if chain_finding is None:
        chain_finding = _review_element_chain(doc_type, text)
    if chain_finding:
        findings.append(chain_finding)
    action_finding = _review_action_items(body)
    if action_finding:
        findings.append(action_finding)

    human_gates = _human_gates(doc_type, text)
    if findings:
        status = "needs_revision"
        summary = "辅助审阅发现结构、逻辑或内容完整性问题，建议先修正文稿。"
        next_action = "revise_text"
    elif human_gates:
        status = "needs_human_review"
        summary = "未发现方法论缺项，但存在需要人工确认的事实、合规或机构口径事项。"
        next_action = "human_review"
    else:
        status = "pass"
        summary = "未发现当前方法论覆盖的结构、逻辑或内容完整性问题。"
        next_action = "render_or_deterministic_check"

    return {
        "status": status,
        "doc_type": doc_type,
        "summary": summary,
        "methodology_version": "formal-writing-methodology-v1",
        "findings": findings,
        "human_gates": human_gates,
        "next_action": next_action,
        "source_path": str(Path(source_path).expanduser().resolve()),
    }


def render_assisted_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Assisted Docx Quality Report",
        "",
        f"- Status: {report.get('status', '')}",
        f"- Doc type: {report.get('doc_type', '')}",
        f"- Methodology: {report.get('methodology_version', '')}",
        f"- Summary: {report.get('summary', '')}",
        f"- Next action: {report.get('next_action', '')}",
        "",
        "## Assisted Findings",
        "",
    ]
    findings = report.get("findings", [])
    if not findings:
        lines.extend(["- None", ""])
    for index, item in enumerate(findings, start=1):
        evidence = item.get("evidence", {})
        lines.append(f"### {index}. {item.get('code', 'unknown')}")
        lines.append("")
        lines.append(f"- Lesson: {item.get('lesson_id', '')} {item.get('lesson_name', '')}")
        lines.append(f"- Source ids: {', '.join(item.get('source_ids', []))}")
        lines.append(f"- Severity: {item.get('severity', '')}")
        lines.append(f"- Question: {item.get('review_question', '')}")
        lines.append(f"- Present: {', '.join(evidence.get('present_elements', []))}")
        lines.append(f"- Missing: {', '.join(evidence.get('missing_elements', []))}")
        if evidence.get("examples"):
            lines.append(f"- Examples: {'; '.join(evidence.get('examples', []))}")
        lines.append(f"- Fix: {item.get('fix', '')}")
        lines.append("")

    lines.extend(["## Human Gates", ""])
    gates = report.get("human_gates", [])
    if not gates:
        lines.extend(["- None", ""])
    for index, item in enumerate(gates, start=1):
        lines.append(f"### {index}. {item.get('code', 'unknown')}")
        lines.append("")
        lines.append(f"- Source ids: {', '.join(item.get('source_ids', []))}")
        lines.append(f"- Trigger: {item.get('trigger', '')}")
        lines.append(f"- Question: {item.get('question', '')}")
        lines.append(f"- Boundary: {item.get('automation_boundary', '')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_assisted_reports(report: dict[str, Any], outdir: str | Path) -> dict[str, str]:
    output_dir = Path(outdir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "assisted_quality_report.json"
    md_path = output_dir / "assisted_quality_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_assisted_report_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}
