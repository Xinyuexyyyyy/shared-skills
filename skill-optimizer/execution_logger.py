"""
execution_logger.py — skill 执行日志记录

L1 自动记录：每次 skill 执行后调用 log()
L2 手动反思：用户补充问题分析时调用 reflect()

存储：../../output/skill-optimizer/runs/logs/executions/{date}.jsonl
"""
import os
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone


def get_exec_dir(output_dir: Path) -> Path:
    d = output_dir / "logs" / "executions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_date():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _exec_file(output_dir: Path, date=None):
    return get_exec_dir(output_dir) / f"{date or _get_date()}.jsonl"


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+08:00")


# ── L1: 自动记录 ─────────────────────────────────────

def log(
    output_dir: Path,
    skill: str,
    action: str,
    result: str,
    duration_ms: int = 0,
    tokens_used: int = 0,
    error: str = None,
    session: str = "main",
    extra: dict = None,
) -> str:
    """
    记录一次 skill 执行。

    Returns:
        execution_id (用于后续 reflect)
    """
    execution_id = uuid.uuid4().hex[:12]

    record = {
        "id": execution_id,
        "timestamp": _now(),
        "session": session,
        "skill": skill,
        "action": action,
        "result": result,
        "error": error,
        "duration_ms": duration_ms,
        "tokens_used": tokens_used,
    }

    if extra:
        record["extra"] = extra

    # L2 反思字段默认 null
    record["problem"] = None
    record["root_cause"] = None
    record["solution"] = None
    record["avoid"] = None
    record["optimize"] = None

    f = _exec_file(output_dir)
    with open(f, "a", encoding="utf-8") as fp:
        fp.write(json.dumps(record, ensure_ascii=False) + "\n")

    return execution_id


# ── L2: 手动反思 ─────────────────────────────────────

def reflect(
    output_dir: Path,
    execution_id: str,
    problem: str = None,
    root_cause: str = None,
    solution: str = None,
    avoid: str = None,
    optimize: str = None,
    date: str = None,
) -> dict:
    """
    用户手动补充反思：问题、根因、解决方案、规避方法、优化建议。
    """
    if not date:
        date = _get_date()

    f = _exec_file(output_dir, date)
    if not f.exists():
        return {"error": f"No log file for {date}"}

    updated = 0
    lines = []
    found = False

    with open(f, encoding="utf-8") as fp:
        for line in fp:
            rec = json.loads(line.strip())
            if rec.get("id") == execution_id:
                if problem: rec["problem"] = problem
                if root_cause: rec["root_cause"] = root_cause
                if solution: rec["solution"] = solution
                if avoid: rec["avoid"] = avoid
                if optimize: rec["optimize"] = optimize
                found = True
            lines.append(rec)

    if found:
        with open(f, "w", encoding="utf-8") as fp:
            for rec in lines:
                fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
        updated = 1

    return {"ok": True, "updated": updated, "found": found}


def log_manual(
    output_dir: Path,
    skill: str,
    action: str,
    result: str,
    problem: str = None,
    root_cause: str = None,
    solution: str = None,
    avoid: str = None,
    optimize: str = None,
    duration_ms: int = 0,
    tokens_used: int = 0,
    error: str = None,
    session: str = "main",
) -> str:
    """手动记录一次执行"""
    execution_id = uuid.uuid4().hex[:12]

    record = {
        "id": execution_id,
        "timestamp": _now(),
        "session": session,
        "skill": skill,
        "action": action,
        "result": result,
        "error": error,
        "duration_ms": duration_ms,
        "tokens_used": tokens_used,
        "problem": problem,
        "root_cause": root_cause,
        "solution": solution,
        "avoid": avoid,
        "optimize": optimize,
        "_manual": True,
    }

    f = _exec_file(output_dir)
    with open(f, "a", encoding="utf-8") as fp:
        fp.write(json.dumps(record, ensure_ascii=False) + "\n")

    return execution_id


# ── 查询 ────────────────────────────────────────────

def get_executions(output_dir: Path, skill: str = None, date: str = None, limit: int = 100) -> list:
    """读取执行日志"""
    if date:
        files = [_exec_file(output_dir, date)]
    else:
        from datetime import timedelta
        dates = [(datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
                 for i in range(30)]
        files = [_exec_file(output_dir, d) for d in reversed(dates)]

    records = []
    for f in files:
        if not f.exists():
            continue
        with open(f, encoding="utf-8") as fp:
            for line in fp:
                rec = json.loads(line.strip())
                if skill and rec.get("skill") != skill:
                    continue
                records.append(rec)
                if len(records) >= limit:
                    break
        if len(records) >= limit:
            break

    return records[-limit:]


def get_problems(output_dir: Path, skill: str = None, days: int = 7) -> list:
    """获取所有有 problem 标记的记录"""
    from datetime import timedelta
    dates = [(datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
             for i in range(days)]
    records = []
    for d in reversed(dates):
        f = _exec_file(output_dir, d)
        if not f.exists():
            continue
        with open(f, encoding="utf-8") as fp:
            for line in fp:
                rec = json.loads(line.strip())
                if rec.get("problem") and (not skill or rec.get("skill") == skill):
                    records.append(rec)
    return records
