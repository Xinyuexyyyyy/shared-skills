"""
daily_review.py — 每日 skill 执行汇聚分析

触发：每日 10:00 CST（cron）

流程：
1. 读取昨日 execution logs
2. 按 skill 分组统计
3. 计算执行分 trend
4. 生成报告 + 推送飞书
"""
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── 清除代理 ────────────────────────────────────────────
for _k in list(os.environ.keys()):
    if "proxy" in _k.lower() or _k.upper() in (
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"
    ):
        del os.environ[_k]

BASE_DIR = Path.home() / ".openclaw" / "skill-optimizer" / "logs"
EXEC_DIR = BASE_DIR / "executions"
REVIEW_DIR = BASE_DIR / "daily_reviews"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)


def _date(days_offset=0):
    return (datetime.now(timezone.utc) - timedelta(days=days_offset)).strftime("%Y-%m-%d")


def _exec_file(date):
    return EXEC_DIR / f"{date}.jsonl"


def _review_file(date):
    return REVIEW_DIR / f"{date}.md"


# ── 读取日志 ────────────────────────────────────────────

def read_day(date):
    f = _exec_file(date)
    if not f.exists():
        return []
    records = []
    with open(f, encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ── 统计分析 ────────────────────────────────────────────

def stats_by_skill(records):
    """按 skill 分组统计"""
    by_skill = {}
    for r in records:
        s = r.get("skill", "unknown")
        if s not in by_skill:
            by_skill[s] = {
                "executions": 0,
                "ok": 0,
                "error": 0,
                "partial": 0,
                "total_duration_ms": 0,
                "total_tokens": 0,
                "problems": [],        # 有 problem 字段的记录
                "optimize_tags": [],   # 被标记 optimize 的
            }
        by_skill[s]["executions"] += 1
        by_skill[s]["total_duration_ms"] += r.get("duration_ms", 0) or 0
        by_skill[s]["total_tokens"] += r.get("tokens_used", 0) or 0
        result = r.get("result", "ok")
        if result == "ok":
            by_skill[s]["ok"] += 1
        elif result == "error":
            by_skill[s]["error"] += 1
        else:
            by_skill[s]["partial"] += 1
        if r.get("problem"):
            by_skill[s]["problems"].append(r)
        if r.get("optimize"):
            by_skill[s]["optimize_tags"].append(r)

    return by_skill


def effectiveness_score(stats) -> tuple[float, str]:
    """
    计算 effectiveness 评分（基于真实执行数据）

    Returns: (score, detail)
    """
    total = stats["executions"]
    if total == 0:
        return 0, "无执行记录"

    ok_rate = stats["ok"] / total

    # 成功率（0-25分）
    success_score = round(ok_rate * 25, 1)

    # 问题解决率（0-15分）
    problems = stats["problems"]
    solutions = [p for p in problems if p.get("solution")]
    root_causes = [p for p in problems if p.get("root_cause")]
    avoid_count = [p for p in problems if p.get("avoid")]

    if problems:
        problem_score = min(15, len(solutions) / len(problems) * 10 + len(root_causes) / len(problems) * 3 + len(avoid_count) / len(problems) * 2)
    else:
        problem_score = 15  # 无问题满分

    # 优化采纳（0-10分）
    optimize_tagged = len(stats["optimize_tags"])
    optimize_score = min(10, optimize_tagged * 3)  # 每个标记3分

    total_score = success_score + problem_score + optimize_score

    detail = (
        f"成功率{ok_rate*100:.0f}%({stats['ok']}/{total})→{success_score}分，"
        f"问题解决{len(solutions)}/{len(problems)}→{problem_score:.1f}分，"
        f"优化标记{optimize_tagged}→{optimize_score}分"
    )

    return round(total_score, 1), detail


# ── trend 计算 ────────────────────────────────────────────

def compute_trend(skill, days=7):
    """
    计算 skill 的 effectiveness trend（最近N天 vs 之前N天）
    Returns: (trend_str, old_score, new_score)
    """
    recent = []
    older = []

    for i in range(days * 2):
        date = _date(i)
        records = [r for r in read_day(date) if r.get("skill") == skill]
        if i < days:
            recent.extend(records)
        else:
            older.extend(records)

    if not older:
        return "📊 首次记录", 0, 0

    old_stats = stats_by_skill(older).get(skill, {"executions": 0, "ok": 0, "problems": [], "optimize_tags": []})
    new_stats = stats_by_skill(recent).get(skill, {"executions": 0, "ok": 0, "problems": [], "optimize_tags": []})

    old_eff, _ = effectiveness_score(old_stats)
    new_eff, _ = effectiveness_score(new_stats)

    delta = new_eff - old_eff
    if delta > 5:
        trend = f"📈 +{delta:.1f}"
    elif delta < -5:
        trend = f"📉 {delta:.1f}"
    else:
        trend = f"➡️ {delta:+.1f}"

    return trend, old_eff, new_eff


# ── 生成报告 ────────────────────────────────────────────

def build_report(date=None):
    if not date:
        date = _date(1)  # 昨天

    records = read_day(date)
    by_skill = stats_by_skill(records)

    # 全局统计
    total_exec = len(records)
    total_ok = sum(s["ok"] for s in by_skill.values())
    total_error = sum(s["error"] for s in by_skill.values())
    total_partial = sum(s["partial"] for s in by_skill.values())
    ok_rate = f"{total_ok/total_exec*100:.0f}%" if total_exec else "N/A"

    # 收集问题
    all_problems = []
    for sname, sdata in by_skill.items():
        all_problems.extend([(sname, p) for p in sdata["problems"]])

    # 构建报告
    lines = [
        f"# 🤖 skill-optimizer 日报 · {date}",
        "",
        f"## 📊 执行概览",
        f"- 总执行：{total_exec} 次 | 成功率：{ok_rate} | 涉及 skills：{len(by_skill)}",
        f"- ✅ 成功：{total_ok} | ❌ 失败：{total_error} | ⚠️ 部分：{total_partial}",
        "",
    ]

    # 按执行数排序
    sorted_skills = sorted(by_skill.items(), key=lambda x: x[1]["executions"], reverse=True)

    # 问题警告
    if all_problems:
        lines.append("## ⚠️ 问题记录")
        for sname, p in all_problems[:5]:  # 最多5条
            result_emoji = "❌" if p.get("result") == "error" else "⚠️"
            lines.append(f"- {result_emoji} **{sname}/{p.get('action')}**：{p.get('problem') or '无描述'}")
            if p.get("solution"):
                lines.append(f"  → 解决：{p.get('solution')}")
        lines.append("")

    # 各 skill 详情
    lines.append("## 📈 各 Skill 详情")
    lines.append("| Skill | 执行 | 成功 | 失败 | effectiveness | trend | 均耗时 |")
    lines.append("|-------|------|------|------|--------------|------|--------|")

    for sname, sdata in sorted_skills:
        eff, _ = effectiveness_score(sdata)
        trend, _, _ = compute_trend(sname)
        avg_ms = sdata["total_duration_ms"] / sdata["executions"] if sdata["executions"] else 0
        ok_s = sdata["ok"]
        err_s = sdata["error"]
        lines.append(
            f"| {sname} | {sdata['executions']} | {ok_s} | {err_s} | {eff:.1f} | {trend} | {avg_ms:.0f}ms |"
        )

    # effectiveness 趋势预警
    lines.append("")
    lines.append("## 🎯 Effectiveness Trend")
    for sname, sdata in sorted_skills:
        trend, old_eff, new_eff = compute_trend(sname)
        eff, _ = effectiveness_score(sdata)
        if "📉" in trend:
            lines.append(f"- ⚠️ **{sname}**：{old_eff:.1f} → {new_eff:.1f}（{trend}），需关注")

    # 优化建议（基于 optimize 标签）
    optimize_items = []
    for sname, sdata in by_skill.items():
        for p in sdata["optimize_tags"]:
            optimize_items.append((sname, p.get("optimize", "")))
    if optimize_items:
        lines.append("")
        lines.append("## 💡 优化建议")
        for sname, suggestion in optimize_items[:3]:
            lines.append(f"- [{sname}]：{suggestion}")

    lines.append("")
    lines.append(f"---\n*由 skill-optimizer daily_review 自动生成 · {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}*")

    return "\n".join(lines)


# ── 主流程 ────────────────────────────────────────────

def run(date=None, push_feishu=True):
    """
    执行每日汇聚。
    """
    if not date:
        date = _date(1)  # 昨天

    print(f"[daily_review] 生成 {date} 日报...")

    report = build_report(date)

    # 保存报告
    rf = _review_file(date)
    rf.write_text(report, encoding="utf-8")
    print(f"[daily_review] 报告已保存: {rf}")

    # 推送飞书
    if push_feishu:
        try:
            _push_feishu(report)
            print("[daily_review] 飞书推送成功")
        except Exception as e:
            print(f"[daily_review] 飞书推送失败: {e}")

    return report


def _push_feishu(text: str):
    """推送飞书"""
    token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "300ae7b9b678095670a36147d3b9ba4f23ea54aea88b91e2")

    # 飞书消息限制 4000 字，切割
    if len(text) > 4000:
        # 按行切割
        lines = text.splitlines()
        chunks = []
        current = []
        current_len = 0
        for line in lines:
            if current_len + len(line) > 3800:
                chunks.append("\n".join(current))
                current = []
                current_len = 0
            current.append(line)
            current_len += len(line)
        if current:
            chunks.append("\n".join(current))
    else:
        chunks = [text]

    import subprocess
    for chunk in chunks:
        r = subprocess.run(
            [
                "openclaw", "message", "send",
                "--channel", "feishu",
                "--account", "default",
                "--target", "user:ou_0db0b6836fca4943b7e6d87867c69c7f",
                "--message", chunk,
            ],
            capture_output=True, text=True,
            timeout=30,
            env={**os.environ, "OPENCLAW_GATEWAY_TOKEN": token}
        )
        if r.returncode != 0:
            print(f"[push] failed: {r.stderr[:200]}")


if __name__ == "__main__":
    import sys
    date = sys.argv[1] if len(sys.argv) > 1 else None
    push = "--no-push" not in sys.argv
    report = run(date=date, push_feishu=push)
    print(report)
