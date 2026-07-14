#!/usr/bin/env python3
"""
memory_gc.py — timeline 机器裁剪(把 #1 的"30条上限"变成不靠自觉的硬执行)

干的事:把 timeline.md 截断到最近 N 条(默认30),溢出的旧条目 append 进
timeline-archive.md。纯机械、可回滚:每次跑前先把 timeline.md 备份到
.claude/memory/.gc-backup/。无需用户确认(纯整理,不改语义)。

"条目"的识别:timeline.md 支持两种格式混排,两者都算一条:
  - 一行制:以 "- 20XX-" 开头(当前主格式)
  - 五段块:以 "## " 开头(旧格式)
从第一个条目标记开始,直到下一个标记或文件结束。文件头部
(# Timeline 标题 + 引言 + 第一个 ---)原样保留。
混排时按文件顺序切条(timeline 本就按时间倒序维护,文件位置≈时间序)。

用法:
  python3 memory_gc.py [--keep N] [--dry-run] [工作区路径]
  --dry-run 只报告会裁掉几条,不写任何文件。
退出码恒为 0。
"""
import sys
import re
from pathlib import Path
from datetime import datetime

# 条目开头:行首是 "## " 或 "- 20XX-"(一行制带年份,不会误匹配五段块内的 "- **字段**")
ENTRY_RE = re.compile(r"(?m)^(?:## |- 20\d\d-)")


def parse_args(argv):
    keep, dry, ws = 30, False, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--keep":
            keep = int(argv[i + 1]); i += 2
        elif a == "--dry-run":
            dry = True; i += 1
        else:
            ws = Path(a); i += 1
    return keep, dry, (ws or Path.cwd())


def split_entries(body):
    """把正文按条目标记切成列表(保持顺序,倒序文件=最新在前)。
    标记 = 行首 '## ' 或 '- 20XX-'(两种格式混排都能切)。"""
    parts = re.split(r"(?m)^(?=## |- 20\d\d-)", body)
    return [p for p in parts if p.strip()]


def main():
    keep, dry, ws = parse_args(sys.argv[1:])
    mem = ws / ".claude" / "memory"
    tl = mem / "timeline.md"
    arch = mem / "timeline-archive.md"
    if not tl.exists():
        print(f"❌ 找不到 {tl}"); return

    text = tl.read_text(encoding="utf-8", errors="ignore")
    # 分离文件头(第一个条目标记之前:标题+引言+第一个 ---)
    m = ENTRY_RE.search(text)
    if not m:
        print("✅ timeline 里没有条目,无需裁剪"); return
    header, body = text[:m.start()], text[m.start():]
    entries = split_entries(body)
    total = len(entries)

    if total <= keep:
        print(f"✅ timeline 共 {total} 条,未超 {keep},无需裁剪"); return

    keep_entries = entries[:keep]      # 最新的 N 条(倒序文件,顶部最新)
    overflow = entries[keep:]          # 溢出的旧条目
    print(f"timeline 共 {total} 条 → 保留最新 {keep},归档 {len(overflow)} 条")

    if dry:
        print("(--dry-run,不写任何文件)")
        print(f"  将归档最旧条目示例: {overflow[-1].splitlines()[0][:50]}")
        return

    # 备份(可回滚)
    bdir = mem / ".gc-backup"
    bdir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (bdir / f"timeline.md.{stamp}").write_text(text, encoding="utf-8")
    print(f"  已备份 → .gc-backup/timeline.md.{stamp}")

    # 写归档(溢出条目 append 到 archive 顶部之后)
    arch_text = arch.read_text(encoding="utf-8", errors="ignore") if arch.exists() else "# Timeline Archive\n\n> 从 timeline.md 自动归档的旧条目。\n\n---\n\n"
    am = ENTRY_RE.search(arch_text)
    a_header = arch_text[:am.start()] if am else arch_text
    a_body = arch_text[am.start():] if am else ""
    arch.write_text(a_header + "".join(overflow) + a_body, encoding="utf-8")
    print(f"  已归档 {len(overflow)} 条 → timeline-archive.md")

    # 写回裁剪后的 timeline
    tl.write_text(header + "".join(keep_entries), encoding="utf-8")
    new_size = len(tl.read_text(encoding='utf-8'))
    print(f"  ✅ timeline.md 裁剪完成,{len(text)//1024}KB → {new_size//1024}KB")


if __name__ == "__main__":
    main()
