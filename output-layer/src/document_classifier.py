from __future__ import annotations

import re
from typing import Any


DOC_TYPE_ALIASES = {
    "project_report": "formal_report",
    "paper_like": "abstract",
    "technical_disclosure": "technical",
    "patent_like": "technical",
    "article": "content_article",
    "wechat_article": "content_article",
    "meeting": "meeting_note",
    "meeting_minutes": "meeting_note",
    "runtime_report": "runtime_record",
    "system_overview": "runtime_record",
}

SUPPORTED_DOC_TYPES = {
    "formal_report",
    "proposal",
    "technical",
    "technical_disclosure",
    "abstract",
    "manual",
    "content_article",
    "meeting_note",
    "runtime_record",
    "policy",
}

HEADING_RE = re.compile(r"^#{1,6}\s+(.*\S)\s*$", re.MULTILINE)
RUNTIME_RE = re.compile(r"(?:PID|端口|监听|版本|运行时间|127\.0\.0\.1|(?:\d{1,3}\.){3}\d{1,3})")


def _normalize_doc_type(raw: object) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    normalized = DOC_TYPE_ALIASES.get(text, text)
    if normalized == "technical_disclosure":
        return "technical"
    if normalized in SUPPORTED_DOC_TYPES:
        return normalized
    return ""


def _headings(body: str) -> list[str]:
    return [match.group(1).strip() for match in HEADING_RE.finditer(body)]


def infer_document_type(frontmatter: dict[str, Any], body: str) -> dict[str, Any]:
    explicit = _normalize_doc_type(frontmatter.get("doc_type") or frontmatter.get("type"))
    if explicit:
        return {"doc_type": explicit, "source": "frontmatter", "signals": ["doc_type"]}

    headings = _headings(body)
    heading_text = "\n".join(headings)
    signals: list[str] = []

    if "标题备选" in heading_text or ("核心命题" in heading_text and "正文" in heading_text):
        signals.append("标题备选" if "标题备选" in heading_text else "核心命题")
        return {"doc_type": "content_article", "source": "heuristic", "signals": signals}

    if "会议纪要" in heading_text or ("讨论结果" in heading_text and "后续动作" in heading_text):
        signals.append("会议纪要" if "会议纪要" in heading_text else "讨论结果+后续动作")
        return {"doc_type": "meeting_note", "source": "heuristic", "signals": signals}

    if ("系统概况" in heading_text or "运行记录" in heading_text or "全景扫描" in heading_text) and RUNTIME_RE.search(body):
        signals.append("运行事实")
        return {"doc_type": "runtime_record", "source": "heuristic", "signals": signals}

    if any(token in heading_text for token in ("立项依据", "研究目标", "研究内容", "预期成果")):
        signals.append("申请类章节")
        return {"doc_type": "proposal", "source": "heuristic", "signals": signals}

    if any(token in heading_text for token in ("技术问题", "技术方案", "技术效果", "实施方式")):
        signals.append("技术说明章节")
        return {"doc_type": "technical", "source": "heuristic", "signals": signals}

    if any(token in heading_text for token in ("适用对象", "前置条件", "操作步骤", "异常处理")):
        signals.append("说明书章节")
        return {"doc_type": "manual", "source": "heuristic", "signals": signals}

    return {"doc_type": "formal_report", "source": "default", "signals": []}
