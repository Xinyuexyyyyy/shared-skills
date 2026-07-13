#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from formal_revision_planner import revise_formal_markdown, write_revision_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a deterministic revised Markdown draft from quality reports.")
    parser.add_argument("input", help="Markdown source path")
    parser.add_argument("--outdir", default="", help="Directory for output.revised.md and formal_revision_report.*")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.input).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else source.parent
    result = revise_formal_markdown(source)
    paths = write_revision_outputs(result, outdir)
    report = result["report"]
    print(f"status={report['status']}")
    print(f"revised={paths['revised']}")
    print(f"json={paths['json']}")
    print(f"markdown={paths['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
