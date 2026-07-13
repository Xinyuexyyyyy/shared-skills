from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from document_classifier import infer_document_type
from source_loader import load_markdown


REQUIRED_SECTIONS: dict[str, tuple[str, ...]] = {
    "formal_report": ("背景", "目的", "方案", "依据", "结论"),
    "proposal": ("立项依据", "研究目标", "研究内容", "创新", "可行", "研究基础", "预期成果"),
    "manual": ("适用", "前置", "步骤", "注意", "异常"),
    "abstract": ("对象", "方法", "结果", "意义"),
    "paper_like": ("问题", "背景", "方法", "结果", "讨论"),
    "policy": ("适用范围", "定义", "职责", "流程", "例外", "执行"),
    "runtime_record": ("概况", "依据", "结论"),
    "meeting_note": ("讨论", "后续"),
    "content_article": (),
}

REQUIRED_SECTION_GROUPS: dict[str, dict[str, tuple[str, ...]]] = {
    "formal_report": {
        "背景": ("背景", "问题", "现有问题", "原始内容", "现状", "概况", "系统概况", "运行记录"),
        "目的": ("目的", "目标", "文档目的", "建设目的"),
        "方案": ("方案", "处理方案", "核心内容", "处理原则", "后续动作", "措施"),
        "依据": ("依据", "边界", "依据与边界", "资料来源", "说明"),
        "结论": ("结论", "下一步", "结论与下一步", "建议"),
    }
}

WEAK_OPENERS = (
    "随着社会的不断发展",
    "在当今快速发展的时代",
    "需要注意的是",
    "值得注意的是",
    "某种程度上",
    "从某种意义上说",
)

TEMPLATE_PHRASES = (
    "需要注意的是",
    "值得注意的是",
    "综上所述",
    "总而言之",
    "不可否认的是",
)

EMOJI_RE = re.compile(
    "[\U0001f300-\U0001f5ff\U0001f600-\U0001f64f\U0001f680-\U0001f6ff\U0001f900-\U0001f9ff]"
)
RAW_HTML_RE = re.compile(r"</?(?:div|span|p|section|article|br|table|tr|td|th)\b[^>]*>", re.IGNORECASE)
BARE_URL_RE = re.compile(r"(?<!\]\()https?://\S+")
STANDARD_REF_RE = re.compile(r"\b(?:GB/T|GB|ISO|IEC|IEEE|RFC|NSF|NSFC)\s*[-A-Z0-9./]*\d", re.IGNORECASE)
SUBJECT_TERMS = ("我", "我们", "本人", "本项目", "该项目", "本报告", "本文", "申请人")
CAPTION_RE = re.compile(r"^\s*(?:图|表)\s*\d*[\-：:、.]?\s*\S+")
REFERENCE_SECTION_RE = re.compile(r"^#{1,6}\s*(?:参考资料|参考文献|资料来源|来源|References)\s*$", re.MULTILINE | re.IGNORECASE)
NUMBERED_H1_SECTION_RE = re.compile(r"^(?:[一二三四五六七八九十]+、|\d+[.、])\S+")
REVISION_REQUIRED_WARNING_CODES = {
    "empty_section_after_heading",
    "mixed_subject_terms",
    "weak_opener",
    "repeated_template_phrase",
    "missing_required_section",
    "missing_reference_section",
    "runtime_record_missing_verification",
}

DOC_TYPE_QUALITY_CONFIG: dict[str, dict[str, bool]] = {
    "content_article": {
        "check_references": False,
        "check_mixed_subject": False,
        "check_figure_captions": False,
    },
    "meeting_note": {
        "check_references": False,
        "check_mixed_subject": False,
        "check_figure_captions": False,
    },
    "runtime_record": {
        "check_references": False,
        "check_mixed_subject": False,
        "check_figure_captions": True,
    },
}


def _make_finding(
    dimension: str,
    severity: str,
    code: str,
    location: str,
    issue: str,
    evidence: str,
    fix: str,
) -> dict[str, str]:
    return {
        "dimension": dimension,
        "severity": severity,
        "code": code,
        "location": location,
        "issue": issue,
        "evidence": evidence[:120],
        "fix": fix,
    }


def _headings(body: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    in_code = False
    for line_no, line in enumerate(body.splitlines(), start=1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        match = re.match(r"^(#{1,6})\s+(.*\S)\s*$", line)
        if match:
            items.append({"level": len(match.group(1)), "text": match.group(2).strip(), "line": line_no})
    return items


def _first_plain_paragraph(body: str) -> str:
    in_code = False
    buffer: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not stripped:
            if buffer:
                break
            continue
        if stripped.startswith(("#", "-", "*", ">", "|")):
            if buffer:
                break
            continue
        buffer.append(stripped)
    return "".join(buffer)


def _infer_doc_type(frontmatter: dict[str, Any]) -> str:
    raw = str(frontmatter.get("doc_type") or frontmatter.get("type") or "formal_report").strip()
    return raw or "formal_report"


def _classify_doc_type(frontmatter: dict[str, Any], body: str) -> str:
    return str(infer_document_type(frontmatter, body)["doc_type"])


def _section_text(headings: list[dict[str, Any]]) -> str:
    return "\n".join(str(item["text"]) for item in headings)


def _missing_required_sections(doc_type: str, section_names: str, body: str) -> list[str]:
    groups = REQUIRED_SECTION_GROUPS.get(doc_type)
    if groups:
        missing: list[str] = []
        haystack = f"{section_names}\n{body}"
        for canonical, aliases in groups.items():
            if not any(alias in haystack for alias in aliases):
                missing.append(canonical)
        return missing
    required = REQUIRED_SECTIONS.get(doc_type, REQUIRED_SECTIONS["formal_report"])
    return [name for name in required if name not in section_names and name not in body]


def _sentence_candidates(body: str) -> list[str]:
    text = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        if stripped.startswith(("#", ">", "|", "-", "*")):
            cleaned_lines.append("")
            continue
        if re.match(r"^\d+[.)、]\s+", stripped):
            cleaned_lines.append("")
            continue
        cleaned_lines.append(stripped)
    text = "\n".join(cleaned_lines)
    parts = re.split(r"[。！？!?]\s*", text)
    return [part.strip() for part in parts if part.strip()]


def _has_single_document_title(h1s: list[dict[str, Any]]) -> bool:
    if len(h1s) <= 1:
        return len(h1s) == 1
    first_title = str(h1s[0]["text"]).strip()
    section_titles = [str(item["text"]).strip() for item in h1s[1:]]
    return bool(first_title) and all(NUMBERED_H1_SECTION_RE.match(title) for title in section_titles)


def _nonempty_noncomment_lines(body: str) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    in_code = False
    for line_no, raw in enumerate(body.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped:
            continue
        lines.append({"line": line_no, "text": stripped})
    return lines


def _detect_empty_sections(body: str) -> list[dict[str, str]]:
    lines = _nonempty_noncomment_lines(body)
    findings: list[dict[str, str]] = []
    for index, item in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.*\S)\s*$", str(item["text"]))
        if not match:
            continue
        current_level = len(match.group(1))
        title = match.group(2).strip()
        if index + 1 >= len(lines):
            continue
        next_item = lines[index + 1]
        next_match = re.match(r"^(#{1,6})\s+(.*\S)\s*$", str(next_item["text"]))
        if next_match and len(next_match.group(1)) <= current_level:
            findings.append(
                _make_finding(
                    "structure",
                    "warning",
                    "empty_section_after_heading",
                    f"line {item['line']}",
                    "标题后没有正文，直接进入同级或更高级标题。",
                    title,
                    "补充该章节说明，或删除空章节。",
                )
            )
    return findings


def _detect_mixed_subject_terms(body: str) -> dict[str, str] | None:
    text = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    found: list[str] = []
    for term in SUBJECT_TERMS:
        if term == "我":
            if re.search(r"(?<!自)我(?!们)", text):
                found.append(term)
        elif term in text:
            found.append(term)
    if len(found) < 2:
        return None
    return _make_finding(
        "formality",
        "warning",
        "mixed_subject_terms",
        "document",
        "同一文档混用多个主体称谓，容易造成责任边界不清。",
        "、".join(found),
        "按文档类型统一为“本报告 / 本项目 / 本文 / 申请人”等一种主体称谓。",
    )


def _has_caption_near(lines: list[str], index: int) -> bool:
    for nearby in (index - 2, index - 1, index + 1, index + 2):
        if 0 <= nearby < len(lines) and CAPTION_RE.match(lines[nearby].strip()):
            return True
    return False


def _detect_missing_figure_or_table_captions(body: str) -> list[dict[str, str]]:
    raw_lines = body.splitlines()
    findings: list[dict[str, str]] = []
    reported_table = False
    for index, line in enumerate(raw_lines):
        stripped = line.strip()
        if re.match(r"^!\[[^\]]*\]\([^)]+\)", stripped) and not _has_caption_near(raw_lines, index):
            findings.append(
                _make_finding(
                    "docx_readiness",
                    "warning",
                    "figure_or_table_missing_caption",
                    f"line {index + 1}",
                    "图片缺少相邻图题或说明，docx 中脱离上下文后难以审阅。",
                    stripped,
                    "在图片前后补“图 x ...”或用途说明。",
                )
            )
        if not reported_table and stripped.startswith("|") and index + 1 < len(raw_lines):
            next_line = raw_lines[index + 1].strip()
            if next_line.startswith("|") and re.search(r"\|\s*:?-{3,}:?\s*(?:\||$)", next_line):
                if not _has_caption_near(raw_lines, index):
                    findings.append(
                        _make_finding(
                            "docx_readiness",
                            "warning",
                            "figure_or_table_missing_caption",
                            f"line {index + 1}",
                            "表格缺少相邻表题或说明，docx 中脱离上下文后难以审阅。",
                            stripped,
                            "在表格前后补“表 x ...”或用途说明。",
                        )
                    )
                reported_table = True
    return findings


def _detect_missing_reference_section(body: str) -> dict[str, str] | None:
    external_source_count = len(BARE_URL_RE.findall(body)) + len(STANDARD_REF_RE.findall(body))
    if external_source_count < 2 or REFERENCE_SECTION_RE.search(body):
        return None
    return _make_finding(
        "completeness",
        "warning",
        "missing_reference_section",
        "document",
        "正文包含多个外部来源线索，但缺少参考资料或来源章节。",
        f"external_source_count={external_source_count}",
        "增加“参考资料”或“资料来源”章节，集中列出标准、链接或文献线索。",
    )


def _doc_type_config(doc_type: str) -> dict[str, bool]:
    defaults = {
        "check_references": True,
        "check_mixed_subject": True,
        "check_figure_captions": True,
    }
    return {**defaults, **DOC_TYPE_QUALITY_CONFIG.get(doc_type, {})}


def _detect_runtime_record_missing_verification(body: str) -> dict[str, str] | None:
    has_verification = any(token in body for token in ("验证", "复核", "测试", "状态", "结果", "输出", "已确认"))
    has_followup = any(token in body for token in ("下一步", "后续", "处理", "修复", "归档", "保留"))
    if has_verification and has_followup:
        return None
    missing = []
    if not has_verification:
        missing.append("验证结果")
    if not has_followup:
        missing.append("后续处理")
    return _make_finding(
        "completeness",
        "warning",
        "runtime_record_missing_verification",
        "document",
        "运行记录需要说明验证结果和后续处理，否则无法判断运行事实是否已闭环。",
        "、".join(missing),
        "补充验证结果、复核状态、后续处理或归档说明。",
    )


def check_docx_quality(source_path: str | Path) -> dict[str, Any]:
    document = load_markdown(str(source_path))
    body = str(document["body"])
    frontmatter = document.get("frontmatter", {})
    doc_type = _classify_doc_type(frontmatter, body)
    doc_config = _doc_type_config(doc_type)
    headings = _headings(body)
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    suggestions: list[dict[str, str]] = []

    h1s = [item for item in headings if item["level"] == 1]
    if not _has_single_document_title(h1s):
        blockers.append(
            _make_finding(
                "structure",
                "blocker",
                "multiple_h1" if len(h1s) > 1 else "missing_h1",
                "document",
                "正式 docx 输出需要且只需要一个总标题。",
                f"h1_count={len(h1s)}",
                "保留一个总标题，其余总标题下调为二级标题或合并。",
            )
        )

    previous_level = 0
    for item in headings:
        level = int(item["level"])
        if previous_level and level > previous_level + 1:
            blockers.append(
                _make_finding(
                    "structure",
                    "blocker",
                    "heading_level_jump",
                    f"line {item['line']}",
                    "标题层级跳跃，docx 渲染后结构不稳定。",
                    str(item["text"]),
                    "补齐中间层级，或把该标题调整到相邻层级。",
                )
            )
        previous_level = level

    warnings.extend(_detect_empty_sections(body))

    if body.count("```") % 2 == 1:
        blockers.append(
            _make_finding(
                "docx_readiness",
                "blocker",
                "unclosed_code_fence",
                "document",
                "存在未闭合代码块，docx 渲染会吞掉后续正文样式。",
                "``` count is odd",
                "闭合代码块，或删除误输入的代码围栏。",
            )
        )

    html_match = RAW_HTML_RE.search(body)
    if html_match:
        blockers.append(
            _make_finding(
                "docx_readiness",
                "blocker",
                "raw_html",
                "document",
                "正文存在裸 HTML 标签，可能进入 docx 正文。",
                html_match.group(0),
                "改为 Markdown 结构，或确认渲染器支持后再保留。",
            )
        )

    emoji_match = EMOJI_RE.search(body)
    if emoji_match:
        warnings.append(
            _make_finding(
                "formality",
                "warning",
                "emoji",
                "document",
                "正式 docx 不建议使用 emoji 或装饰符。",
                emoji_match.group(0),
                "删除 emoji，改为正式文字说明。",
            )
        )

    url_match = BARE_URL_RE.search(body)
    if url_match:
        warnings.append(
            _make_finding(
                "docx_readiness",
                "warning",
                "bare_url",
                "document",
                "裸 URL 直接进入正文会降低正式文档可读性。",
                url_match.group(0),
                "改为带说明文字的链接，或移入参考资料列表。",
            )
        )

    first_plain = _first_plain_paragraph(body)
    if first_plain and any(first_plain.startswith(prefix) for prefix in WEAK_OPENERS):
        warnings.append(
            _make_finding(
                "formality",
                "warning",
                "weak_opener",
                "first paragraph",
                "开头使用低信息套话，正式文档应更早交代对象、目的或结论。",
                first_plain,
                "删除套话，把文档目的、对象或核心判断前移。",
            )
        )

    repeated = [phrase for phrase in TEMPLATE_PHRASES if body.count(phrase) >= 2]
    if repeated:
        warnings.append(
            _make_finding(
                "formality",
                "warning",
                "repeated_template_phrase",
                "document",
                "模板化表达重复出现，削弱正式感。",
                ", ".join(repeated),
                "保留承担结构功能的连接句，删除重复套话。",
            )
        )

    mixed_subject = _detect_mixed_subject_terms(body)
    if mixed_subject and doc_config["check_mixed_subject"]:
        warnings.append(mixed_subject)

    if doc_config["check_figure_captions"]:
        warnings.extend(_detect_missing_figure_or_table_captions(body))

    if doc_config["check_references"]:
        missing_references = _detect_missing_reference_section(body)
        if missing_references:
            warnings.append(missing_references)

    if doc_type == "runtime_record":
        runtime_verification = _detect_runtime_record_missing_verification(body)
        if runtime_verification:
            warnings.append(runtime_verification)

    section_names = _section_text(headings)
    missing = _missing_required_sections(doc_type, section_names, body)
    for name in missing:
        warnings.append(
            _make_finding(
                "completeness",
                "warning",
                "missing_required_section",
                "document",
                f"{doc_type} 文档缺少必要要素：{name}。",
                name,
                f"补充“{name}”相关章节或内容。",
            )
        )

    long_sentences = [sentence for sentence in _sentence_candidates(body) if len(sentence) > 120]
    if long_sentences:
        suggestions.append(
            _make_finding(
                "formality",
                "suggestion",
                "long_sentence",
                "document",
                "存在较长句，可能影响正式文档可读性。",
                long_sentences[0],
                "拆成两句或改为列表。",
            )
        )

    if blockers:
        status = "blocked"
        next_action = "revise_text"
        summary = "当前存在阻断问题，不适合作为正式 docx 输出。"
    elif any(item.get("code") in REVISION_REQUIRED_WARNING_CODES for item in warnings):
        status = "draft_only"
        next_action = "revise_text"
        summary = "当前可作为草稿检查，但不建议直接作为正式 docx 交付。"
    else:
        status = "pass"
        next_action = "render_docx"
        summary = "当前未发现阻断或警告问题，可以进入 docx 渲染。"

    return {
        "status": status,
        "doc_type": doc_type,
        "summary": summary,
        "blockers": blockers,
        "warnings": warnings,
        "suggestions": suggestions,
        "render_notes": [],
        "next_action": next_action,
        "source_path": str(Path(source_path).expanduser().resolve()),
    }


def render_quality_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Docx Quality Report",
        "",
        f"- Status: {report.get('status', '')}",
        f"- Doc type: {report.get('doc_type', '')}",
        f"- Summary: {report.get('summary', '')}",
        f"- Next action: {report.get('next_action', '')}",
        "",
    ]
    for field, title in (("blockers", "Blockers"), ("warnings", "Warnings"), ("suggestions", "Suggestions")):
        lines.extend([f"## {title}", ""])
        items = report.get(field, [])
        if not items:
            lines.extend(["- None", ""])
            continue
        for index, item in enumerate(items, start=1):
            lines.append(f"### {index}. {item.get('code', 'unknown')}")
            lines.append("")
            lines.append(f"- Dimension: {item.get('dimension', '')}")
            lines.append(f"- Severity: {item.get('severity', '')}")
            lines.append(f"- Location: {item.get('location', '')}")
            lines.append(f"- Issue: {item.get('issue', '')}")
            lines.append(f"- Evidence: {item.get('evidence', '')}")
            lines.append(f"- Fix: {item.get('fix', '')}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_quality_reports(report: dict[str, Any], outdir: str | Path) -> dict[str, str]:
    output_dir = Path(outdir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "docx_quality_report.json"
    md_path = output_dir / "docx_quality_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_quality_report_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}
