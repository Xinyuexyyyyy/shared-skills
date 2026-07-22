#!/usr/bin/env python3
"""Read-only library check used by the v3 manifest."""

from pathlib import Path


REQUIRED = (
    "harnessctl",
    "config/agent.yaml",
    "config/workflow.yaml",
    "config/memory.yaml",
    "config/policy.yaml",
    "config/capabilities.yaml",
    "schemas/turn-envelope.schema.json",
    "tests/test-registry.yaml",
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    missing = [item for item in REQUIRED if not (root / item).is_file()
    ]
    if missing:
        print("缺少 library 文件：" + ", ".join(missing))
        return 1
    print("library smoke 通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
