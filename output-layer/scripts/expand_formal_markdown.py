#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from formal_expander import expand_formal_markdown, write_expansion_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Expand short or informal Markdown into a formal draft.")
    parser.add_argument("input", help="Markdown source path")
    parser.add_argument("--mode", choices=["off", "conservative", "structured"], default="", help="Override expansion mode")
    parser.add_argument("--outdir", default="", help="Directory for output.expanded.md and formal_expansion_report.*")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.input).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else source.parent
    result = expand_formal_markdown(source, args.mode or None)
    paths = write_expansion_outputs(result, outdir)
    report = result["report"]
    print(f"status={report['status']}")
    print(f"expanded={paths['expanded']}")
    print(f"json={paths['json']}")
    print(f"markdown={paths['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
