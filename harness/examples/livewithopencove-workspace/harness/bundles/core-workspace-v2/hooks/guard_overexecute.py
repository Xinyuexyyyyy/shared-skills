#!/usr/bin/env python3
"""PreToolUse hook: 用户最后一句是问号且想改文件 → 拦截。

防过度执行的硬约束:用户问"能不能/怎么/为什么",但 agent 想 Write/Edit
文件,大概率是过度路由。先拦下,让 agent 直接答问题,而不是擅自落盘。

豁免:用户消息含"写入/保存/落盘/生成/创建/修改/改一下"等明确执行词,放行。

遵循 HOOKS-RESPONSIBILITY.md:出错静默 exit 0。
"""
import json
import re
import sys
import tempfile
from pathlib import Path

# 用户消息含这些词 = 明确要执行,放行(不拦)
EXEC_KEYWORDS = [
    "写入", "保存", "落盘", "落地", "生成", "创建", "新建",
    "修改", "改一下", "改下", "改进", "更新", "覆盖",
    "删除", "删掉", "清理", "整理",
    "实现", "做出来", "做一下", "干一下", "搞一下",
    "做好", "做完", "完成", "搞定", "弄好",
    "告诉我", "给我", "发我", "拿给我",
    "执行", "运行", "跑一下", "试一下", "开始",
    "继续", "接着做", "下一步",
    "写", "改", "存", "建",  # 单字执行词(短消息常见)
]

# 问句标志:消息以这些结尾 = 用户在问问题
QUESTION_ENDINGS = ["?", "?", "吗", "呢", "么"]

# 问句关键词:消息含这些 = 用户在问判断/方法
QUESTION_KEYWORDS = [
    "可以吗", "能吗", "行吗", "好吗",
    "怎么样", "如何", "怎么", "为什么", "什么",
    "是不是", "对不对", "对吗",
    "能不能", "可不可以", "要不要", "用不用",
    "有没有", "缺不缺", "装不装",
    "哪个", "哪种", "哪里",
]


def looks_like_question(prompt: str) -> bool:
    """启发式判断:用户消息更像问问题还是要执行。"""
    if not prompt:
        return False
    prompt = prompt.strip()
    # 短消息(< 50 字)末尾是问号 → 很可能问句
    if len(prompt) < 200:
        for end in QUESTION_ENDINGS:
            if prompt.endswith(end):
                return True
    # 含问句关键词
    for kw in QUESTION_KEYWORDS:
        if kw in prompt:
            return True
    return False


def has_exec_intent(prompt: str) -> bool:
    """用户消息是否含明确执行意图(放行信号)。"""
    if not prompt:
        return False
    for kw in EXEC_KEYWORDS:
        if kw in prompt:
            return True
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = data.get("tool_name", "")
    if tool not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    session_id = data.get("session_id") or "unknown"
    prompt_path = Path(tempfile.gettempdir()) / f"last-user-prompt-{session_id}.txt"

    try:
        prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
    except Exception:
        sys.exit(0)

    if not prompt:
        sys.exit(0)

    # 用户明确要执行 → 放行
    if has_exec_intent(prompt):
        sys.exit(0)

    # 不是问句 → 放行(可能是叙述、报告等)
    if not looks_like_question(prompt):
        sys.exit(0)

    # 问句 + 没有执行意图 + 想改文件 → 拦
    tin = data.get("tool_input", {}) or {}
    fpath = tin.get("file_path") or tin.get("path") or "(未知路径)"

    reason = (
        f"⚠️ 过度执行拦截:用户最近一句是问句(\"{prompt[:60]}...\"),"
        f"但你想 {tool} 文件 `{fpath}`。"
        f"按输出控制层二审规则:用户问判断/方法时,先直接回答问题,不擅自落盘。"
        f"如果用户确实要你执行,请先在对话里说明\"如果你确认,我可以把这条写入...\","
        f"等用户明确说\"写入/保存/落盘/生成\"等词后再调用 {tool}。"
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
