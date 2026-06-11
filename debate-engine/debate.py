#!/usr/bin/env python3
"""
debate-engine: AI 吵架引擎 v2
完整辩论赛制：立论 → 驳论 → 自由辩论（多轮对话）→ 裁判提取
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

ENV_PATH = Path(os.path.expanduser("~/Daily Work/.env"))


def load_env():
    config = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                config[key.strip()] = val.strip()
    return config


def call_kimi(config, messages, temperature=0.8, retries=3):
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
    for attempt in range(retries):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=180)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            if attempt < retries - 1:
                wait = 5 * (attempt + 1)
                print(f"  [网络错误，{wait}s 后重试 ({attempt+1}/{retries})...]")
                time.sleep(wait)
            else:
                raise


# === 角色 system prompts ===

ADVOCATE_SYSTEM = """你是正方辩手。你基于自己的素材，有一套完整的世界观和主张。
规则：
- 你有自己的正面立场，不只是防守
- 必须引用素材原文支撑观点
- 既要捍卫自己的主张，也要主动攻击对方的立场
- 态度坚定但讲道理，不回避对方有力的质疑
- 用中文回答，300字以内"""

CHALLENGER_SYSTEM = """你是反方辩手。你基于自己的素材，有一套独立的世界观和主张。
你不只是"反对正方"——你有自己要捍卫的立场。
规则：
- 你有自己的正面立场，不只是拆台
- 必须引用素材原文支撑观点
- 既要攻击对方的漏洞，也要建设自己的论点
- 态度尖锐、不留情面，但言之有物
- 用中文回答，300字以内"""

JUDGE_SYSTEM = """你是裁判。你不判对错，只提取辩论中暴露的核心张力。
你的输出必须是严格的 JSON 格式，包含以下字段：
- core_tension: 一句话描述这场辩论揭示的核心矛盾/张力
- resolution_paths: 数组，2-3条可能的解决路径，每条包含 path（路径描述）和 narrative_strength（1-5分）
- connections: 数组，辩论中浮现的素材间意外连接
- strongest_moment: 辩论中最有力的一击（引用原文）
- new_ground: 自由辩论阶段碰撞出的、双方立论中都没有的新东西"""


def run_debate(material_a: str, material_b: str, material_c: str = ""):
    """完整辩论赛制：立论→驳论→自由辩论→裁判提取"""
    config = load_env()
    if not config.get("KIMI_API_KEY"):
        print("错误：未找到 KIMI_API_KEY，请检查 ~/Daily Work/.env")
        sys.exit(1)

    challenger_material = material_b
    if material_c:
        challenger_material += f"\n\n---\n\n{material_c}"

    # === Phase 1: 立论 ===
    print("\n" + "=" * 60)
    print("【Phase 1: 立论】双方各自陈述正面主张")
    print("=" * 60)

    print("\n--- 正方立论 ---")
    adv_thesis = call_kimi(config, [
        {"role": "system", "content": ADVOCATE_SYSTEM},
        {"role": "user", "content": f"以下是你的素材：\n\n{material_a}\n\n请基于这个素材，陈述你的正面主张。不是总结素材，是提出你的立场和世界观。必须引用素材原文。"},
    ])
    print(f"\n正方：\n{adv_thesis}\n")

    print("--- 反方立论 ---")
    chal_thesis = call_kimi(config, [
        {"role": "system", "content": CHALLENGER_SYSTEM},
        {"role": "user", "content": f"以下是你的素材：\n\n{challenger_material}\n\n请基于这个素材，陈述你自己的正面主张。不要管正方说了什么——你有你自己的立场和世界观。必须引用素材原文。"},
    ])
    print(f"\n反方：\n{chal_thesis}\n")

    # === Phase 2: 驳论 ===
    print("\n" + "=" * 60)
    print("【Phase 2: 驳论】双方攻击对方的立论")
    print("=" * 60)

    print("\n--- 正方驳论（攻击反方立论）---")
    adv_rebuttal = call_kimi(config, [
        {"role": "system", "content": ADVOCATE_SYSTEM},
        {"role": "user", "content": f"你的立论是：\n{adv_thesis}\n\n反方的立论是：\n{chal_thesis}\n\n请攻击反方的立论。找到他论点中的漏洞、矛盾或不成立的前提。同时巩固你自己的立场。"},
    ])
    print(f"\n正方：\n{adv_rebuttal}\n")

    print("--- 反方驳论（攻击正方立论）---")
    chal_rebuttal = call_kimi(config, [
        {"role": "system", "content": CHALLENGER_SYSTEM},
        {"role": "user", "content": f"你的立论是：\n{chal_thesis}\n\n正方的立论是：\n{adv_thesis}\n\n正方刚才还攻击了你：\n{adv_rebuttal}\n\n请攻击正方的立论，同时回应他对你的攻击。巩固你自己的立场。"},
    ])
    print(f"\n反方：\n{chal_rebuttal}\n")

    # === Phase 3: 自由辩论 ===
    print("\n" + "=" * 60)
    print("【Phase 3: 自由辩论】双方就核心分歧展开对话式争夺")
    print("=" * 60)

    free_debate_context = f"""辩论背景：
正方立论：{adv_thesis}
反方立论：{chal_thesis}
正方驳论：{adv_rebuttal}
反方驳论：{chal_rebuttal}"""

    free_debate_log = []

    # Round 1: 正方开火
    print("\n--- 自由辩论 Round 1 ---")
    free_adv_1 = call_kimi(config, [
        {"role": "system", "content": ADVOCATE_SYSTEM},
        {"role": "user", "content": f"""{free_debate_context}

现在进入自由辩论。你可以：提出新角度、追问对方回避的问题、让步后反击、或揭示更深层的矛盾。
不要重复之前说过的话。找到你们之间最核心的那个分歧，往深处挖。"""},
    ])
    print(f"\n正方：{free_adv_1}\n")
    free_debate_log.append(f"正方：{free_adv_1}")

    # Round 1: 反方回应
    free_chal_1 = call_kimi(config, [
        {"role": "system", "content": CHALLENGER_SYSTEM},
        {"role": "user", "content": f"""{free_debate_context}

正方在自由辩论中说：
{free_adv_1}

请回应。你可以：反击、追问、让步后提出更强的论点、或把战场拉到新的维度。
不要重复之前说过的话。往深处挖。"""},
    ])
    print(f"\n反方：{free_chal_1}\n")
    free_debate_log.append(f"反方：{free_chal_1}")

    # Round 2: 正方继续
    print("\n--- 自由辩论 Round 2 ---")
    free_adv_2 = call_kimi(config, [
        {"role": "system", "content": ADVOCATE_SYSTEM},
        {"role": "user", "content": f"""{free_debate_context}

自由辩论进行中：
{chr(10).join(free_debate_log)}

请继续。这是自由辩论的最后一轮，说出你最有力的话。可以让步、可以反击、可以提出全新角度。"""},
    ])
    print(f"\n正方：{free_adv_2}\n")
    free_debate_log.append(f"正方：{free_adv_2}")

    # Round 2: 反方最终回应
    free_chal_2 = call_kimi(config, [
        {"role": "system", "content": CHALLENGER_SYSTEM},
        {"role": "user", "content": f"""{free_debate_context}

自由辩论进行中：
{chr(10).join(free_debate_log)}

请做最终回应。这是你最后的机会。说出你最核心的判断。"""},
    ])
    print(f"\n反方：{free_chal_2}\n")
    free_debate_log.append(f"反方：{free_chal_2}")

    # === Phase 4: 裁判提取 ===
    print("\n" + "=" * 60)
    print("【Phase 4: 裁判提取】")
    print("=" * 60)

    full_log = f"""=== 正方立论 ===
{adv_thesis}

=== 反方立论 ===
{chal_thesis}

=== 正方驳论 ===
{adv_rebuttal}

=== 反方驳论 ===
{chal_rebuttal}

=== 自由辩论 ===
{chr(10).join(free_debate_log)}"""

    synthesis = call_kimi(config, [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": f"以下是完整辩论记录：\n\n{full_log}\n\n请提取核心张力，输出 JSON。"},
    ], temperature=0.3)
    print(f"\n裁判：\n{synthesis}\n")

    return {"debate_log": full_log, "synthesis": synthesis}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        config = load_env()
        print("测试 Kimi API 连通性...")
        try:
            result = call_kimi(config, [
                {"role": "user", "content": "说一个字：好"},
            ], temperature=0)
            print(f"连通成功！响应: {result}")
        except Exception as e:
            print(f"连通失败: {e}")
        sys.exit(0)

    if len(sys.argv) < 3:
        print("用法: python3 debate.py <素材A文件> <素材B文件> [素材C文件]")
        print("  或: python3 debate.py --test")
        sys.exit(1)

    mat_a = Path(sys.argv[1]).read_text(encoding="utf-8")
    mat_b = Path(sys.argv[2]).read_text(encoding="utf-8")
    mat_c = Path(sys.argv[3]).read_text(encoding="utf-8") if len(sys.argv) > 3 else ""

    run_debate(mat_a, mat_b, mat_c)
