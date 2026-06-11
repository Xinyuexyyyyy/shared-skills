#!/usr/bin/env python3
"""
Skill 推荐器
根据用户输入的任务描述，推荐可能匹配的 skill
"""

import json
import os
import sys
from difflib import SequenceMatcher
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INDEX_PATH = SCRIPT_DIR / "skill-index.json"
_RESOLVED_INDEX_PATH = None
_WORKSPACE_ROOT = None


def resolve_index_path():
    """优先用当前工作区索引，其次回退到脚本同目录索引。"""
    global _RESOLVED_INDEX_PATH, _WORKSPACE_ROOT
    if _RESOLVED_INDEX_PATH is not None:
        return _RESOLVED_INDEX_PATH

    env_path = os.environ.get("SKILL_INDEX_PATH")
    cwd = Path.cwd()
    candidates = []
    if env_path:
        candidates.append(Path(env_path).expanduser())
    candidates.extend(
        [
            cwd / "skills" / "skill-index.json",
            cwd / "skill-index.json",
            DEFAULT_INDEX_PATH,
        ]
    )

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        if resolved.exists():
            _RESOLVED_INDEX_PATH = resolved
            if resolved.parent.name == "skills":
                _WORKSPACE_ROOT = resolved.parent.parent
            else:
                _WORKSPACE_ROOT = resolved.parent
            return _RESOLVED_INDEX_PATH

    raise FileNotFoundError("skill-index.json not found in cwd or shared tools directory")


def load_skills():
    with open(resolve_index_path(), "r", encoding="utf-8") as f:
        return json.load(f)


def similarity(a, b):
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _skill_scope(skill):
    """给推荐结果一个稳定的优先级：当前工作区 > built-in > 其他工作区。"""
    workspace_root = _WORKSPACE_ROOT or resolve_index_path().parent
    path = skill.get("path")
    if path:
        try:
            resolved = Path(path).resolve()
            if resolved == workspace_root or workspace_root in resolved.parents:
                return "local"
        except OSError:
            pass
    if skill.get("source") == "built-in" or skill.get("status") == "built-in":
        return "built-in"
    return "external"


def _candidate_rank(item):
    scope_rank = {"local": 2, "built-in": 1, "external": 0}.get(item.get("scope"), 0)
    status_rank = {"stable": 3, "draft": 2, "unknown": 1, "built-in": 1}.get(item.get("status"), 0)
    return (item["score"], scope_rank, status_rank, -len(item.get("path") or ""))


def recommend(query, top_k=3):
    """根据用户输入推荐 skill"""
    idx = load_skills()
    query_lower = query.lower()
    intent_boosts = {
        "先对齐一下工作方式": {"skill-optimizer": 30},
        "对齐工作方式": {"skill-optimizer": 30},
        "校准协作方式": {"skill-optimizer": 30},
        "锐评一下": {"skill-optimizer": 18, "critique": 8},
        "锐评": {"skill-optimizer": 18, "critique": 8},
        "你有什么 skill": {"skill-dashboard": 30},
        "你有什么能力": {"skill-dashboard": 30},
        "看看我的技能": {"skill-dashboard": 30},
        "帮我拆一下": {"task-decompose": 24},
        "拆一下这个任务": {"task-decompose": 24},
        "拆解任务": {"task-decompose": 24},
        "复杂任务": {"task-crafter": 24, "project-sop": 10},
        "规划一个复杂任务": {"task-crafter": 28, "project-sop": 10},
        "复杂项目": {"task-crafter": 24, "project-sop": 12},
        "帮我做个新项目": {"project-sop": 28, "task-crafter": 10},
        "新项目": {"project-sop": 22, "task-crafter": 8},
        "开始一个项目": {"project-sop": 24, "task-crafter": 8},
        "优化一个 skill": {"skill-optimizer": 24, "simplify": 4},
    }

    best_by_skill = {}

    for sid, skill in idx["skills"].items():
        score = 0
        reasons = []
        short_id = skill.get("short_id") or skill.get("name") or skill["id"]

        for phrase, boosts in intent_boosts.items():
            if phrase in query:
                for target, boost in boosts.items():
                    if short_id == target or skill["name"] == target:
                        score += boost
                        reasons.append(f"意图短语命中: {phrase}")

        # 1. 触发词精确匹配（权重最高）
        for trigger in skill.get("triggers", []):
            trigger_lower = trigger.lower()
            if trigger_lower in query_lower:
                score += 10
                reasons.append(f"触发词命中: {trigger}")
            elif similarity(trigger_lower, query_lower) > 0.6:
                score += 5
                reasons.append(f"触发词相似: {trigger}")

        # 2. 名称匹配
        name_lower = skill["name"].lower()
        if name_lower in query_lower:
            score += 8
            reasons.append("名称命中")
        elif similarity(name_lower, query_lower) > 0.5:
            score += 3
            reasons.append("名称相似")

        # 3. 描述关键词匹配
        desc = skill.get("description", "").lower()
        # 提取 query 中的关键词（2字以上）
        keywords = [w for w in set(query_lower.split()) if len(w) >= 2]
        matched_keywords = [w for w in keywords if w in desc]
        if matched_keywords:
            score += len(matched_keywords) * 2
            reasons.append(f"描述关键词: {', '.join(matched_keywords[:3])}")

        # 4. 领域匹配
        domain = skill.get("domain", "").lower()
        if domain in query_lower:
            score += 4
            reasons.append(f"领域命中: {domain}")

        if score > 0:
            candidate = {
                "skill_id": sid,
                "short_id": short_id,
                "name": skill["name"],
                "description": skill["description"][:80] + "...",
                "status": skill["status"],
                "domain": skill.get("domain", ""),
                "scope": _skill_scope(skill),
                "path": skill.get("path", ""),
                "score": score,
                "reasons": reasons,
            }
            current = best_by_skill.get(short_id)
            if current is None or _candidate_rank(candidate) > _candidate_rank(current):
                best_by_skill[short_id] = candidate

    results = sorted(best_by_skill.values(), key=lambda x: _candidate_rank(x), reverse=True)
    return results[:top_k]


def main():
    if len(sys.argv) < 2:
        print("用法: python3 skill-recommend.py \"任务描述\"")
        print("示例: python3 skill-recommend.py \"帮我分析一下竞品的定价策略\"")
        sys.exit(1)

    query = sys.argv[1]
    results = recommend(query)

    if not results:
        print(f"🔍 没有找到匹配的 skill")
        print(f"   输入: \"{query}\"")
        print(f"   建议: 换个说法，或者直接说 skill 名")
        return

    print(f"🔍 根据 \"{query}\" 推荐:")
    print()

    for i, r in enumerate(results, 1):
        status_icon = "✅" if r["status"] == "stable" else "📝" if r["status"] == "draft" else "🔧"
        print(f"{i}. {status_icon} {r['name']} [{r['status']}] (匹配度: {r['score']})")
        print(f"   {r['description']}")
        print(f"   原因: {'; '.join(r['reasons'])}")
        print()


if __name__ == "__main__":
    main()
