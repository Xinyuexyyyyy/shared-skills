#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from docx_quality_checker import check_docx_quality, write_quality_reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether Markdown is ready for formal docx output.")
    parser.add_argument("input", help="Markdown source path")
    parser.add_argument("--outdir", default="", help="Directory for docx_quality_report.json/md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.input).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else source.parent
    report = check_docx_quality(source)
    paths = write_quality_reports(report, outdir)
    print(f"status={report['status']}")
    print(f"json={paths['json']}")
    print(f"markdown={paths['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
