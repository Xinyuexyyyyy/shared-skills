#!/usr/bin/env python3
"""
记忆提醒 hook (memory-nudge)

挂在 Stop 事件。会话结束时做一个纯只读检查:
  这一轮明显产出了东西(改了工作区里的文件),
  但对应工作区的 tasks/INDEX.md 最近没动 ——
  就打印一行提醒，让 agent/用户记得更新任务记忆。

原则:
  - 只提醒，不自动写记忆（沿用"提议-确认才写"模型）。
  - 只读，不改任何文件。出错静默退出，绝不阻断会话。
"""
from __future__ import annotations
import sys, json, time
from pathlib import Path
# 这一轮算"有产出"的最近改动窗口（秒）
RECENT = 1800


def newest_mtime(root: Path) -> float:
    """output/ 下一级条目的最新 mtime。只看顶层目录/文件，不递归——
    避免 rglob 成千上万个产物文件拖慢每次会话结束。"""
    newest = 0.0
    try:
        for p in root.iterdir():
            if p.name.startswith("."):
                continue
            try:
                m = p.stat().st_mtime
                if m > newest:
                    newest = m
            except Exception:
                continue
    except Exception:
        pass
    return newest


def main() -> None:
    try:
        now = time.time()
        payload = json.load(sys.stdin)
        ws = Path(payload.get("cwd") or Path.cwd()).resolve()
        index = ws / ".claude" / "memory" / "tasks" / "INDEX.md"
        out = ws / "output"
        if not index.exists() or not out.exists():
            return
        index_m = index.stat().st_mtime
        prod_m = newest_mtime(out)
        if prod_m > now - RECENT and index_m < prod_m:
            print(f"[记忆提醒] {ws.name} 最近有产出但 tasks/INDEX.md 未更新；"
                  f"收尾时考虑提议更新 INDEX + 对应任务 artifacts.md。")
    except Exception:
        pass  # 任何异常都静默，不阻断会话
    sys.exit(0)


if __name__ == "__main__":
    main()
