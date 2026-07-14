#!/usr/bin/env python3
"""
lessons_gc.py — lessons.md 经验库的体检 + 退役归档(对标 memory_gc.py)

干的事(默认只读 dry-run,不改文件):
  1. 去重检测:scope 重叠 + 标题高相似 的条目,报"疑似重复,建议合并"。
  2. 矛盾检测:同 scope 下出现相反建议(X 用问句 / X 别用问句),报冲突待人裁。
  3. 退役建议:harmful>helpful,或 applied=0 且 last 超过 N 天(默认90)的条目,
     建议移入 lessons-archive.md。
只有加 --apply 才真正归档退役条目(只移不删,先备份到 .gc-backup,可回滚)。
去重和矛盾永远只报告不动手——合并/裁决是语义判断,留给人。

条目识别:lessons.md 里以 "## " 开头 = 一条经验的开始。
meta 行(可选):紧跟标题的 HTML 注释
  <!-- meta: id=L015 | scope=output-layer,远端部署 | applied=0 | helpful=0 | harmful=0 | last=2026-06-10 -->

用法:
  python3 lessons_gc.py [--stale-days N] [--apply] [工作区路径]
  不加 --apply = dry-run(只报告)。退出码恒为 0。
"""
import sys
import re
from pathlib import Path
from datetime import datetime


def parse_args(argv):
    stale, apply, ws = 90, False, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--stale-days":
            stale = int(argv[i + 1]); i += 2
        elif a == "--apply":
            apply = True; i += 1
        elif a == "--dry-run":
            i += 1  # 兼容:dry-run 是默认行为
        else:
            ws = Path(a); i += 1
    return stale, apply, (ws or Path.cwd())


def strip_template_comments(body):
    """剥离 HTML 注释块,但保留 meta 行(<!-- meta: ... --> 要被 parse_meta 读)。
    防止 lessons.md 模板里 `<!-- 模板: ## YYYY-MM-DD ... -->` 的示例标题被误算成真条目。"""
    return re.sub(
        r"<!--(?!\s*meta:).*?-->", "", body, flags=re.DOTALL)


def split_entries(body):
    """按 '## ' 切成条目列表(顺序保留,倒序文件=最新在前)。
    只保留真正以 '## ' 开头的块——丢掉第一个条目之前的文件头(标题+说明)。"""
    body = strip_template_comments(body)
    parts = re.split(r"(?m)^(?=## )", body)
    return [p for p in parts if p.lstrip().startswith("## ")]


def parse_meta(entry):
    """从条目里抽 meta 注释,返回 dict;没有则返回默认值。"""
    m = re.search(r"<!--\s*meta:\s*(.*?)\s*-->", entry)
    meta = {"id": "", "scope": [], "applied": 0, "helpful": 0,
            "harmful": 0, "last": ""}
    if not m:
        return meta
    for field in m.group(1).split("|"):
        if "=" not in field:
            continue
        k, v = field.split("=", 1)
        k, v = k.strip(), v.strip()
        if k == "scope":
            meta["scope"] = [s.strip() for s in v.split(",") if s.strip()]
        elif k in ("applied", "helpful", "harmful"):
            try:
                meta[k] = int(v)
            except ValueError:
                meta[k] = 0
        elif k in ("id", "last"):
            meta[k] = v
    return meta


def title_of(entry):
    """取标题行(去掉 '## ' 和日期前缀,用于相似度比较)。"""
    line = entry.lstrip().splitlines()[0]
    line = re.sub(r"^##\s*", "", line)
    line = re.sub(r"^\d{4}-\d{2}-\d{2}\s*[:：]\s*", "", line)
    return line.strip()


def token_set(s):
    """粗分词:中文按字、英文按词,转小写集合。够文本匹配用,不上 embedding。"""
    s = s.lower()
    en = re.findall(r"[a-z0-9]+", s)
    zh = re.findall(r"[一-鿿]", s)
    return set(en) | set(zh)


def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def days_since(date_str):
    """last 距今天数;无法解析返回 None。"""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return (datetime.now() - d).days
    except (ValueError, TypeError):
        return None


# 矛盾检测:同一动作的正/反措辞。粗启发式,只为提醒人去看,不做裁决。
_NEG = re.compile(r"不要|别|不用|避免|禁止|勿|不应|不能")


def detect_dups(items, threshold=0.3):
    """两两比 scope 重叠 + 标题相似;超阈值报疑似重复。
    阈值偏低(0.3):去重只报告不删,宁可多提醒人瞄一眼,不漏。
    中英混排逐字分词会拉低 jaccard,所以这里不取高阈。"""
    hits = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            scope_overlap = set(a["meta"]["scope"]) & set(b["meta"]["scope"])
            if not scope_overlap:
                continue
            sim = jaccard(a["tokens"], b["tokens"])
            if sim >= threshold:
                hits.append((a, b, scope_overlap, sim))
    return hits


def detect_conflicts(items):
    """同 scope 下,标题 token 高度重叠但一正一反措辞 -> 疑似矛盾。"""
    hits = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            if not (set(a["meta"]["scope"]) & set(b["meta"]["scope"])):
                continue
            # 标题主题接近
            if jaccard(a["tokens"], b["tokens"]) < 0.4:
                continue
            neg_a = bool(_NEG.search(a["title"]))
            neg_b = bool(_NEG.search(b["title"]))
            if neg_a != neg_b:
                hits.append((a, b))
    return hits


def detect_retire(items, stale_days):
    """退役候选:harmful>helpful,或 applied=0 且 last 超 stale_days。"""
    out = []
    for it in items:
        m = it["meta"]
        reason = None
        if m["harmful"] > m["helpful"] and m["harmful"] > 0:
            reason = f"harmful({m['harmful']})>helpful({m['helpful']})"
        else:
            ds = days_since(m["last"])
            if m["applied"] == 0 and ds is not None and ds > stale_days:
                reason = f"applied=0 且 {ds} 天未用(>{stale_days})"
        if reason:
            out.append((it, reason))
    return out


def main():
    stale, apply, ws = parse_args(sys.argv[1:])
    mem = ws / ".claude" / "memory"
    lf = mem / "lessons.md"
    arch = mem / "lessons-archive.md"
    if not lf.exists():
        print(f"❌ 找不到 {lf}"); return

    text = lf.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"(?m)^## ", text)
    if not m:
        print("✅ lessons.md 里没有 '## ' 条目,无需体检"); return
    header, body = text[:m.start()], text[m.start():]
    raw = split_entries(body)

    items = []
    for e in raw:
        title = title_of(e)
        items.append({
            "raw": e, "title": title, "meta": parse_meta(e),
            "tokens": token_set(title),
        })
    print(f"lessons.md 共 {len(items)} 条经验。")

    dups = detect_dups(items)
    conflicts = detect_conflicts(items)
    retire = detect_retire(items, stale)

    if dups:
        print(f"\n⚠️  疑似重复 {len(dups)} 组(建议人工合并,脚本不动):")
        for a, b, sc, sim in dups:
            print(f"  · [{','.join(sc)}] 相似度{sim:.0%}")
            print(f"      A: {a['title'][:40]}")
            print(f"      B: {b['title'][:40]}")
    if conflicts:
        print(f"\n⚠️  疑似矛盾 {len(conflicts)} 组(同 scope 一正一反,待人裁):")
        for a, b in conflicts:
            print(f"      A: {a['title'][:40]}")
            print(f"      B: {b['title'][:40]}")
    if retire:
        print(f"\n🗄  建议退役 {len(retire)} 条 → lessons-archive.md:")
        for it, reason in retire:
            print(f"  · {it['title'][:40]}  ({reason})")
    if not (dups or conflicts or retire):
        print("✅ 无重复/矛盾/退役建议,经验库健康。")

    if not apply:
        if retire:
            print("\n(dry-run。加 --apply 仅归档上面的退役条目;重复/矛盾永远只报告。)")
        return

    if not retire:
        print("\n无退役条目,不动文件。")
        return

    # 备份(可回滚)
    bdir = mem / ".gc-backup"
    bdir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (bdir / f"lessons.md.{stamp}").write_text(text, encoding="utf-8")
    print(f"\n  已备份 → .gc-backup/lessons.md.{stamp}")

    retire_raws = {id(it["raw"]) for it, _ in retire}
    kept = [it["raw"] for it in items if id(it["raw"]) not in retire_raws]
    moved = [it["raw"] for it in items if id(it["raw"]) in retire_raws]

    # 归档(append 到 archive header 之后)
    default_arch = ("# Lessons Archive\n\n> 从 lessons.md 自动退役的旧经验"
                    "(harmful>helpful 或长期未用)。需要时可回捞。\n\n---\n\n")
    arch_text = arch.read_text(encoding="utf-8", errors="ignore") if arch.exists() else default_arch
    am = re.search(r"(?m)^## ", arch_text)
    a_header = arch_text[:am.start()] if am else arch_text
    a_body = arch_text[am.start():] if am else ""
    arch.write_text(a_header + "".join(moved) + a_body, encoding="utf-8")

    lf.write_text(header + "".join(kept), encoding="utf-8")
    print(f"  ✅ 已退役 {len(moved)} 条 → lessons-archive.md,lessons.md 余 {len(kept)} 条。")


if __name__ == "__main__":
    main()
