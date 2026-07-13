from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from document_classifier import infer_document_type
from source_loader import load_markdown


DOC_TYPE_ALIASES = {
    "project_report": "formal_report",
    "paper_like": "formal_report",
}

SUPPORTED_DOC_TYPES = {
    "formal_report",
    "proposal",
    "technical",
    "technical_disclosure",
    "abstract",
    "manual",
    "runtime_record",
    "meeting_note",
    "content_article",
}

COLLOQUIAL_REPLACEMENTS = (
    (r"这个东西现在能跑", "当前输出链路已具备基础运行能力"),
    (r"这个东西", "当前事项"),
    (r"太薄了", "内容结构不足"),
    (r"有点水", "内容密度不足，缺少结构化展开"),
    (r"围着那几句话绕来绕去", "对用户前置条件存在重复复述"),
    (r"写得很口语", "表达不符合正式 docx 交付要求"),
    (r"挺烦的", "影响正式文档的阅读和交付质量"),
    (r"弄一个正式点的关", "建立正式文档输出前的质量门控"),
    (r"后面要弄一个正式点的关", "后续应建立正式文档输出前的质量门控"),
    (r"别让这种稿子直接出 docx", "避免不具备交付条件的草稿直接进入 docx 输出"),
    (r"别乱编事实", "扩写层不得新增未经提供的事实、数据、政策或结论"),
)

REPETITIVE_PHRASES = (
    "提升输出质量",
    "优化输出体验",
    "形成输出闭环",
    "提升质量",
    "优化用户体验",
    "完善机制",
    "推动质量提升",
    "高质量",
    "闭环",
)

FACT_SIGNAL_RE = re.compile(r"\d|案例|样例|日志|截图|实验|试验|验证|数据|指标|结果|依据|政策|标准|文献|参考|版本|接口|端口")
HUMAN_CONFIRMATION_RE = re.compile(r"预算|附件|政策|标准|版本号|端口|PID|实验结果|申报资格")
WEAK_ACTION_RE = re.compile(r"(加强|推动|完善|提升|优化)([\u4e00-\u9fffA-Za-z0-9]{0,12})")

UNSUPPORTED_CLAIM_RULES = (
    (
        re.compile(r"(实践证明|已经证明)"),
        "downgrade_unsupported_claim",
        "将超出证据范围的确定性结论降级为待验证表述。",
        "原文包含“实践证明”或“已经证明”等无证据支撑的确定性结论。",
        "待验证：需要补充验证过程后再形成结论",
    ),
    (
        re.compile(r"显著提升"),
        "downgrade_unsupported_claim",
        "将“显著提升”降级为待验证效果。",
        "原文包含未给出对比指标的效果判断。",
        "效果有待通过对比指标进一步验证",
    ),
    (
        re.compile(r"完全解决"),
        "downgrade_unsupported_claim",
        "将“完全解决”降级为处理目标。",
        "原文包含超出证据范围的完全性结论。",
        "目标是用于处理相关问题，实际效果仍需验证",
    ),
    (
        re.compile(r"符合申报要求"),
        "mark_human_confirmation",
        "将需专家或机构判断的合规结论标记为人工确认项。",
        "原文直接给出“符合申报要求”结论。",
        "是否符合申报要求需结合当年指南人工确认",
    ),
    (
        re.compile(r"具备(创新性|先进性|合规性)"),
        "mark_human_confirmation",
        "将需评审判断的性质结论标记为人工确认项。",
        "原文直接给出创新性、先进性或合规性判断。",
        "相关判断需结合评审标准和事实依据人工确认",
    ),
)

DOC_TYPE_DEFAULT_PLACEHOLDERS: dict[str, tuple[tuple[str, str], ...]] = {
    "formal_report": (
        ("缺少事实依据", "待补充：当前问题对应的真实样例、抽样结果或验证记录。"),
        ("行动项信息不足", "待补充：下一步行动的对象、执行条件和验收方式。"),
    ),
    "proposal": (
        ("缺少事实依据", "待补充：立项依据对应的业务痛点、外部要求或已验证事实。"),
        ("缺少事实依据", "待补充：研究基础、资源条件或前期验证结果。"),
    ),
    "technical_disclosure": (
        ("缺少事实依据", "待补充：现有技术缺陷的具体场景、参数或失败表现。"),
        ("缺少事实依据", "待补充：技术效果的验证结果、对比数据或实验记录。"),
    ),
    "abstract": (
        ("缺少事实依据", "待补充：方法或材料的关键参数。"),
        ("缺少事实依据", "待补充：结果或发现的可复核表述。"),
    ),
    "manual": (
        ("缺少事实依据", "待补充：适用版本、依赖环境或前置权限要求。"),
        ("缺少事实依据", "待补充：常见异常场景、报错表现和处理边界。"),
    ),
}


def _doc_type(frontmatter: dict[str, Any]) -> str:
    raw = str(frontmatter.get("doc_type") or frontmatter.get("type") or "formal_report").strip()
    normalized = DOC_TYPE_ALIASES.get(raw, raw) or "formal_report"
    if normalized == "technical":
        return "technical_disclosure"
    if normalized not in SUPPORTED_DOC_TYPES:
        return "formal_report"
    if normalized in {"runtime_record", "meeting_note", "content_article"}:
        return "formal_report"
    return normalized


def _reported_doc_type(frontmatter: dict[str, Any], body: str) -> str:
    raw = str(frontmatter.get("doc_type") or frontmatter.get("type") or "").strip()
    normalized = DOC_TYPE_ALIASES.get(raw, raw)
    if normalized in SUPPORTED_DOC_TYPES:
        return normalized
    return str(infer_document_type(frontmatter, body)["doc_type"])


def _expansion_template_doc_type(doc_type: str) -> str:
    if doc_type == "technical":
        return "technical_disclosure"
    if doc_type in {"runtime_record", "meeting_note", "content_article"}:
        return "formal_report"
    if doc_type in SUPPORTED_DOC_TYPES:
        return doc_type
    return "formal_report"


def _mode(frontmatter: dict[str, Any], override: str | None = None) -> str:
    raw = str(override or frontmatter.get("expansion_mode") or "structured").strip().lower()
    if raw not in {"off", "conservative", "structured"}:
        return "structured"
    return raw


def _plain_text(body: str) -> str:
    text = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+[.)、]\s+", "", text, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", text).strip()


def _has_heading(body: str) -> bool:
    return bool(re.search(r"^#{1,6}\s+\S+", body, re.MULTILINE))


def _headings(body: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    in_code = False
    for line_no, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        match = re.match(r"^(#{1,6})\s+(.*\S)\s*$", line)
        if match:
            items.append({"level": len(match.group(1)), "text": match.group(2).strip(), "line": line_no})
    return items


def _source_title(body: str) -> str | None:
    for item in _headings(body):
        title = str(item["text"]).strip()
        if title in {"输入", "草稿", "原文"}:
            continue
        return title
    return None


def _has_meaningful_source_structure(body: str) -> bool:
    title = _source_title(body)
    if not title:
        return False
    return len(_headings(body)) >= 2


def _body_without_title(body: str) -> str:
    title = _source_title(body)
    if not title:
        return body.strip()
    skipped = False
    lines: list[str] = []
    for line in body.splitlines():
        if not skipped and re.match(r"^#{1,6}\s+" + re.escape(title) + r"\s*$", line.strip()):
            skipped = True
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _sentence_count(text: str) -> int:
    parts = re.split(r"[。！？!?；;]\s*", text)
    return len([part for part in parts if part.strip()])


def _excerpt(text: str, limit: int = 140) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def _is_output_layer_context(text: str) -> bool:
    return any(token in text for token in ("输出层", "output-layer", "docx", "质量门"))


def _formalize_text(text: str) -> tuple[str, bool]:
    changed = False
    result = text
    for pattern, replacement in COLLOQUIAL_REPLACEMENTS:
        updated = re.sub(pattern, replacement, result)
        if updated != result:
            changed = True
            result = updated
    return result, changed


def _contains_repetition(text: str) -> bool:
    lowered = text.lower()
    hits = 0
    for phrase in REPETITIVE_PHRASES:
        if phrase.lower() in lowered:
            hits += 1
    return hits >= 2


def _weak_action_fragments(text: str) -> list[str]:
    items: list[str] = []
    for match in WEAK_ACTION_RE.finditer(text):
        verb, tail = match.groups()
        tail = tail or ""
        if tail.startswith(("后", "前")):
            continue
        fragment = f"{verb}{tail}".strip()
        if fragment and fragment not in items:
            items.append(fragment)
    return items


def _has_fact_support(text: str) -> bool:
    return bool(FACT_SIGNAL_RE.search(text))


def _needs_user_input(text: str) -> bool:
    compact = text.strip()
    if not compact:
        return True
    if len(compact) < 18:
        return True
    if _sentence_count(compact) <= 1 and len(compact) < 40:
        return True
    return False


def _make_action(code: str, description: str, evidence: str) -> dict[str, str]:
    return {"code": code, "description": description, "evidence": evidence}


def _add_action(
    actions: list[dict[str, str]],
    seen_codes: set[str],
    code: str,
    description: str,
    evidence: str,
) -> None:
    if code in seen_codes:
        return
    actions.append(_make_action(code, description, evidence))
    seen_codes.add(code)


def _add_blocked(
    blocked: list[dict[str, str]],
    seen_placeholders: set[str],
    reason: str,
    placeholder: str,
) -> None:
    if placeholder in seen_placeholders:
        return
    blocked.append({"reason": reason, "placeholder": placeholder})
    seen_placeholders.add(placeholder)


def _downgrade_unsupported_claims(
    text: str,
    actions: list[dict[str, str]],
    seen_codes: set[str],
    blocked: list[dict[str, str]],
    seen_placeholders: set[str],
) -> str:
    updated = text
    for pattern, code, description, evidence, replacement in UNSUPPORTED_CLAIM_RULES:
        if not pattern.search(updated):
            continue
        updated = pattern.sub(replacement, updated)
        _add_action(actions, seen_codes, code, description, evidence)
        if code == "downgrade_unsupported_claim":
            _add_blocked(
                blocked,
                seen_placeholders,
                "缺少事实依据",
                "待补充：支撑确定性判断的验证过程、对比数据或外部依据。",
            )
        if code == "mark_human_confirmation":
            _add_blocked(
                blocked,
                seen_placeholders,
                "需人工确认",
                "待补充：相关合规、创新或评审结论的正式依据，并由人工确认。",
            )
    return updated


def _append_default_placeholders(
    doc_type: str,
    analysis: dict[str, Any],
    blocked: list[dict[str, str]],
    seen_placeholders: set[str],
) -> None:
    if analysis.get("preserve_topic") and doc_type == "formal_report":
        return
    if analysis["has_fact_support"]:
        return
    for reason, placeholder in DOC_TYPE_DEFAULT_PLACEHOLDERS[doc_type]:
        _add_blocked(blocked, seen_placeholders, reason, placeholder)
    has_action_placeholder = any("行动" in item["placeholder"] or "验收" in item["placeholder"] for item in blocked)
    if analysis["weak_actions"] and not has_action_placeholder:
        _add_blocked(
            blocked,
            seen_placeholders,
            "行动项信息不足",
            "待补充：行动对象、执行条件和结果判定方式。",
        )
    human_confirmation = HUMAN_CONFIRMATION_RE.findall(analysis["plain_text"])
    if human_confirmation:
        _add_blocked(
            blocked,
            seen_placeholders,
            "需人工确认",
            "待补充：涉及预算、政策、标准或版本号的内容需人工确认。",
        )


def _format_placeholder_lines(blocked: list[dict[str, str]]) -> list[str]:
    if not blocked:
        return ["- None"]
    return [f"- {item['placeholder']}" for item in blocked]


def _quality_gate_sentence(analysis: dict[str, Any]) -> str:
    if analysis["output_layer_context"]:
        return "建议按“正式扩写 -> `docx_quality_report` -> `assisted_quality_report`”的顺序继续处理。"
    return "建议先完成正式扩写，再进入后续质量检查或人工复核。"


def _report_title(doc_type: str, analysis: dict[str, Any]) -> str:
    if doc_type == "formal_report" and analysis["output_layer_context"]:
        return "输出层正式写作质量关建设说明"
    if doc_type == "proposal":
        return "项目申请材料扩写稿"
    if doc_type == "technical_disclosure":
        return "技术说明扩写稿"
    if doc_type == "abstract":
        return "摘要扩写稿"
    if doc_type == "manual":
        return "使用说明扩写稿"
    return "正式文档扩写稿"


def _compose_markdown(title: str, sections: list[tuple[str, list[str]]]) -> str:
    lines = [f"# {title}", ""]
    for heading, paragraphs in sections:
        lines.append(f"## {heading}")
        lines.append("")
        for paragraph in paragraphs:
            if paragraph.startswith(("- ", "1. ", "2. ", "3. ")):
                lines.append(paragraph)
            else:
                lines.append(paragraph)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _preserve_topic_formal_report(title: str, body: str, analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    body_content = _body_without_title(body)
    intro = "本稿在保留原始主题和已给信息的基础上，补充正式文档所需的说明、边界和后续处理口径。"
    if "会议纪要" in title:
        intro = "本纪要用于记录已确认事项和后续动作，并为后续正式输出、回归验证和文档收口提供依据。"
    boundary = [
        "本次扩写只整理原文已给出的讨论结果和后续动作，不新增未提供的事实、数据、责任人或完成期限。",
        "如需进入正式交付，应补充责任对象、完成条件和验收方式。",
    ]
    return [
        ("一、文档目的", [intro]),
        (
            "二、原始内容整理",
            [
                body_content,
            ],
        ),
        (
            "三、依据与边界",
            boundary,
        ),
        (
            "四、结论与下一步",
            [
                "当前内容可作为正式初稿继续进入质量检查。",
                "下一步应根据质量报告决定是否补充事实依据、行动条件或人工确认项。",
            ],
        ),
    ]


def _structured_formal_report(analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    problem = "当前原稿存在结构不足、表达偏口语、观点重复或事实边界不清的问题，不适合直接进入正式交付。"
    if analysis["repetitive"]:
        problem = "当前原稿重复使用抽象目标词，缺少对象、动作和验收方式，信息密度不足。"
    plan_line = "如原稿只给出抽象目标，本稿将其收敛为可审阅的对象、问题、处理动作和下一步安排。"
    result_line = "当前可先将扩写稿作为正式初稿，再依据质量报告决定是继续渲染、回修正文还是先补事实。"
    if analysis["repetitive"]:
        plan_line = "建议将流程收敛为扩写、检查、修订、再输出，避免继续堆叠抽象口号。"
        result_line = "后续应通过质量报告区分可渲染、需修订或需补事实，再决定是否进入正式交付。"
    return [
        (
            "一、建设目的",
            [
                "本稿用于将短输入、口语化输入或重复空泛输入整理为可审阅的正式文档初稿，并保持原始立场不变。",
            ],
        ),
        (
            "二、现有问题与背景",
            [
                problem,
                f"原始输入可归纳为：{analysis['source_excerpt']}",
            ],
        ),
        (
            "三、处理原则与方案",
            [
                "扩写层只补结构、表达、过渡、边界和行动项，不新增未经提供的事实、数据、政策或结论。",
                "如涉及引用、项目基础或研究结果，仍应保持原文边界，不在扩写阶段自行补写。",
                _quality_gate_sentence(analysis),
                plan_line,
            ],
        ),
        (
            "四、依据与边界",
            [
                "以下内容因原稿未提供可复核依据，当前只能以待补充形式保留：",
                *_format_placeholder_lines(analysis["blocked"]),
            ],
        ),
        (
            "五、结论与下一步",
            [
                result_line,
                "如需进入正式交付，应优先补齐事实依据、行动条件和人工确认项。",
            ],
        ),
    ]


def _conservative_formal_report(analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    return [
        (
            "一、当前状态",
            [
                "当前输出链路已具备基础运行能力，但正文仍可能存在内容密度不足、结构展开不充分或表达不够正式的问题。",
            ],
        ),
        (
            "二、主要问题",
            [
                f"原始输入可归纳为：{analysis['source_excerpt']}",
                "上述问题会直接影响正式文档的阅读体验和交付稳定性。",
            ],
        ),
        (
            "三、控制目标",
            [
                "后续应建立正式文档输出前的质量门控，对结构完整性、表达正式性、内容重复和事实边界进行检查。",
                "若原稿只停留在抽象口号，应先补齐对象、动作和验收方式，再继续下游处理。",
            ],
        ),
        (
            "四、输出边界",
            [
                "质量门控只判断文稿是否具备进入正式 docx 的条件，不替代事实核验、合规审查或机构口径确认。",
                "如需进入正式交付，至少补充以下信息：",
                *_format_placeholder_lines(analysis["blocked"]),
            ],
        ),
    ]


def _structured_proposal(analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    return [
        (
            "一、立项依据",
            [
                "当前输入反映了一个待收敛的项目设想，但尚未形成可直接评审的立项依据。",
                f"原始输入可归纳为：{analysis['source_excerpt']}",
            ],
        ),
        (
            "二、研究目标",
            [
                "本稿目标是把现有想法整理为明确的问题定义、研究目标和后续行动，而不是提前给出未经验证的结论。",
            ],
        ),
        (
            "三、研究内容",
            [
                "建议围绕研究对象、关键问题、实施步骤和阶段性产出展开正文，并保持事实边界清晰。",
            ],
        ),
        (
            "四、创新与边界",
            [
                "创新性、先进性或合规性不在本稿内直接下结论；如缺少对比依据，应以待补充形式保留。",
                *_format_placeholder_lines(analysis["blocked"][:1]),
            ],
        ),
        (
            "五、可行性与研究基础",
            [
                "可行性判断应基于已有资源、前期工作和验证基础，当前缺失部分需显式标记。",
                *_format_placeholder_lines(analysis["blocked"][1:2]),
            ],
        ),
        (
            "六、预期成果与下一步",
            [
                "预期成果应限定在现有证据范围内表述，并在补齐研究基础后继续进入质量检查或申报写作。",
            ],
        ),
    ]


def _conservative_proposal(analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    return [
        (
            "一、立项依据",
            [
                f"原始输入可归纳为：{analysis['source_excerpt']}",
                "当前材料可作为立项动机说明，但不足以直接支撑完整申报。",
            ],
        ),
        (
            "二、研究目标与内容",
            [
                "建议先将研究目标、主要任务和预期成果分开表述，避免重复使用抽象判断。",
            ],
        ),
        (
            "三、研究基础与边界",
            [
                "涉及研究基础、资源条件和创新性判断的内容必须补充事实依据后再形成正式表述。",
                *_format_placeholder_lines(analysis["blocked"]),
            ],
        ),
    ]


def _structured_technical_disclosure(analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    return [
        (
            "一、技术问题、目的与背景",
            [
                "本稿用于将现有技术描述整理为正式说明，不对未验证效果作确定性判断。",
                f"原始输入可归纳为：{analysis['source_excerpt']}",
            ],
        ),
        (
            "二、技术方案",
            [
                "建议按组成部分、处理流程和关键动作描述技术方案，避免只保留口号式目标。",
            ],
        ),
        (
            "三、技术效果与验证需求",
            [
                "技术效果只能表述到已有证据范围内；缺少对比实验、参数或日志时，应保留为待补充。",
                *_format_placeholder_lines(analysis["blocked"][:1]),
            ],
        ),
        (
            "四、依据与边界条件",
            [
                "涉及参数、标准、版本、接口或人工确认口径的内容，应集中放在边界条件中说明。",
                *_format_placeholder_lines(analysis["blocked"][1:]),
            ],
        ),
        (
            "五、结论与下一步",
            [
                "当前可先形成技术说明初稿，待补齐验证依据后再进入正式评审、专利或交付流程。",
            ],
        ),
    ]


def _conservative_technical_disclosure(analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    return [
        (
            "一、技术问题与方案概述",
            [
                f"原始输入可归纳为：{analysis['source_excerpt']}",
                "当前材料适合先整理为问题、方案和边界三部分，不宜直接给出效果结论。",
            ],
        ),
        (
            "二、效果与边界",
            [
                "所有效果判断应降级到“待验证”范围内，未提供验证过程或对比数据时不得直接宣称改进结果。",
                *_format_placeholder_lines(analysis["blocked"]),
            ],
        ),
    ]


def _structured_abstract(analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    return [
        (
            "一、对象与问题",
            [
                "本稿用于将原始想法压缩为摘要结构，先交代研究对象、问题指向和写作边界。",
                f"原始输入可归纳为：{analysis['source_excerpt']}",
            ],
        ),
        (
            "二、方法与材料",
            [
                "方法和材料只能依据现有输入整理；关键参数、样本或材料信息缺失时需直接标记。",
                *_format_placeholder_lines(analysis["blocked"][:1]),
            ],
        ),
        (
            "三、结果与发现",
            [
                "结果部分不得补写未提供的数据或发现，当前缺失项应以待补充保留。",
                *_format_placeholder_lines(analysis["blocked"][1:2]),
            ],
        ),
        (
            "四、意义与边界",
            [
                "意义表述应与原始证据强度一致，不扩大为创新性、先进性或推广价值结论。",
            ],
        ),
    ]


def _conservative_abstract(analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    return [
        (
            "一、对象、方法与结果概述",
            [
                f"原始输入可归纳为：{analysis['source_excerpt']}",
                "当前可先整理为摘要概述，但关键参数和结果仍需补充。",
            ],
        ),
        (
            "二、意义与边界",
            [
                "摘要中的意义判断不得超出原始证据范围；缺少材料、结果或对比时应保留待补充标记。",
                *_format_placeholder_lines(analysis["blocked"]),
            ],
        ),
    ]


def _structured_manual(analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    return [
        (
            "一、适用对象",
            [
                "本稿用于整理当前流程说明，帮助后续把零散说明收敛成可复核的使用文档。",
                f"原始输入可归纳为：{analysis['source_excerpt']}",
            ],
        ),
        (
            "二、前置条件",
            [
                "执行前应确认适用版本、依赖环境、权限要求和输入材料；原稿未提供的部分需保留待补充。",
                *_format_placeholder_lines(analysis["blocked"][:1]),
            ],
        ),
        (
            "三、操作步骤",
            [
                "1. 待补充：第一步的具体入口、命令或界面位置。",
                "2. 待补充：核心操作动作、顺序和结果确认方式。",
                "3. 待补充：完成后的输出物、记录要求或下一步流转。",
            ],
        ),
        (
            "四、注意事项",
            [
                "注意事项只记录已有边界，不额外补写未提供的限制条件或风险结论。",
            ],
        ),
        (
            "五、异常处理",
            [
                "异常处理应覆盖报错表现、排查边界和人工接管条件；当前缺失项需显式保留。",
                *_format_placeholder_lines(analysis["blocked"][1:]),
            ],
        ),
    ]


def _conservative_manual(analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    return [
        (
            "一、适用对象与前置条件",
            [
                f"原始输入可归纳为：{analysis['source_excerpt']}",
                "当前说明可作为操作意图记录，但不足以直接充当正式使用说明。",
            ],
        ),
        (
            "二、步骤与异常边界",
            [
                "在没有具体入口、命令或界面顺序前，不应补写具体步骤；应先保留待补充项。",
                *_format_placeholder_lines(analysis["blocked"]),
            ],
        ),
    ]


def _sections_for(doc_type: str, mode: str, analysis: dict[str, Any]) -> list[tuple[str, list[str]]]:
    if analysis.get("preserve_topic") and doc_type == "formal_report":
        return _preserve_topic_formal_report(str(analysis["source_title"]), str(analysis["source_body"]), analysis)
    if doc_type == "formal_report":
        return _conservative_formal_report(analysis) if mode == "conservative" else _structured_formal_report(analysis)
    if doc_type == "proposal":
        return _conservative_proposal(analysis) if mode == "conservative" else _structured_proposal(analysis)
    if doc_type == "technical_disclosure":
        return (
            _conservative_technical_disclosure(analysis)
            if mode == "conservative"
            else _structured_technical_disclosure(analysis)
        )
    if doc_type == "abstract":
        return _conservative_abstract(analysis) if mode == "conservative" else _structured_abstract(analysis)
    if doc_type == "manual":
        return _conservative_manual(analysis) if mode == "conservative" else _structured_manual(analysis)
    return _structured_formal_report(analysis)


def _build_summary(status: str, mode: str) -> str:
    if status == "skipped":
        return "formal expansion 已关闭。"
    if status == "needs_user_input":
        return "已生成基础骨架，但关键信息不足；缺失事实已保留为待补充。"
    if mode == "conservative":
        return "已按保守模式整理表达和结构，缺失事实以待补充标记保留。"
    return "已生成正式扩写稿，缺失事实以待补充标记保留。"


def _build_revision_plan(actions: list[dict[str, str]], blocked: list[dict[str, str]]) -> list[dict[str, str]]:
    plan: list[dict[str, str]] = []
    action_index: dict[str, int] = {}

    def merge_field(existing: str, addition: str) -> str:
        if not addition or addition in existing:
            return existing
        trimmed = existing.rstrip("。；; ")
        return f"{trimmed}；{addition}"

    def add(action: str, target: str, reason: str, instruction: str) -> None:
        if action not in action_index:
            action_index[action] = len(plan)
            plan.append({"action": action, "target": target, "reason": reason, "instruction": instruction})
            return

        item = plan[action_index[action]]
        item["target"] = merge_field(item["target"], target)
        item["reason"] = merge_field(item["reason"], reason)
        item["instruction"] = merge_field(item["instruction"], instruction)

    action_codes = {item.get("code", "") for item in actions}
    if "merge_repeated_claims" in action_codes:
        add(
            "合并重复表达",
            "正文中反复出现的质量、体验、闭环类表述",
            "重复抽象词会降低信息密度。",
            "保留一次核心判断，并补充对象、动作、条件或验收方式。",
        )
    if "complete_action_item_shape" in action_codes:
        add(
            "补齐行动项",
            "弱行动项",
            "行动项缺少对象、执行条件或结果判定方式。",
            "把“加强/推动/完善/提升”改为“面向谁，在什么条件下，执行什么动作，达到什么结果”。",
        )
    if "downgrade_unsupported_claim" in action_codes:
        add(
            "降级结论",
            "无依据的确定性判断",
            "原文没有提供验证过程、对比数据或外部依据。",
            "将“证明/显著提升/完全解决”等表述改为“待验证/目标是/需进一步验证”。",
        )
    if "mark_human_confirmation" in action_codes:
        add(
            "人工确认",
            "合规、创新性、先进性或机构口径判断",
            "这些判断不能由扩写层自动给出。",
            "补充正式依据，并由负责人或对应机构确认。",
        )
    for item in blocked:
        reason = str(item.get("reason", ""))
        placeholder = str(item.get("placeholder", ""))
        if "事实" in reason:
            add(
                "补充事实依据",
                placeholder.replace("待补充：", "") or "事实依据",
                "扩写层不能编造事实、数据、案例或来源。",
                "补充可复核的真实样例、抽样结果、验证记录、来源或责任人口径。",
            )
        elif "行动" in reason:
            add(
                "补齐行动项",
                placeholder.replace("待补充：", "") or "行动项",
                "行动项信息不足。",
                "补充行动对象、执行条件、完成标准和验收方式。",
            )
        elif "人工" in reason:
            add(
                "人工确认",
                placeholder.replace("待补充：", "") or "人工确认项",
                "该内容涉及事实、合规或机构口径。",
                "在正式交付前由人工确认，不由扩写层代替判断。",
            )
    return plan


def _source_excerpt(formal_text: str, repetitive: bool) -> str:
    if repetitive:
        return "当前事项需要围绕明确对象、处理动作和验收方式建立正式流程，避免重复使用提升质量、优化体验、形成闭环等抽象表述。"
    return _excerpt(formal_text)


def _render_frontmatter(frontmatter: dict[str, Any]) -> str:
    if not frontmatter:
        return ""
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"- {item}")
            continue
        lines.append(f"{key}: {value}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def expand_formal_markdown(source_path: str | Path, mode_override: str | None = None) -> dict[str, Any]:
    document = load_markdown(str(source_path))
    frontmatter = dict(document.get("frontmatter", {}))
    body = str(document["body"])
    report_doc_type = _reported_doc_type(frontmatter, body)
    doc_type = _expansion_template_doc_type(report_doc_type)
    mode = _mode(frontmatter, mode_override)
    actions: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    seen_codes: set[str] = set()
    seen_placeholders: set[str] = set()

    if mode == "off":
        report = {
            "status": "skipped",
            "doc_type": report_doc_type,
            "template_doc_type": doc_type,
            "mode": mode,
            "summary": _build_summary("skipped", mode),
            "actions": [],
            "blocked_expansions": [],
            "revision_plan": [],
            "next_action": "render_or_review",
            "source_path": str(Path(source_path).expanduser().resolve()),
        }
        return {
            "expanded_markdown": str(document["body"]).lstrip(),
            "frontmatter": frontmatter,
            "report": report,
        }

    plain_text = _plain_text(body)
    if not plain_text:
        _add_blocked(blocked, seen_placeholders, "输入为空", "待补充：正文内容。")
        report = {
            "status": "needs_user_input",
            "doc_type": report_doc_type,
            "template_doc_type": doc_type,
            "mode": mode,
            "summary": _build_summary("needs_user_input", mode),
            "actions": [],
            "blocked_expansions": blocked,
            "revision_plan": _build_revision_plan([], blocked),
            "next_action": "fill_missing_facts",
            "source_path": str(Path(source_path).expanduser().resolve()),
        }
        return {
            "expanded_markdown": "# 正式文档扩写稿\n\n待补充：正文内容。\n",
            "frontmatter": frontmatter,
            "report": report,
        }

    if len(plain_text) < 300 or not _has_heading(body):
        _add_action(
            actions,
            seen_codes,
            "build_formal_skeleton",
            "识别为短输入或缺少正式章节，进入骨架扩写。",
            "原文少于 300 字或缺少正式章节。",
        )

    formal_text, changed = _formalize_text(plain_text)
    if changed:
        _add_action(
            actions,
            seen_codes,
            "formalize_colloquial_expression",
            "将口语化表达改为正式说明。",
            "原文包含“太薄了”“这个东西”“挺烦的”等口语化表达。",
        )

    formal_text = _downgrade_unsupported_claims(formal_text, actions, seen_codes, blocked, seen_placeholders)

    repetitive = _contains_repetition(plain_text)
    if repetitive:
        _add_action(
            actions,
            seen_codes,
            "merge_repeated_claims",
            "合并重复的抽象目标表述。",
            "原文多次出现提升质量、优化体验、形成闭环等低信息表达。",
        )

    weak_actions = _weak_action_fragments(plain_text)
    if weak_actions:
        _add_action(
            actions,
            seen_codes,
            "complete_action_item_shape",
            "为弱行动项补充对象、条件和结果边界。",
            f"原文包含抽象行动项：{', '.join(weak_actions[:3])}",
        )

    analysis: dict[str, Any] = {
        "plain_text": plain_text,
        "formal_text": formal_text,
        "source_excerpt": _source_excerpt(formal_text, repetitive),
        "repetitive": repetitive,
        "has_fact_support": _has_fact_support(plain_text),
        "weak_actions": weak_actions,
        "output_layer_context": _is_output_layer_context(plain_text),
        "preserve_topic": mode == "structured" and _has_meaningful_source_structure(body),
        "source_title": _source_title(body),
        "source_body": body,
    }

    _append_default_placeholders(doc_type, analysis, blocked, seen_placeholders)
    if blocked:
        _add_action(
            actions,
            seen_codes,
            "add_boundary_placeholders",
            "对缺少事实依据或需人工确认的位置保留待补充标记。",
            "原文未提供足够事实依据，无法安全扩写为确定性内容。",
        )

    if analysis["preserve_topic"]:
        _add_action(
            actions,
            seen_codes,
            "preserve_source_topic",
            "保留原始标题和章节职责进行正式扩写。",
            "原稿已有明确标题和章节结构。",
        )

    sections = _sections_for(doc_type, mode, {**analysis, "blocked": blocked})
    title = str(analysis["source_title"]) if analysis["preserve_topic"] else _report_title(doc_type, analysis)
    expanded = _compose_markdown(title, sections)

    status = "needs_user_input" if _needs_user_input(plain_text) else "expanded"
    next_action = "fill_missing_facts" if status == "needs_user_input" else "quality_check"
    report = {
        "status": status,
        "doc_type": report_doc_type,
        "template_doc_type": doc_type,
        "mode": mode,
        "summary": _build_summary(status, mode),
        "actions": actions,
        "blocked_expansions": blocked,
        "revision_plan": _build_revision_plan(actions, blocked),
        "next_action": next_action,
        "source_path": str(Path(source_path).expanduser().resolve()),
    }
    return {
        "expanded_markdown": expanded,
        "frontmatter": frontmatter,
        "report": report,
    }


def render_expansion_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Formal Expansion Report",
        "",
        f"- Status: {report.get('status', '')}",
        f"- Doc type: {report.get('doc_type', '')}",
        f"- Mode: {report.get('mode', '')}",
        f"- Summary: {report.get('summary', '')}",
        f"- Next action: {report.get('next_action', '')}",
        f"- Source: {report.get('source_path', '')}",
        "",
        "## Actions",
        "",
    ]
    actions = report.get("actions", [])
    if not actions:
        lines.extend(["- None", ""])
    for index, action in enumerate(actions, start=1):
        lines.append(f"### {index}. {action.get('code', 'unknown')}")
        lines.append("")
        lines.append(f"- Description: {action.get('description', '')}")
        lines.append(f"- Evidence: {action.get('evidence', '')}")
        lines.append("")
    lines.extend(["## Blocked Expansions", ""])
    blocked = report.get("blocked_expansions", [])
    if not blocked:
        lines.extend(["- None", ""])
    for index, item in enumerate(blocked, start=1):
        lines.append(f"### {index}. {item.get('reason', '')}")
        lines.append("")
        lines.append(f"- Placeholder: {item.get('placeholder', '')}")
        lines.append("")
    lines.extend(["## Revision Plan", ""])
    revision_plan = report.get("revision_plan", [])
    if not revision_plan:
        lines.extend(["- None", ""])
    for index, item in enumerate(revision_plan, start=1):
        lines.append(f"### {index}. {item.get('action', '')}")
        lines.append("")
        lines.append(f"- Target: {item.get('target', '')}")
        lines.append(f"- Reason: {item.get('reason', '')}")
        lines.append(f"- Instruction: {item.get('instruction', '')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_expansion_outputs(result: dict[str, Any], outdir: str | Path) -> dict[str, str]:
    output_dir = Path(outdir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    expanded_path = output_dir / "output.expanded.md"
    json_path = output_dir / "formal_expansion_report.json"
    md_path = output_dir / "formal_expansion_report.md"
    expanded_document = f"{_render_frontmatter(dict(result.get('frontmatter', {})))}{str(result['expanded_markdown']).lstrip()}"
    expanded_path.write_text(expanded_document, encoding="utf-8")
    json_path.write_text(json.dumps(result["report"], ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_expansion_report_markdown(result["report"]), encoding="utf-8")
    return {"expanded": str(expanded_path), "json": str(json_path), "markdown": str(md_path)}
