#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
output-layer 目录整理器（幂等、可重复跑）

解决的问题：
  output-layer 下每次生成都摊一个 `时间戳-主题/` 文件夹，几十份堆在一起，
  找最新得用眼睛在时间戳里扫。

整理后：
  output-layer/
    README.md                  ← 各主题最新更新时间（说明，不是流水账）
    <主题>/                     ← 打开就是最新那份成品
    _archive/<主题>/<时间戳>/    ← 历史份，要时才翻

幂等：以后再生成新的 `时间戳-主题/`，再跑一次脚本：
  - 当前 <主题>/ 里那份（旧的最新）按它的原始时间戳移进 _archive/
  - 新的扶正成 <主题>/
  - 刷新 README

用法：
  python3 organize.py            # dry-run，只打印计划，不动文件
  python3 organize.py --apply    # 真正执行
  python3 organize.py --dir <路径>   # 指定 output-layer 目录（默认脚本推断）
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from datetime import datetime

# `时间戳-主题` 形如 20260520-192132-010051-openclaw-system-overview
#                    20260520-103231-本科生怎么写专利
TS_PREFIX = re.compile(r"^(\d{8}-\d{6})(?:-\d+)?-(.+)$")
# 已扶正的主题夹里，用这个文件记原始时间戳，保证幂等
STAMP_FILE = ".source_ts"
ARCHIVE_DIR = "_archive"
RESERVED = {ARCHIVE_DIR, "README.md", ".DS_Store"}


def parse_slug(name: str):
    """从 `时间戳-主题` 提取 (时间戳, 主题)。不匹配返回 (None, None)。"""
    m = TS_PREFIX.match(name)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def read_stamp(path: str) -> str | None:
    f = os.path.join(path, STAMP_FILE)
    if os.path.isfile(f):
        with open(f, encoding="utf-8") as fh:
            return fh.read().strip()
    return None


def write_stamp(path: str, ts: str) -> None:
    with open(os.path.join(path, STAMP_FILE), "w", encoding="utf-8") as fh:
        fh.write(ts)


def fmt_ts(ts: str) -> str:
    """20260520-192132 -> 2026-05-20 19:21"""
    try:
        dt = datetime.strptime(ts, "%Y%m%d-%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts


def collect(base: str):
    """
    扫描 base，返回 {主题: [(时间戳, 文件夹名, 是否已扶正)]}，按时间戳降序。
    已扶正的干净主题夹用它的 .source_ts 参与排序。
    """
    groups: dict[str, list[tuple[str, str, bool]]] = {}
    for name in os.listdir(base):
        if name in RESERVED or name.startswith("."):
            continue
        full = os.path.join(base, name)
        if not os.path.isdir(full):
            continue

        ts, slug = parse_slug(name)
        if ts is not None:
            # 带时间戳的原始产物夹
            groups.setdefault(slug, []).append((ts, name, False))
        else:
            # 没时间戳前缀 -> 视为已扶正的干净主题夹
            stamp = read_stamp(full)
            if stamp is None:
                # 没有 stamp 文件，用目录 mtime 兜底
                stamp = datetime.fromtimestamp(os.path.getmtime(full)).strftime(
                    "%Y%m%d-%H%M%S"
                )
            groups.setdefault(name, []).append((stamp, name, True))

    for slug in groups:
        groups[slug].sort(key=lambda x: x[0], reverse=True)
    return groups


def plan(base: str):
    """生成搬动计划。返回 (moves, promotions, summary)。"""
    groups = collect(base)
    moves = []        # (src_abs, dst_abs)  旧份 -> _archive
    promotions = []   # (src_abs, dst_abs, ts)  最新 -> 扶正为干净主题夹
    summary = []      # (主题, 最新时间, 历史份数)

    for slug, items in groups.items():
        newest_ts, newest_name, newest_promoted = items[0]
        clean = os.path.join(base, slug)

        if not newest_promoted:
            # 最新那份还是 `时间戳-主题/`，要扶正为 `主题/`
            promotions.append((os.path.join(base, newest_name), clean, newest_ts))

        # 其余的都归档
        archived = 0
        for ts, name, promoted in items[1:]:
            if promoted:
                # 已存在的干净夹，但有更新的份要扶正 -> 旧干净夹先按其原始时间戳归档
                dst = os.path.join(base, ARCHIVE_DIR, slug, ts)
                moves.append((clean, dst))
            else:
                dst = os.path.join(base, ARCHIVE_DIR, slug, ts)
                moves.append((os.path.join(base, name), dst))
            archived += 1

        summary.append((slug, newest_ts, archived))

    return moves, promotions, summary


def render_readme(base: str, summary) -> str:
    lines = [
        "# output-layer 产物目录",
        "",
        "每个主题一个文件夹，**打开就是最新那份成品**。历史版本在 `_archive/`，要时才翻。",
        "",
        "> 此目录由 `scripts/organize.py` 维护。生成新产物后跑 `python3 organize.py --apply` 即可重新整理。",
        "",
        "## 各主题最新",
        "",
        "| 主题 | 最新更新 | 历史份数 |",
        "| --- | --- | --- |",
    ]
    for slug, ts, archived in sorted(summary, key=lambda x: x[1], reverse=True):
        lines.append(f"| [{slug}](./{slug}/) | {fmt_ts(ts)} | {archived} |")
    lines += [
        "",
        "## 目录结构",
        "",
        "```",
        "output-layer/",
        "  README.md            ← 本文件",
        "  <主题>/              ← 最新成品（output.docx / output.clean.md 等）",
        "  _archive/<主题>/<时间戳>/   ← 历史份",
        "```",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None, help="output-layer 目录路径")
    ap.add_argument("--apply", action="store_true", help="真正执行（默认 dry-run）")
    args = ap.parse_args()

    base = args.dir or os.path.join(
        os.path.expanduser("~"), "Daily Work", "output", "output-layer"
    )
    base = os.path.abspath(base)
    if not os.path.isdir(base):
        print(f"[Error] 目录不存在: {base}")
        sys.exit(1)

    print(f"目标目录: {base}")
    moves, promotions, summary = plan(base)

    if not promotions and not moves:
        print("已经是整理好的状态，无需改动。")
        # 仍然刷新 README
        if args.apply:
            with open(os.path.join(base, "README.md"), "w", encoding="utf-8") as fh:
                fh.write(render_readme(base, summary))
            print("已刷新 README.md")
        return

    print(f"\n=== 计划 ===")
    print(f"扶正为干净主题夹: {len(promotions)} 个")
    for src, dst, ts in promotions:
        print(f"  {os.path.basename(src)}  ->  {os.path.basename(dst)}/   ({fmt_ts(ts)})")
    print(f"\n归档进 _archive/: {len(moves)} 个")
    for src, dst in moves:
        rel = os.path.relpath(dst, base)
        print(f"  {os.path.basename(src)}  ->  {rel}")

    print(f"\n各主题结果:")
    for slug, ts, archived in sorted(summary, key=lambda x: x[1], reverse=True):
        print(f"  {slug}: 最新 {fmt_ts(ts)}，归档 {archived} 份")

    if not args.apply:
        print("\n[dry-run] 以上为计划，未改动任何文件。确认后加 --apply 执行。")
        return

    # 真正执行：先归档（腾空干净主题夹路径），再扶正新份
    for src, dst in moves:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
    for src, dst, ts in promotions:
        os.rename(src, dst)
        write_stamp(dst, ts)

    with open(os.path.join(base, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(render_readme(base, summary))

    print("\n[已执行] 目录整理完成，README.md 已生成。")


if __name__ == "__main__":
    main()
