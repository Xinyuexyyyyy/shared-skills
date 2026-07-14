#!/usr/bin/env python3
"""UserPromptSubmit hook: 每次用户发消息时,把输出控制层 SKILL.md 注入为 system reminder。

模型在每轮推理前都能看到二审逻辑,不靠自觉记忆。
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
            "hookEventName": "UserPromptSubmit",
            "additionalContext": content,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
