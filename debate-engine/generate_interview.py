#!/usr/bin/env python3
"""
content-pipeline Phase 1: 自动生成虚构访谈稿
从种子表随机抽取一组，调用 LLM 生成完整的结构化访谈稿。
"""
import os
import sys
import json
import random
import time
import requests
from pathlib import Path
from datetime import datetime

ENV_PATH = Path(os.path.expanduser("~/Daily Work/.env"))

PERSONAS = [
    ("P01", "大厂程序员转独立开发", "25-35", "互联网公司3-5年，受够了，想自己做产品"),
    ("P02", "小城青年不愿回老家", "22-28", "二本毕业，大城市漂着，家里催回去"),
    ("P03", "35+被优化后重新出发", "33-40", "中层管理，突然被裁，identity崩塌"),
    ("P04", "文科生自学编程", "20-30", "非计算机背景，靠AI工具入门，撞墙多次"),
    ("P05", "全职妈妈想重返职场", "28-38", "带了3年孩子，怕脱节，怕不被需要"),
    ("P06", "在读研究生对学术失望", "23-27", "读研才发现不喜欢学术，但沉没成本太大"),
    ("P07", "体制内想跳出来", "26-35", "公务员/国企，稳定但窒息，不敢走"),
    ("P08", "自由职业者焦虑没安全感", "25-35", "收入不稳定，自由但孤独，羡慕又不甘"),
    ("P09", "情侣异地分手后重建生活", "24-32", "感情断裂后发现自己不知道怎么独处"),
    ("P10", "普通打工人发现了一个热爱", "22-35", "工作无感，但业余时间找到了一件发光的事"),
]

THEMES = [
    ("T01", "辞职/转型的决定性瞬间", "什么让你终于迈出那一步？"),
    ("T02", "用AI工具从零建了一个东西", "你怎么从完全不会到跑通了？"),
    ("T03", "一段关系的结束与重建", "结束时你最怕什么？后来怎么过来的？"),
    ("T04", "从应该做到想做的转变", "你什么时候发现自己一直在活别人的剧本？"),
    ("T05", "一次失败后的复盘", "失败当时你怎么想的？现在呢？"),
    ("T06", "搬到一个新城市/新环境", "什么让你离开？什么让你留下？"),
    ("T07", "发现自己擅长一件事的瞬间", "你怎么知道这件事我行的？"),
    ("T08", "跟父母/家人的一次关键对话", "他们理解吗？不理解的时候你怎么办？"),
    ("T09", "独处/孤独/一个人的时刻", "你什么时候学会跟自己待在一起的？"),
    ("T10", "第一次赚到属于自己的钱", "不是工资，是你自己创造的价值兑现"),
]

ARCS = [
    ("A01", "窒息→逃离→重建", "旧系统压迫→决定离开→新秩序建立"),
    ("A02", "迷茫→撞墙→顿悟", "不知道要什么→尝试失败→突然明白"),
    ("A03", "自信→崩塌→清醒", "以为自己行→现实打脸→放下重来"),
    ("A04", "逃避→直面→接纳", "一直回避的事→被迫面对→跟它和解"),
    ("A05", "平淡→发现→点燃", "日子没波澜→偶然发现一件事→生活变了"),
]


def load_env():
    config = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                config[key.strip()] = val.strip()
    return config


def call_kimi(config, messages, temperature=0.8):
    base = config["KIMI_BASE_URL"].rstrip("/")
    url = f"{base}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config['KIMI_API_KEY']}",
        "Content-Type": "application/json",
        "User-Agent": "claude-code/1.0",
    }
    payload = {
        "model": config["KIMI_MODEL"],
        "messages": messages,
        "temperature": temperature,
    }
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=300)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
            else:
                raise


def pick_seed(persona_id=None, theme_id=None, arc_id=None):
    p = next((x for x in PERSONAS if x[0] == persona_id), None) if persona_id else random.choice(PERSONAS)
    t = next((x for x in THEMES if x[0] == theme_id), None) if theme_id else random.choice(THEMES)
    a = next((x for x in ARCS if x[0] == arc_id), None) if arc_id else random.choice(ARCS)
    return p, t, a


def generate(persona_id=None, theme_id=None, arc_id=None):
    config = load_env()
    p, t, a = pick_seed(persona_id, theme_id, arc_id)
    print(f"种子: {p[0]} x {t[0]} x {a[0]}")
    print(f"人设: {p[1]}（{p[2]}岁，{p[3]}）")
    print(f"主题: {t[1]}（{t[2]}）")
    print(f"情绪弧: {a[1]}（{a[2]}）")
    print()

    prompt = f"""请你同时扮演记者和受访者，完成一次完整的9轮访谈。

受访者人设：{p[1]}，{p[2]}岁，背景：{p[3]}
故事主题：{t[1]}——{t[2]}
情绪弧线：{a[1]}（{a[2]}）

要求：
- 受访者的回答必须包含具体场景、具体数字、具体对话
- 不要泛泛而谈，每一轮都要有新的细节浮现
- 允许有犹豫、自相矛盾、说不清楚的地方（真实感）
- 最后产出标准的结构化访谈稿，格式如下：

# 访谈稿：[标题]

## 一、故事线总览
用3-5句话概括完整故事线。

## 二、素材卡片
每个关键场景一张卡片，含：场景、引语、意义。

## 三、金句清单
可直接用于文章的原话。

## 四、关键细节清单
数字、对话、物品、动作、地点、人物。

## 五、情感转折点
按时间顺序列出情绪变化节点。

## 六、未展开的线索
可追问但本次未深入的方向。"""

    print("正在生成访谈稿...")
    result = call_kimi(config, [
        {"role": "user", "content": prompt},
    ], temperature=0.85)

    # Save
    out_dir = Path(os.path.expanduser("~/content work/content/interviews/auto-generated"))
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    filename = f"访谈稿_auto_{p[0]}_{t[0]}_{a[0]}_{today}.md"
    out_path = out_dir / filename
    out_path.write_text(result, encoding="utf-8")
    print(f"\n✅ 已保存: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else None
    tid = sys.argv[2] if len(sys.argv) > 2 else None
    aid = sys.argv[3] if len(sys.argv) > 3 else None
    generate(pid, tid, aid)
