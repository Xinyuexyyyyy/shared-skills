#!/usr/bin/env python3
"""UserPromptSubmit hook: 把用户最近一句 prompt 存到系统临时目录,供后续 hook 读取判断意图。

guard_overexecute.py / nudge_subagent_dispatch.py 等 hook 需要"用户最近说了什么"
来判断 agent 是否过度执行。这个 hook 只读 stdin、写一个临时文件,不阻断不注入。

遵循 HOOKS-RESPONSIBILITY.md:出错静默 exit 0。
"""
import json
import sys
import tempfile
from pathlib import Path


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        sys.exit(0)

    prompt = data.get("prompt") or ""
    session_id = data.get("session_id") or "unknown"

    if not isinstance(prompt, str) or not prompt.strip():
        sys.exit(0)

    p = Path(tempfile.gettempdir()) / f"last-user-prompt-{session_id}.txt"
    try:
        p.write_text(prompt.strip(), encoding="utf-8")
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
