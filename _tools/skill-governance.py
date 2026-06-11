#!/usr/bin/env python3
"""
Skill governance orchestrator.

最小落地：
1. 读取统一 skill 索引
2. 汇总 usage / score / current-position
3. 计算 active / dormant / repair-needed / archivable
4. 生成机器可读快照与 dashboard 可消费数据
"""

from __future__ import annotations

import argparse
import os
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT_DIR = SCRIPT_DIR.parent


def resolve_workspace_root() -> Path:
    env_root = os.environ.get("SKILL_WORKSPACE_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root).expanduser())
    cwd = Path.cwd()
    candidates.extend([cwd, cwd.parent if cwd.name == "skills" else cwd / "skills"])

    for candidate in candidates:
        if candidate.name == "skills":
            root = candidate.parent
        else:
            root = candidate
        if (root / "skills" / "skill-index.json").exists() or (root / "skill-index.json").exists():
            return root.resolve()
    return DEFAULT_ROOT_DIR


ROOT_DIR = resolve_workspace_root()
SKILLS_DIR = ROOT_DIR / "skills"
INDEX_PATH = SKILLS_DIR / "skill-index.json"
if not INDEX_PATH.exists():
    INDEX_PATH = ROOT_DIR / "skill-index.json"
USAGE_STATS_PATH = SKILLS_DIR / "skill-usage.json"
if not USAGE_STATS_PATH.exists():
    USAGE_STATS_PATH = ROOT_DIR / "skill-usage.json"
USAGE_LOG_PATH = ROOT_DIR / ".claude" / "skill-usage.jsonl"
CURRENT_POSITION_PATH = ROOT_DIR / ".claude" / "memory" / "current-position.md"
SCORES_DIR = ROOT_DIR / "output" / "skill-optimizer" / "runs" / "scores"
CRITIQUES_DIR = ROOT_DIR / "output" / "skill-optimizer" / "runs" / "critiques"
SNAPSHOT_PATH = SKILLS_DIR / "skill-governance.snapshot.json"
DASHBOARD_DATA_PATH = SKILLS_DIR / "skill-governance.data.js"


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def load_recommend_module():
    spec = importlib.util.spec_from_file_location(
        "skill_recommend_module", SCRIPT_DIR / "skill-recommend.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def parse_iso(ts: str | None):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def normalize_path_string(path: str | None) -> str | None:
    if not path:
        return None
    try:
        return str(Path(path).resolve())
    except OSError:
        return str(Path(path))


def normalize_score_payloads() -> list[dict]:
    payloads = []
    if not SCORES_DIR.exists():
        return payloads
    for file in SCORES_DIR.glob("*.json"):
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        payload["_file"] = str(file)
        payload["_normalized_path"] = normalize_path_string(payload.get("path"))
        payloads.append(payload)
    return payloads


def lookup_score_payload(skill: dict, score_payloads: list[dict]) -> dict | None:
    skill_path = normalize_path_string(skill.get("path"))
    if not skill_path:
        return None
    for payload in score_payloads:
        payload_path = payload.get("_normalized_path")
        if payload_path == skill_path:
            return payload
    skill_dir = str(Path(skill_path).parent) if skill_path.endswith("SKILL.md") else str(Path(skill_path))
    for payload in score_payloads:
        payload_path = payload.get("_normalized_path")
        if payload_path and str(Path(payload_path).parent) == skill_dir:
            return payload
    return None


def list_critique_artifacts(skill: dict) -> list[str]:
    if not CRITIQUES_DIR.exists():
        return []
    candidates = {
        skill.get("short_id") or "",
        skill.get("name") or "",
    }
    artifacts = []
    for candidate in candidates:
        if not candidate:
            continue
        critique_dir = CRITIQUES_DIR / candidate
        if critique_dir.exists():
            artifacts.extend(str(path) for path in sorted(critique_dir.glob("*.md")))
    return artifacts


def build_focus_text() -> str:
    if not CURRENT_POSITION_PATH.exists():
        return ""
    return CURRENT_POSITION_PATH.read_text(encoding="utf-8").lower()


def build_focus_query() -> str:
    if not CURRENT_POSITION_PATH.exists():
        return ""
    lines = []
    for raw_line in CURRENT_POSITION_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- **正在进行：") or line.startswith("- **次级活跃:") or line[:2].isdigit():
            lines.append(line)
    return " ".join(lines)[:1200]


def matches_focus(skill: dict, focus_text: str) -> bool:
    if not focus_text:
        return False
    candidates = {
        (skill.get("short_id") or "").lower(),
        (skill.get("name") or "").lower(),
    }
    candidates.update(t.lower() for t in skill.get("triggers", [])[:3])
    candidates = {c for c in candidates if len(c) >= 3}
    return any(c in focus_text for c in candidates)


def compute_usage_windows(records: list[dict]) -> dict[str, dict]:
    now = datetime.now()
    windows = {}
    for record in records:
        skill_id = record.get("skill_id")
        if not skill_id:
            continue
        item = windows.setdefault(
            skill_id,
            {
                "count_7d": 0,
                "count_30d": 0,
                "last_used": None,
                "last_task_summary": None,
                "last_result_type": None,
            },
        )
        ts = parse_iso(record.get("timestamp"))
        if ts:
            if ts > now - timedelta(days=7):
                item["count_7d"] += 1
            if ts > now - timedelta(days=30):
                item["count_30d"] += 1
            if item["last_used"] is None or ts.isoformat() > item["last_used"]:
                item["last_used"] = ts.isoformat()
        item["last_task_summary"] = record.get("task_summary") or record.get("user_input")
        item["last_result_type"] = record.get("result_type") or record.get("source")
    return windows


def derive_governance(skill: dict, usage: dict, score_payload: dict | None, in_focus: bool) -> dict:
    score = None if not score_payload else score_payload.get("current_score")
    if score is None and score_payload:
        score = score_payload.get("total")
    last_used = parse_iso(usage.get("last_used"))
    last_used_days = None if not last_used else (datetime.now() - last_used).days
    modified = parse_iso(skill.get("last_modified"))
    modified_days = None if not modified else (datetime.now() - modified).days

    if score is not None and score < 70:
        status = "repair-needed"
        disposition = "repair"
        reason = f"score_below_threshold:{score}"
    elif in_focus or usage.get("count_7d", 0) > 0:
        status = "active"
        disposition = "promote" if usage.get("count_30d", 0) >= 2 or in_focus else "watch"
        reason = "in_current_focus" if in_focus else "used_within_7d"
    elif (last_used_days is not None and last_used_days >= 30) or (
        last_used_days is None
        and modified_days is not None
        and modified_days >= 30
        and skill.get("source") != "built-in"
    ):
        status = "archivable"
        disposition = "archive"
        reason = "inactive_30d"
    elif (last_used_days is not None and last_used_days >= 7) or (
        last_used_days is None
        and modified_days is not None
        and modified_days >= 7
    ):
        status = "dormant"
        disposition = "watch"
        reason = "inactive_7d"
    else:
        status = "active"
        disposition = "watch"
        reason = "recently_created_or_missing_usage"

    return {
        "status": status,
        "disposition": disposition,
        "reason": reason,
        "current_score": score,
        "last_used_days": last_used_days,
    }


def build_snapshot(query: str | None = None) -> dict:
    index = load_json(INDEX_PATH, {"skills": {}, "summary": {}, "workspaces": []})
    usage_stats_payload = load_json(USAGE_STATS_PATH, {"stats": {}})
    usage_records = load_jsonl(USAGE_LOG_PATH)
    usage_windows = compute_usage_windows(usage_records)
    score_payloads = normalize_score_payloads()
    focus_text = build_focus_text()
    focus_query = build_focus_query()

    skills = []
    governance_counter = Counter()
    disposition_counter = Counter()

    for skill_id, skill in index.get("skills", {}).items():
        usage = usage_windows.get(skill_id, {})
        stats_fallback = usage_stats_payload.get("stats", {}).get(skill_id, {})
        if not usage and stats_fallback:
            usage = {
                "count_7d": 0,
                "count_30d": stats_fallback.get("count", 0),
                "last_used": stats_fallback.get("last_used"),
                "last_task_summary": None,
                "last_result_type": None,
            }

        score_payload = lookup_score_payload(skill, score_payloads)
        critique_files = list_critique_artifacts(skill)
        in_focus = matches_focus(skill, focus_text)
        governance = derive_governance(skill, usage, score_payload, in_focus)

        skills.append(
            {
                "id": skill_id,
                "short_id": skill.get("short_id"),
                "name": skill.get("name"),
                "workspace": skill.get("workspace"),
                "status": skill.get("status"),
                "domain": skill.get("domain"),
                "triggers": skill.get("triggers", []),
                "governance_status": governance["status"],
                "governance_disposition": governance["disposition"],
                "governance_reason": governance["reason"],
                "in_current_focus": in_focus,
                "usage": {
                    "count_7d": usage.get("count_7d", 0),
                    "count_30d": usage.get("count_30d", 0),
                    "last_used": usage.get("last_used"),
                    "last_used_days": governance["last_used_days"],
                    "last_task_summary": usage.get("last_task_summary"),
                    "last_result_type": usage.get("last_result_type"),
                },
                "quality": {
                    "current_score": governance["current_score"],
                    "score_file": score_payload.get("_file") if score_payload else None,
                    "scored_at": score_payload.get("scored_at") if score_payload else None,
                    "has_critique": bool(critique_files),
                    "critique_files": critique_files,
                },
                "path": skill.get("path"),
            }
        )
        governance_counter[governance["status"]] += 1
        disposition_counter[governance["disposition"]] += 1

    skills.sort(
        key=lambda item: (
            item["governance_status"] != "repair-needed",
            item["governance_status"] != "archivable",
            item["governance_status"] != "dormant",
            item["governance_status"] != "active",
            item["short_id"] or item["name"] or item["id"],
        )
    )

    recommendations = []
    focus_recommendations = []
    recommend_module = None
    if query or focus_query:
        recommend_module = load_recommend_module()
    if query and recommend_module:
        for rec in recommend_module.recommend(query):
            skill_row = next((s for s in skills if s["id"] == rec["skill_id"]), None)
            recommendations.append(
                {
                    **rec,
                    "governance_status": skill_row["governance_status"] if skill_row else None,
                    "governance_disposition": skill_row["governance_disposition"] if skill_row else None,
                }
            )
    if focus_query and recommend_module:
        for rec in recommend_module.recommend(focus_query):
            skill_row = next((s for s in skills if s["id"] == rec["skill_id"]), None)
            focus_recommendations.append(
                {
                    **rec,
                    "governance_status": skill_row["governance_status"] if skill_row else None,
                    "governance_disposition": skill_row["governance_disposition"] if skill_row else None,
                }
            )

    return {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "query": query,
            "focus_query": focus_query,
            "sources": {
                "index": str(INDEX_PATH),
                "usage_stats": str(USAGE_STATS_PATH),
                "usage_log": str(USAGE_LOG_PATH),
                "scores_dir": str(SCORES_DIR),
                "current_position": str(CURRENT_POSITION_PATH),
            },
        },
        "summary": {
            "total_skills": len(skills),
            "governance_status": dict(governance_counter),
            "disposition": dict(disposition_counter),
            "scored_skills": len(score_payloads),
            "usage_records": len(usage_records),
        },
        "focus_recommendations": focus_recommendations,
        "recommendations": recommendations,
        "skills": skills,
    }


def write_snapshot(snapshot: dict, output_path: Path = SNAPSHOT_PATH):
    output_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    DASHBOARD_DATA_PATH.write_text(
        "window.SKILL_GOVERNANCE_DATA = "
        + json.dumps(snapshot, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )


def refresh_sources():
    subprocess.run([sys.executable, str(SCRIPT_DIR / "scan-skills.py")], cwd=ROOT_DIR, check=True)
    subprocess.run([sys.executable, str(SCRIPT_DIR / "skill-trace.py")], cwd=ROOT_DIR, check=True)


def print_summary(snapshot: dict):
    summary = snapshot["summary"]
    print("Skill governance snapshot ready")
    print(f"- total skills: {summary['total_skills']}")
    print(f"- governance status: {summary['governance_status']}")
    print(f"- disposition: {summary['disposition']}")
    print(f"- scored skills: {summary['scored_skills']}")
    print(f"- usage records: {summary['usage_records']}")
    if snapshot.get("focus_recommendations"):
        print("- focus recommendations:")
        for rec in snapshot["focus_recommendations"]:
            print(
                f"  - {rec['name']} score={rec['score']} "
                f"status={rec['governance_status']} reasons={'; '.join(rec['reasons'][:2])}"
            )
    if snapshot["recommendations"]:
        print("- recommendations:")
        for rec in snapshot["recommendations"]:
            print(
                f"  - {rec['name']} score={rec['score']} "
                f"status={rec['governance_status']} reasons={'; '.join(rec['reasons'][:2])}"
            )
    print(f"- snapshot: {SNAPSHOT_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Generate a unified skill governance snapshot.")
    parser.add_argument("--refresh", action="store_true", help="先刷新 skill 索引和 usage 再生成快照")
    parser.add_argument("--query", help="附带生成一组推荐结果")
    parser.add_argument("--output", default=str(SNAPSHOT_PATH), help="快照输出路径")
    args = parser.parse_args()

    if args.refresh:
        refresh_sources()

    snapshot = build_snapshot(query=args.query)
    write_snapshot(snapshot, Path(args.output))
    print_summary(snapshot)


if __name__ == "__main__":
    main()
