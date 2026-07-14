#!/usr/bin/env python3
"""
check_map.py — 归位缺口检测(只读,零写入,零风险)

干两件事,治"整理完又乱、地图还自己不知道":
  1. ls 工作区顶层目录 → diff workspace-map.md 登记的项 → 打印"未登记目录"
  2. 用 mtime 断言 map 新鲜度:若有单元目录比 map 还新,报"地图可能过期"
     (废掉 map 里人手写的"最后更新 YYYY-MM-DD",那个已被证明会忘填)

用法: python3 check_map.py [工作区路径]   默认当前目录
退出码恒为 0(它只报告,不拦路)。
"""
import sys
import os
import re
from pathlib import Path

# 不算"单元"的顶层项:点目录、统一资产目录、纯文件
IGNORE = {
    ".git", ".claude", ".DS_Store", "node_modules", "__pycache__",
}


def load_registered(map_path):
    """从 workspace-map.md 抽出所有被登记的名字。
    登记形式: 表格首列的 `name/` 或 `name`(反引号包裹)。"""
    if not map_path.exists():
        return set()
    text = map_path.read_text(encoding="utf-8", errors="ignore")
    names = set()
    # 抓所有 `...` 反引号内容,取第一段路径,去掉尾部 /
    for m in re.findall(r"`([^`]+)`", text):
        first = m.strip().split("/")[0].strip()
        if first:
            names.add(first)
    return names


def main():
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    map_path = ws / ".claude" / "memory" / "workspace-map.md"

    # 1) 磁盘上的真实顶层目录
    on_disk = {p.name for p in ws.iterdir()
               if p.is_dir() and p.name not in IGNORE and not p.name.startswith(".")}
    registered = load_registered(map_path)
    unregistered = sorted(on_disk - registered)

    print(f"=== 归位缺口检测 @ {ws} ===")
    print(f"磁盘顶层目录: {len(on_disk)}  |  地图已登记: {len(registered & on_disk)}")
    print()
    if unregistered:
        print(f"⚠️ 未登记目录 ({len(unregistered)}):  这些在硬盘上但地图不知道")
        for n in unregistered:
            print(f"   - {n}/")
    else:
        print("✅ 所有顶层目录都已登记")
    print()

    # 2) mtime 断言新鲜度(废掉人手写的"最后更新"日期)
    if map_path.exists():
        map_mtime = map_path.stat().st_mtime
        newer = []
        for p in ws.iterdir():
            if p.is_dir() and p.name not in IGNORE and not p.name.startswith("."):
                if p.stat().st_mtime > map_mtime:
                    newer.append(p.name)
        if newer:
            print(f"⚠️ 地图可能过期: {len(newer)} 个目录比 map 更新(map 最后改于 "
                  f"{__import__('datetime').datetime.fromtimestamp(map_mtime):%Y-%m-%d})")
            for n in sorted(newer)[:10]:
                print(f"   - {n}/ 更新更晚")
        else:
            print("✅ 地图比所有目录都新,新鲜")
    else:
        print("❌ 找不到 workspace-map.md")


if __name__ == "__main__":
    main()
