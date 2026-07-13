#!/usr/bin/env python3
"""
web-scrape: 轻量优先、被封自动升级的抓取核心。
底层全用本机已有依赖,零新增:curl_cffi(反爬HTTP) + playwright(浏览器) + bs4(解析)。

档位:
  L1 fetch    -> curl_cffi 伪装浏览器 TLS 指纹的 HTTP 请求(最轻,默认)
  L2 stealth  -> curl_cffi + 更完整浏览器头/重试(L1 被反爬挡时)
  L3 browser  -> playwright Chromium 真实渲染(JS 站 / L2 仍失败)

用法:
  fetch_html(url, level="auto")            -> (html, used_level)  自动逐级升级
  extract(html, selector=None)             -> 选元素或 dump 结构样本
  写出由调用方用 to_jsonl / write_manifest 完成
"""
import sys, json, time, argparse
from pathlib import Path

# 反爬挑战页特征(粗判:被 Cloudflare/验证挡)
_CHALLENGE_MARKERS = (
    "just a moment", "cf-browser-verification", "checking your browser",
    "attention required", "captcha", "enable javascript and cookies",
)


def _looks_blocked(status, html):
    if status in (403, 429, 503):
        return True
    low = (html or "").lower()[:4000]
    return any(m in low for m in _CHALLENGE_MARKERS)


def _l1_l2(url, impersonate, timeout, retries):
    """curl_cffi 档:L1=default impersonate, L2=更强+重试。"""
    from curl_cffi import requests as creq
    last_err = None
    for attempt in range(retries + 1):
        try:
            r = creq.get(url, impersonate=impersonate, timeout=timeout)
            return r.status_code, r.text
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"curl_cffi 请求失败: {last_err}")


def _l3_browser(url, timeout):
    """playwright Chromium:真实渲染,跑完即关。"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            return 200, page.content()
        finally:
            browser.close()


def fetch_html(url, level="auto", timeout=20, content_ok=None):
    """逐级升级抓取。返回 (html, used_level, status)。

    content_ok: 可选回调 (html) -> bool。即便 status=200 也由它判内容够不够;
                返回 False 触发升级(挡 JS 站"200 空壳"假成功)。auto 档生效。
    """
    def _ok(status, html):
        if _looks_blocked(status, html):
            return False
        if content_ok is not None and not content_ok(html):
            return False
        return True

    # L1
    if level in ("auto", "l1"):
        status, html = _l1_l2(url, "chrome", timeout, retries=1)
        if _ok(status, html):
            return html, "L1", status
        if level == "l1":
            return html, "L1", status
        reason = "被挡" if _looks_blocked(status, html) else "200 但选不到目标内容"
        print(f"[web-scrape] L1 {reason}(status={status}),升级 L2 stealth(绕反爬,可能踩目标站 ToS)", file=sys.stderr)

    # L2
    if level in ("auto", "l2"):
        status, html = _l1_l2(url, "chrome131", timeout, retries=2)
        if _ok(status, html):
            return html, "L2", status
        if level == "l2":
            return html, "L2", status
        reason = "仍被挡" if _looks_blocked(status, html) else "仍选不到目标内容"
        print(f"[web-scrape] L2 {reason}(status={status}),升级 L3 浏览器渲染", file=sys.stderr)

    # L3
    status, html = _l3_browser(url, timeout)
    return html, "L3", status


def _selector_has_hits(html, selector):
    """selector 在 html 里是否选到至少一个节点。auto 档用它判'200 空壳'。"""
    if not html or not selector:
        return True
    from bs4 import BeautifulSoup
    return bool(BeautifulSoup(html, "lxml").select(selector))


def extract(html, selector=None, attr=None, limit=None):
    """selector=None 时 dump 结构样本;否则按 CSS 选择器提取文本/属性。"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    if not selector:
        # 结构样本:列出页面主要可选标签 + 类名,帮用户圈字段
        sample = []
        for tag in soup.find_all(True, limit=60):
            cls = ".".join(tag.get("class", [])) if tag.get("class") else ""
            ident = f"{tag.name}" + (f".{cls}" if cls else "")
            txt = tag.get_text(strip=True)[:60]
            if txt:
                sample.append({"selector_hint": ident, "sample_text": txt})
        return {"_structure_sample": sample[:40]}
    nodes = soup.select(selector)
    if limit:
        nodes = nodes[:limit]
    out = []
    for n in nodes:
        out.append(n.get(attr) if attr else n.get_text(strip=True))
    return out


def to_jsonl(records, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path = out_path.with_name(out_path.stem + "-" + str(int(time.time())) + out_path.suffix)
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return str(out_path)


def write_manifest(out_dir, source_url, count, level, status, verdict):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    m = {
        "source_url": source_url,
        "count": count,
        "fetcher_level": level,
        "http_status": status,
        "robots_respected": "manual",
        "verdict": verdict,  # "ok" | "empty" | "blocked"
    }
    p = out_dir / "manifest.json"
    p.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(p)


def _cli():
    ap = argparse.ArgumentParser(description="web-scrape 抓取核心")
    ap.add_argument("url")
    ap.add_argument("--level", default="auto", choices=["auto", "l1", "l2", "l3"])
    ap.add_argument("--selector", default=None, help="CSS 选择器;省略则 dump 结构样本")
    ap.add_argument("--attr", default=None, help="提取属性而非文本,如 href")
    ap.add_argument("--out", default=None, help="输出 jsonl 路径;省略则打印")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    html, level, status = fetch_html(
        a.url,
        level=a.level,
        content_ok=(lambda h: _selector_has_hits(h, a.selector)) if a.selector else None,
    )
    data = extract(html, selector=a.selector, attr=a.attr, limit=a.limit)
    if isinstance(data, dict):  # 结构样本
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    verdict = "ok" if data else "empty"
    if a.out:
        path = to_jsonl([{"value": d} for d in data], a.out)
        out_dir = Path(a.out).parent
        write_manifest(out_dir, a.url, len(data), level, status, verdict)
        print(f"[web-scrape] {len(data)} 条 | 档位 {level} | status {status} | -> {path}")
    else:
        print(json.dumps({"count": len(data), "level": level, "data": data}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _cli()
