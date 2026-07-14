#!/usr/bin/env python3
"""Stop hook: 检测本轮是否做了大事但没派过 sub-agent → 输出提醒(不阻断)。

按输出控制层第 6 节:大事场景应该用两段制(派 sub-agent 起草 + 主 agent 二审)。
本 hook 不能强制 block(避免死循环),只在每轮结束时输出提醒到 stderr,
让 agent 在下次回合看到"上一轮该派 sub-agent 但没派"。

启发式判断:本轮如果改了 SKILL.md / CLAUDE.md / AGENTS.md / settings.json
等关键配置文件,但没用过 Agent 工具(派 sub-agent),就提醒。

遵循 HOOKS-RESPONSIBILITY.md:出错静默 exit 0,绝不阻断会话。
"""
import json
import re
import sys
from pathlib import Path


# 检测"大事"信号:transcript 中出现这些路径的 Edit/Write
BIG_DEAL_PATHS = [
    r"CLAUDE\.md",
    r"AGENTS\.md",
    r"SKILL\.md",
    r"settings\.json",
    r"settings\.local\.json",
    r"hooks\.json",
    r"\.codex/",
    r"shared-skills/",
    r"task_draft/consensus/",
]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    transcript_path = data.get("transcript_path") or ""
    if not transcript_path or not Path(transcript_path).exists():
        sys.exit(0)

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        sys.exit(0)

    # 检测本轮是否触及大事路径(用 Edit/Write/MultiEdit)
    big_deal_hit = False
    for pat in BIG_DEAL_PATHS:
        if re.search(rf'"(Edit|Write|MultiEdit)"[^}}]*{pat}', content):
            big_deal_hit = True
            break

    if not big_deal_hit:
        sys.exit(0)

    # 检测本轮是否派过 sub-agent(用 Agent / Task 工具)
    used_subagent = bool(re.search(r'"name"\s*:\s*"(Agent|Task)"', content))

    # 检测本轮 agent 收尾是否含四段交付格式关键词(结论/怎么验/未完成/下一步)
    # 取 transcript 最后 5000 字符作为收尾消息近似
    tail = content[-5000:] if len(content) > 5000 else content
    has_four_segments = (
        ("结论" in tail or "**结论**" in tail) and
        ("怎么验" in tail or "**怎么验**" in tail) and
        ("未完成" in tail or "**未完成**" in tail) and
        ("下一步" in tail or "**下一步**" in tail)
    )

    reminders = []
    if not used_subagent:
        reminders.append(
            "本轮改了关键配置但没派 sub-agent 起草。按 SKILL.md 第 6 节两段制要求,"
            "大事场景应先派 sub-agent 起草改动方案,主 agent 审核后再落盘。"
        )
    if not has_four_segments:
        reminders.append(
            "本轮大事完成,但收尾没用四段交付格式(结论/怎么验/未完成/下一步)。"
            "按 SKILL.md 第 5 节,大事完成后正式交付必须走四段。"
        )

    if reminders:
        print("[输出控制层提醒] " + " ".join(reminders) + " 下次类似场景请遵守。", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
