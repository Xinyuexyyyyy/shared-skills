#!/usr/bin/env python3
"""Codex SessionStart hook: 每次会话开始时,把输出控制层 SKILL.md 注入为 system reminder。

与 Claude Code 版的唯一差别: hookEventName 从 UserPromptSubmit 改成 SessionStart。
Codex 调用时机: 会话开始(startup/resume/clear),一次注入,持久在 context。

模型在新会话开始时就能看到二审逻辑,不靠自觉记忆。
遵循 HOOKS-RESPONSIBILITY.md:出错静默 exit 0,绝不阻断会话。
"""
import json
import sys
from pathlib import Path

SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "output-control-layer" / "SKILL.md"


def main():
    try:
        sys.stdin.read()  # 读完 stdin,避免 broken pipe
    except Exception:
        pass

    try:
        content = SKILL_PATH.read_text(encoding="utf-8")
    except Exception:
        sys.exit(0)  # 读不到 skill 就放行,不阻断

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",  # ← 与 Claude Code 版唯一差别
            "additionalContext": content,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
