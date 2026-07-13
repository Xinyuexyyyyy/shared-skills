"""
rubric.py — 8维度 SKILL.md 评分引擎

结构维度（60分）：纯静态文本分析，零外部依赖
效果维度（25分）：由 Claude 在对话中评估，或退化为启发式评分
"""
import os
import re
import json
from pathlib import Path

# 评分维度定义
DIMENSIONS = [
    ("frontmatter",   "Frontmatter质量",      8),
    ("workflow",       "工作流清晰度",          15),
    ("boundary",      "边界条件覆盖",          10),
    ("checkpoint",     "检查点设计",             7),
    ("specificity",    "指令具体性",             15),
    ("resources",      "资源整合度",             5),
    ("architecture",  "整体架构",              15),
    ("effectiveness", "实测表现",              25),
]

MAX_TOTAL = 100


def load_skill_md(skill_path: str) -> tuple[str, dict]:
    """读取 SKILL.md，返回 (body_text, frontmatter_dict)"""
    p = Path(skill_path)
    # 如果传入的是目录，找目录下的 SKILL.md
    if p.is_dir():
        p = p / "SKILL.md"
    if not p.exists():
        raise FileNotFoundError(f"SKILL.md not found: {p}")

    text = p.read_text(encoding="utf-8")

    # 解析 frontmatter
    fm = {}
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if m:
        fm_text = m.group(1)
        current_key = None
        for line in fm_text.splitlines():
            if not line.strip():
                continue
            if re.match(r"^\w+:\s*", line):
                k, v = line.split(":", 1)
                current_key = k.strip()
                fm[current_key] = v.strip()
            elif current_key:
                fm[current_key] += "\n" + line
        body = text[m.end():]
    else:
        body = text

    return body, fm


def score_frontmatter(fm: dict, body: str) -> tuple[int, str]:
    """维度1: Frontmatter质量（8分）"""
    score = 0
    reasons = []

    name = fm.get("name", "")
    desc = fm.get("description", "")

    # name 规范
    if name and re.match(r"^[a-z0-9_-]+$", name):
        score += 3
        reasons.append("name规范")
    elif name:
        reasons.append(f"name格式: {name}")

    # description 含触发词
    trigger_words = ["当", "当用户", "触发", "使用", "skill"]
    if desc and any(w in desc for w in trigger_words):
        score += 3
        reasons.append("description含触发词")
    elif desc:
        reasons.append("description缺少触发词")

    # 长度
    if len(desc) <= 1024:
        score += 2
    else:
        reasons.append(f"description过长({len(desc)}>1024)")

    return score, "; ".join(reasons) if reasons else "OK"


def score_workflow(body: str) -> tuple[int, str]:
    """维度2: 工作流清晰度（15分）"""
    score = 0
    reasons = []

    steps = re.findall(r"(?:^|\n)\s*(?:\d+[.)]|[-*]\s+|[A-Z][.)]\s+)", body)
    if len(steps) >= 3:
        score += 6
        reasons.append(f"步骤数:{len(steps)}")
    elif len(steps) > 0:
        score += 3
        reasons.append(f"步骤偏少:{len(steps)}")

    io_keywords = ["输入", "输出", "参数", "返回", "调用", "action", "input", "output"]
    io_count = sum(1 for kw in io_keywords if kw in body)
    if io_count >= 4:
        score += 5
        reasons.append("输入输出清晰")
    elif io_count >= 2:
        score += 2
        reasons.append(f"输入输出一般({io_count})")

    if re.search(r"(?i)##?\s+(stage|phase|step|节点)", body):
        score += 4
        reasons.append("有阶段结构")

    return min(score, 15), "; ".join(reasons) if reasons else "OK"


def score_boundary(body: str) -> tuple[int, str]:
    """维度3: 边界条件覆盖（10分）"""
    score = 0
    reasons = []

    boundary_keywords = [
        "异常", "错误", "失败", "fallback", "超时", "limit",
        "边界", "如果", "when", "except", "error", "timeout",
        "降级", "重试", "退避", "回滚", "限流", "并发"
    ]
    count = sum(1 for kw in boundary_keywords if re.search(kw, body, re.I))
    if count >= 8:
        score += 6
        reasons.append(f"边界覆盖充分({count})")
    elif count >= 4:
        score += 4
        reasons.append(f"边界覆盖一般({count})")
    elif count >= 2:
        score += 2
        reasons.append(f"边界覆盖偏少({count})")

    if re.search(r"(?i)(\*\*条件\*\*.*：.*\n\*\*处理\*\*.*：)", body):
        score += 4
        reasons.append("有明确的条件-处理错误处理")
    elif re.search(r"(?i)(如果.*失败|如果.*超时|如果.*错误|异常时|error.*处理|except|处理.*：)", body):
        score += 2
        reasons.append("有错误处理但不够明确")

    return min(score, 10), "; ".join(reasons) if reasons else "OK"


def score_checkpoint(body: str) -> tuple[int, str]:
    """维度4: 检查点设计（7分）"""
    score = 0
    reasons = []

    checkpoint_keywords = [
        "确认", "暂停", "等用户", "展示", "向用户", "展示给",
        "confirm", "pause", "await", "check"
    ]
    count = sum(1 for kw in checkpoint_keywords if kw in body)
    if count >= 2:
        score += 5
        reasons.append(f"检查点充分({count})")
    elif count == 1:
        score += 2
        reasons.append(f"检查点偏少({count})")

    if re.search(r"(?i)(确认后再|等用户确认|先确认)", body):
        score += 2
        reasons.append("关键决策有确认")

    return min(score, 7), "; ".join(reasons) if reasons else "OK"


def score_specificity(body: str) -> tuple[int, str]:
    """维度5: 指令具体性（15分）"""
    score = 0
    reasons = []

    examples = re.findall(r"```", body)
    if len(examples) >= 2:
        score += 5
        reasons.append(f"示例充分({len(examples)//2})")
    elif len(examples) >= 1:
        score += 2
        reasons.append("有示例")

    concrete_patterns = [
        r"`[^`]+`",
        r"(?:file|path|url|api|key)[:：]\s*\S+",
    ]
    concrete_count = sum(len(re.findall(p, body, re.I)) for p in concrete_patterns)
    if concrete_count >= 5:
        score += 5
        reasons.append("指令具体")
    elif concrete_count >= 2:
        score += 3
        reasons.append(f"指令较具体({concrete_count})")

    vague_words = ["等等", "之类", "什么的", "若干", "一些", "若干"]
    vague_count = sum(1 for w in vague_words if w in body)
    if vague_count == 0:
        score += 5
    elif vague_count <= 2:
        score += 2
        reasons.append(f"少量模糊词({vague_count})")

    return min(score, 15), "; ".join(reasons) if reasons else "OK"


def score_resources(body: str) -> tuple[int, str]:
    """维度6: 资源整合度（5分）"""
    score = 0
    reasons = []

    ref_patterns = [
        r"\[.*?\]\(.*?\)",
        r"`[^`]+`",
        r"(?:script|file|skill|module)[:：]\s*\S+",
    ]
    ref_count = sum(len(re.findall(p, body)) for p in ref_patterns)
    if ref_count >= 3:
        score += 3
        reasons.append(f"引用充分({ref_count})")

    if re.search(r"(?:path|dir|folder|目录)[:：]", body, re.I):
        score += 2
        reasons.append("有路径规范")

    return min(score, 5), "; ".join(reasons) if reasons else "OK"


def score_architecture(body: str) -> tuple[int, str]:
    """维度7: 整体架构（15分）"""
    score = 0
    reasons = []

    headers = re.findall(r"^#{1,3}\s+", body, re.MULTILINE)
    if len(headers) >= 4:
        score += 5
        reasons.append(f"层次清晰({len(headers)}标题)")
    elif len(headers) >= 2:
        score += 3

    lines = [l.strip() for l in body.splitlines() if l.strip()]
    if len(lines) < 20:
        score += 3
        reasons.append(f"内容简洁({len(lines)}行)")
    elif len(lines) > 500:
        score -= 2
        reasons.append(f"内容过长({len(lines)}行)")

    if re.search(r"(?i)##?\s+action", body):
        score += 4
        reasons.append("action结构清晰")
    if re.search(r"(?i)##?\s+(skill|tool)", body):
        score += 3
        reasons.append("skill/tool结构清晰")

    return max(0, min(score, 15)), "; ".join(reasons) if reasons else "OK"


def score_effectiveness(skill_path: str, has_tested: bool = False) -> tuple[int, str]:
    """
    维度8: 实测表现（25分）

    在当前环境下，实测需要 Claude 在对话中完成。
    如果没有实测数据，退化为启发式评分。
    """
    if has_tested:
        # 如果用户提供了实测反馈，由 Claude 打分
        return 20, "已实测，具体分数由 Claude 评估"

    # 启发式评分：基于代码文件存在性判断
    p = Path(skill_path)
    if p.is_dir():
        has_py = (p / "skill.py").exists()
        has_js = (p / "skill.js").exists() or (p / "index.js").exists()
        has_tests = list(p.glob("*test*")) or list(p.glob("*spec*"))

        score = 10
        reasons = ["无实测数据，启发式评分"]
        if has_py or has_js:
            score += 3
            reasons.append("有实现代码")
        if has_tests:
            score += 5
            reasons.append("有测试文件")
        if (p / "README.md").exists() or (p / "README").exists():
            score += 2
            reasons.append("有README")

        return min(20, score), "; ".join(reasons)

    return 10, "无实测数据，无代码文件"


def score_skill(skill_path: str, has_tested: bool = False) -> dict:
    """
    对目标 skill 执行完整8维度评分。

    Args:
        skill_path: skill 目录路径或 SKILL.md 文件路径
        has_tested: 是否已完成实测（由 Claude 在对话中标记）

    Returns:
        {
            "skill": str,
            "total": float,
            "dimensions": [{"name", "label", "score", "max", "reason"}],
            "structure_score": int,
            "effectiveness_score": int,
        }
    """
    body, fm = load_skill_md(skill_path)
    skill_name = fm.get("name", Path(skill_path).name)

    dimensions = []

    # 结构维度（静态分析）
    scores = {
        "frontmatter": score_frontmatter(fm, body),
        "workflow": score_workflow(body),
        "boundary": score_boundary(body),
        "checkpoint": score_checkpoint(body),
        "specificity": score_specificity(body),
        "resources": score_resources(body),
        "architecture": score_architecture(body),
    }

    for name, label, max_score in DIMENSIONS[:-1]:  # 除 effectiveness 外
        s, r = scores[name]
        dimensions.append({
            "name": name, "label": label,
            "score": s, "max": max_score, "reason": r
        })

    structure_score = sum(d["score"] for d in dimensions)

    # 效果维度
    eff_score, eff_reason = score_effectiveness(skill_path, has_tested)
    dimensions.append({
        "name": "effectiveness", "label": "实测表现",
        "score": eff_score, "max": 25, "reason": eff_reason
    })

    total = structure_score + eff_score

    return {
        "skill": skill_name,
        "path": str(skill_path),
        "total": round(total, 1),
        "dimensions": dimensions,
        "structure_score": structure_score,
        "effectiveness_score": eff_score,
    }


def format_score_report(result: dict) -> str:
    """格式化评分报告"""
    lines = [
        f"**【Skill 评分报告】{result['skill']}**",
        f"路径：{result['path']}",
        f"",
        f"**综合评分：{result['total']}/100**",
        f"结构维度：{result['structure_score']}/60 | 效果维度：{result['effectiveness_score']}/25",
        f"",
        "| 维度 | 得分 | 满分 | 评价 |",
        "|------|------|------|------|",
    ]
    for d in result["dimensions"]:
        status = "🟢" if d["score"] / d["max"] >= 0.8 else ("🟡" if d["score"] / d["max"] >= 0.5 else "🔴")
        lines.append(f"| {d['label']} | {d['score']} | {d['max']} | {status} {d['reason']} |")

    # 找最低分维度
    lowest = min(result["dimensions"], key=lambda x: x["score"] / x["max"] if x["max"] > 0 else 999)
    lines.append(f"")
    lines.append(f"**最低分维度：{lowest['label']}** ({lowest['score']}/{lowest['max']})")
    lines.append(f"")
    lines.append(f"建议：优先优化 {lowest['label']} 维度。")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    skill = sys.argv[1] if len(sys.argv) > 1 else "."
    result = score_skill(skill)
    print(format_score_report(result))
