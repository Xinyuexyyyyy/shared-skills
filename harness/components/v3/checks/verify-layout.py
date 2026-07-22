#!/usr/bin/env python3
"""Self-contained v3 bundle layout check; it stores no runtime state."""

from pathlib import Path


REQUIRED = (
    "manifest.yaml", "config/agent.yaml", "config/workflow.yaml",
    "config/memory.yaml", "config/policy.yaml", "config/capabilities.yaml",
    "runtime/common/HARNESS.md.tmpl", "runtime/codex/AGENTS.md.tmpl",
    "runtime/claude/CLAUDE.md.tmpl", "schemas/turn-envelope.schema.json",
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    missing = [item for item in REQUIRED if not (root / item).is_file()]
    if missing:
        print("缺少 bundle 布局文件：" + ", ".join(missing))
        return 1
    print("bundle 布局检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
