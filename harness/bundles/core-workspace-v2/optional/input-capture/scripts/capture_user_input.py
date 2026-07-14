#!/usr/bin/env python3
"""Manual capture tool for a workspace-local harness inbox.

This is intentionally dependency-free and conservative. It preserves raw input
first, writes optional distill cards only for useful classes, and refuses to
store obvious secrets.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Iterable


INBOX_ROOT = Path.cwd() / ".claude" / "capture"
RAW_DIR = INBOX_ROOT / "user-input"
CARD_DIR = INBOX_ROOT / "inspiration-cards"


SENSITIVE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:password|passwd|pwd|token|secret|api[_-]?key)\s*[:=]\s*\S+", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b不要记录\b|\b别存\b|\b敏感\b"),
)


CLASS_KEYWORDS = {
    "research_seed": (
        "调研",
        "研究",
        "找论文",
        "论文",
        "竞品",
        "市场",
        "PRD",
        "产品发现",
        "research",
        "literature",
    ),
    "task_seed": (
        "做",
        "实现",
        "修",
        "优化",
        "接入",
        "清理",
        "改造",
        "落地",
        "build",
        "implement",
        "fix",
    ),
    "memory_candidate": (
        "以后每次",
        "我希望",
        "我要求",
        "默认",
        "不要",
        "必须",
        "偏好",
        "规则",
    ),
    "inspiration": (
        "灵感",
        "想法",
        "启发",
        "洞察",
        "可以",
        "也许",
        "idea",
        "inspiration",
        "insight",
    ),
}


CARD_CLASSES = {"inspiration", "task_seed", "research_seed", "memory_candidate"}


@dataclass(frozen=True)
class Classification:
    name: str
    confidence: str
    signals: tuple[str, ...]
    next_route_hint: str | None
    actions_allowed: tuple[str, ...]
    summary: str
    sensitive: bool = False
    sensitive_reason: str | None = None


def now_local() -> datetime:
    return datetime.now().astimezone()


def stable_id(captured_at: datetime, text: str, source: str) -> str:
    digest = hashlib.sha1(f"{captured_at.isoformat()}|{source}|{text}".encode("utf-8")).hexdigest()[:8]
    return f"{captured_at.strftime('%Y%m%d-%H%M%S')}-{digest}"


def read_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text.strip()
    if args.file:
        return Path(args.file).read_text(encoding="utf-8").strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise SystemExit("Provide --text, --file, or stdin input.")


def contains_sensitive(text: str) -> str | None:
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            return pattern.pattern
    return None


def compact_summary(text: str, limit: int = 120) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def keyword_hits(text: str, keywords: Iterable[str]) -> list[str]:
    lowered = text.lower()
    hits = []
    for keyword in keywords:
        if keyword.lower() in lowered:
            hits.append(keyword)
    return hits


def classify(text: str) -> Classification:
    sensitive_reason = contains_sensitive(text)
    if sensitive_reason:
        return Classification(
            name="sensitive_skip",
            confidence="high",
            signals=("sensitive",),
            next_route_hint=None,
            actions_allowed=("redacted_record_only",),
            summary="Input looked sensitive, so raw text was not stored.",
            sensitive=True,
            sensitive_reason=sensitive_reason,
        )

    if len(text.strip()) < 12:
        return Classification(
            name="none",
            confidence="high",
            signals=("too_short",),
            next_route_hint=None,
            actions_allowed=("raw_record_only",),
            summary=compact_summary(text),
        )

    hits_by_class = {
        class_name: keyword_hits(text, keywords)
        for class_name, keywords in CLASS_KEYWORDS.items()
    }
    scored = sorted(
        ((class_name, len(hits), hits) for class_name, hits in hits_by_class.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    best_class, best_score, best_hits = scored[0]

    if best_score == 0:
        return Classification(
            name="none",
            confidence="medium",
            signals=("no_keyword_signal",),
            next_route_hint=None,
            actions_allowed=("raw_record_only",),
            summary=compact_summary(text),
        )

    route_hint = {
        "inspiration": None,
        "task_seed": "task_draft_or_tasks_after_confirmation",
        "research_seed": "deep-research_or_idea-to-research_after_confirmation",
        "memory_candidate": "memory_write_requires_confirmation",
    }[best_class]

    action = "card_only" if best_class == "inspiration" else "seed_card_only"
    confidence = "high" if best_score >= 2 else "medium"
    return Classification(
        name=best_class,
        confidence=confidence,
        signals=tuple(best_hits[:6]),
        next_route_hint=route_hint,
        actions_allowed=(action,),
        summary=compact_summary(text),
    )


def record_for(raw_id: str, captured_at: datetime, args: argparse.Namespace, text: str, cls: Classification) -> dict:
    stored_text = None if cls.sensitive else text
    return {
        "id": raw_id,
        "captured_at": captured_at.isoformat(),
        "workspace": args.workspace,
        "source": args.source,
        "session_id": args.session_id,
        "cwd": args.cwd,
        "classification": cls.name,
        "confidence": cls.confidence,
        "sensitive": cls.sensitive,
        "sensitive_reason": cls.sensitive_reason,
        "text": stored_text,
        "summary": cls.summary,
        "signals": list(cls.signals),
        "actions_allowed": list(cls.actions_allowed),
        "next_route_hint": cls.next_route_hint,
    }


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def card_text(raw_id: str, captured_at: datetime, args: argparse.Namespace, payload: dict) -> str:
    route = payload["next_route_hint"] or "none"
    action = ", ".join(payload["actions_allowed"])
    signals = ", ".join(payload["signals"]) or "none"
    return (
        f"\n## {captured_at.strftime('%Y-%m-%d %H:%M')} · {payload['classification']} · {payload['confidence']}\n\n"
        f"- **Source:** {args.source}\n"
        f"- **Raw ID:** {raw_id}\n"
        f"- **Digest:** {payload['summary']}\n"
        f"- **Signals:** {signals}\n"
        f"- **Default action:** {action}\n"
        f"- **Route hint:** {route}\n"
    )


def append_card(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# Input Capture Cards · {path.stem}\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture user input into a workspace-local inbox.")
    parser.add_argument("--text", help="User input text to capture.")
    parser.add_argument("--file", help="Path to a UTF-8 text file to capture.")
    parser.add_argument("--source", default="manual", help="Input source label.")
    parser.add_argument("--session-id", default=None, help="Optional runtime session id.")
    parser.add_argument("--cwd", default=None, help="Optional working directory where the input was submitted.")
    parser.add_argument("--workspace", default="workspace", help="Workspace label.")
    parser.add_argument("--inbox-root", default=str(INBOX_ROOT), help="Inbox root for raw input and cards.")
    parser.add_argument("--dry-run", action="store_true", help="Print payload without writing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = read_text(args)
    captured_at = now_local()
    cls = classify(text)
    raw_id = stable_id(captured_at, text, args.source)
    payload = record_for(raw_id, captured_at, args, text, cls)

    inbox_root = Path(args.inbox_root)
    raw_path = inbox_root / "user-input" / f"{captured_at.strftime('%Y-%m-%d')}.jsonl"
    card_path = inbox_root / "inspiration-cards" / f"{captured_at.strftime('%Y-%m')}.md"

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    append_jsonl(raw_path, payload)
    wrote_card = False
    if cls.name in CARD_CLASSES and not cls.sensitive:
        append_card(card_path, card_text(raw_id, captured_at, args, payload))
        wrote_card = True

    print(json.dumps({
        "ok": True,
        "id": raw_id,
        "classification": cls.name,
        "raw_path": str(raw_path),
        "card_path": str(card_path) if wrote_card else None,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
