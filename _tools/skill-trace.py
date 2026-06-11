#!/usr/bin/env python3
"""
Skill 使用追踪器
从 Claude Code 历史日志中反推 skill 使用记录
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT_DIR = SCRIPT_DIR.parent


def resolve_root_dir() -> Path:
    env_root = os.environ.get("SKILL_WORKSPACE_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root).expanduser())
    cwd = Path.cwd()
    candidates.extend([cwd, cwd.parent if cwd.name == "skills" else cwd / "skills"])
    for candidate in candidates:
        root = candidate.parent if candidate.name == "skills" else candidate
        if (root / ".claude").exists() and ((root / "skills").exists() or (root / "skill-index.json").exists()):
            return root.resolve()
    return DEFAULT_ROOT_DIR


ROOT_DIR = resolve_root_dir()

# === 配置 ===
HISTORY_PATH = os.path.expanduser("~/.claude/history.jsonl")
USAGE_PATH = ROOT_DIR / ".claude" / "skill-usage.jsonl"
SKILL_INDEX_PATH = ROOT_DIR / "skills" / "skill-index.json"
if not SKILL_INDEX_PATH.exists():
    SKILL_INDEX_PATH = ROOT_DIR / "skill-index.json"
SKILL_USAGE_JSON_PATH = ROOT_DIR / "skills" / "skill-usage.json"
DASHBOARD_DATA_PATH = ROOT_DIR / "skills" / "skill-dashboard.data.js"


def load_skill_triggers():
    """从 skill-index.json 加载所有 skill 的触发词"""
    with open(SKILL_INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)

    triggers = []
    for sid, skill in index["skills"].items():
        for trigger in skill.get("triggers", []):
            if trigger and len(trigger) > 1:
                triggers.append({
                    "skill_id": sid,
                    "skill_name": skill["name"],
                    "trigger": trigger.lower(),
                    "domain": skill.get("domain", "general"),
                })
    return triggers


def scan_history(triggers, max_lines=2000):
    """扫描历史日志，匹配 skill 使用记录"""
    usage = []

    if not Path(HISTORY_PATH).exists():
        return usage

    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                text = record.get("display", "")
                if not text:
                    continue

                text_lower = text.lower()
                ts = record.get("timestamp", 0)
                session = record.get("sessionId", "unknown")
                project = record.get("project", "")

                # 匹配每个 skill 的触发词
                for t in triggers:
                    trigger_lower = t["trigger"].lower()
                    # 简单匹配：触发词出现在用户输入中
                    # 排除过于短或通用的触发词（避免误匹配）
                    if len(trigger_lower) < 2:
                        continue
                    if trigger_lower in text_lower:
                        usage.append({
                            "timestamp": datetime.fromtimestamp(ts / 1000).isoformat() if ts else None,
                            "session_id": session,
                            "skill_id": t["skill_id"],
                            "skill_name": t["skill_name"],
                            "trigger_matched": t["trigger"],
                            "user_input": text[:100],
                            "project": project,
                            "source": "history",
                        })
                        break  # 一条记录只匹配一个 skill（第一个命中的）

            except (json.JSONDecodeError, KeyError):
                continue

    return usage


def merge_with_existing(new_usage):
    """合并新记录与已有记录，去重"""
    existing = []
    if USAGE_PATH.exists():
        with open(USAGE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        existing.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    # 用 (session_id, skill_id, user_input) 去重
    seen = set()
    for u in existing:
        key = (u.get("session_id", ""), u.get("skill_id", ""), u.get("user_input", ""))
        seen.add(key)

    merged = existing.copy()
    for u in new_usage:
        key = (u.get("session_id", ""), u.get("skill_id", ""), u.get("user_input", ""))
        if key not in seen:
            merged.append(u)
            seen.add(key)

    return merged


def write_usage(usage_records):
    """写入使用记录到 JSONL"""
    USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_PATH, "w", encoding="utf-8") as f:
        for record in usage_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def compute_stats(usage_records):
    """计算使用统计"""
    stats = {}
    for u in usage_records:
        sid = u["skill_id"]
        if sid not in stats:
            stats[sid] = {
                "count": 0,
                "last_used": None,
                "sessions": set(),
            }
        stats[sid]["count"] += 1
        stats[sid]["sessions"].add(u.get("session_id", ""))
        ts = u.get("timestamp")
        if ts and (stats[sid]["last_used"] is None or ts > stats[sid]["last_used"]):
            stats[sid]["last_used"] = ts

    # 把 set 转成 count
    for sid in stats:
        stats[sid]["session_count"] = len(stats[sid]["sessions"])
        del stats[sid]["sessions"]

    return stats


def generate_usage_json():
    """生成 usage stats 供仪表盘读取"""
    records = []
    if USAGE_PATH.exists():
        with open(USAGE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    stats = compute_stats(records)

    usage_json = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
        },
        "stats": stats,
    }

    with open(SKILL_USAGE_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(usage_json, f, ensure_ascii=False, indent=2)

    return usage_json


def write_dashboard_data(index_path=None, usage_path=None, output_path=None):
    """同步写入 dashboard 本地快照，保证 file:// 直开也能看到最新使用统计。"""
    index_file = Path(index_path) if index_path else SKILL_INDEX_PATH
    usage_file = Path(usage_path) if usage_path else SKILL_USAGE_JSON_PATH
    if not index_file.exists() or not usage_file.exists():
        return

    with open(index_file, "r", encoding="utf-8") as f:
        index = json.load(f)
    with open(usage_file, "r", encoding="utf-8") as f:
        usage = json.load(f)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "index": index,
        "usage": usage,
    }

    output_file = Path(output_path) if output_path else DASHBOARD_DATA_PATH
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("window.SKILL_DASHBOARD_DATA = ")
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write(";\n")


def main():
    print("🔍 扫描历史日志，提取 skill 使用记录...")

    triggers = load_skill_triggers()
    print(f"  已加载 {len(triggers)} 个触发词")

    new_usage = scan_history(triggers)
    print(f"  从历史日志中发现 {len(new_usage)} 条使用记录")

    merged = merge_with_existing(new_usage)
    print(f"  合并后共 {len(merged)} 条记录")

    write_usage(merged)
    print(f"  已写入 {USAGE_PATH}")

    usage_json = generate_usage_json()
    print(f"  已生成 skill-usage.json ({len(usage_json['stats'])} 个 skill 有使用记录)")
    write_dashboard_data()
    print("  已同步更新 skill-dashboard.data.js")

    # 打印统计
    print("\n📊 使用统计:")
    for sid, s in sorted(usage_json["stats"].items(), key=lambda x: -x[1]["count"])[:10]:
        last = s["last_used"][:10] if s["last_used"] else "N/A"
        print(f"  {sid:30s} 使用 {s['count']:3d} 次  最后: {last}")


if __name__ == "__main__":
    main()
