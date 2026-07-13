---
name: web-scrape
description: 当用户给一个 URL 要从中提取数据/字段,或普通 curl/WebFetch 因 JS 渲染或反爬被挡而抓不到时使用。轻量优先,被封自动逐级升级(curl_cffi 反爬HTTP → playwright 浏览器渲染),用 bs4 提字段,输出 JSONL+manifest。零新增依赖,全用本机已装的库。不用于"这页讲什么"的阅读(走 WebFetch)或找资料调研(走 research);整站爬和绕反爬前先确认。
status: stable
agents: main
---

# web-scrape

## Purpose
用本机已有的 `curl_cffi`(伪装浏览器 TLS 指纹的反爬 HTTP)+ `playwright`(Chromium 渲染)+ `bs4`(解析)抓取「难抓的网页」并提结构化字段。
策略:**轻量优先,被挡才升级**;输出 JSON/JSONL + manifest;过出口验证;反爬/整站走红线确认。
零新增依赖——这些库本机已装,本 skill 只提供调度大脑和边界规则。

## When to use this skill
- 给了 URL,要从中提字段(标题、价格、列表项、链接等)。
- `WebFetch`/`curl`/`requests` 抓不到(JS 渲染、Cloudflare 等反爬拦截)。
- 需要可重跑、结果落盘成结构化数据(jsonl)的抓取。

## When not to use this skill
- 只想知道"这页讲什么" → 用 `WebFetch`。
- 抓正文转 Markdown 喂阅读 → 用 `source-intake` / `trafilatura`。
- 找资料 / 调研 → 用 `research`。
- 登录态 / 付费墙内私有数据 → 停,先和用户确认合规。
- 要"操控网站"(点按钮、填表单、连 Notion/gh)→ 用 `opencli browser`,不是抓取。

## User defaults
- 环境:本机 Mac(路径/代理参数化,可切服务器)。
- 反爬:`level=auto`,L1 普通请求优先,被封才升 L2 stealth → L3 浏览器。
- 输出:`data.jsonl` + `manifest.json`,落当前任务目录 `evidence/scrape/`。
- `robots.txt`:由调用者判断并在 manifest 标注(默认温和抓取,不暴力)。

## Required inputs
1. 目标 URL(缺则停,问)。
2. 要提取的字段(若字段不明:先抓一页 `--selector` 留空 dump 结构样本,让用户圈字段)。

## Optional inputs
- `--selector` CSS 选择器 / `--attr` 提属性(如 href) / `--limit` 上限。
- `--level`(auto/l1/l2/l3) / `--out` 输出路径。
- 代理(走环境变量,不写进脚本)。

## Boundary analysis
- 单页 / 给定 URL:直接做。
- 整站 / 自动翻页 / 抓量未知:**先确认**(限流 + 上限 + 预计条数)。
- 字段不明:先 dump 结构样本,不瞎猜选择器。

## Clarification rules
**必须问:** ① 无 URL ② 字段不明 ③ 要整站/翻页 ④ 疑似登录态/付费墙。
**不必问(用默认):** 输出格式、目录、重试次数、反爬升级策略、是否用浏览器。
集中一次问,不碎问。

## Transformation modes(抓取档位,自动升级)
1. **L1** — `curl_cffi` impersonate=chrome,最轻,默认首选。
2. **L2 stealth** — `curl_cffi` 更强指纹+重试,L1 被封时用;**升级前 stderr 告知正在绕反爬、可能踩 ToS**。
3. **L3 browser** — `playwright` Chromium 真实渲染,L2 仍失败或纯 JS 站;跑完即关(`with` 上下文)。

## Workflow
1. **环境自检**:`python3 -c "import curl_cffi, bs4; from playwright.sync_api import sync_playwright"`。缺则提示(正常本机已全装)。
2. **抓取**:`python3 scripts/scrape.py <url> --level auto`,自动逐级升级,返回 html + 实际档位。
3. **字段不明先 dump**:`--selector` 留空 → 出结构样本,让用户圈字段。
4. **提取**:`--selector '.item' --attr href` 按字段提取。
5. **导出**:`--out evidence/scrape/data.jsonl` → 写 jsonl + manifest.json。
6. **出口验证**(硬断言):count>0、关键字段非空、文件落盘可打开、manifest 记录真实档位。
7. **报告**:对话里 3~5 行人话(几条 / 哪档 / 存哪 / 是否完全成功);不产长 .md。

## Output format
- `evidence/scrape/data.jsonl` — 一行一条记录。
- `evidence/scrape/manifest.json` — `{source_url, count, fetcher_level, http_status, robots_respected, verdict}`,`verdict` ∈ `ok|empty|blocked`。
- 对话:3~5 行人话结论。

## File and directory rules
- 默认写 `<当前任务目录>/evidence/scrape/`;不存在则建。
- 不覆盖已有 `data.jsonl`:存在则自动加时间戳后缀(脚本已实现)。
- 不把整页原始 HTML 留进产物(除非 debug 且用户要)。

## Tool rules
- 路径/代理参数化,不写死(为切服务器留口)。
- 浏览器档 `with sync_playwright()` 跑完即关,不留进程(脚本已实现 `finally: browser.close()`)。
- 整站强制限流 + 上限。
- 频率温和,不暴力请求。

## Safety rules
1. 整站/翻页**先确认**。
2. 升级到 L2/L3 前 stderr **告知**正在绕反爬、可能踩目标站 ToS。
3. 不抓登录态/付费墙私有数据;不存别人 cookie/密钥进产物。
4. 抓 0 条/被封**如实报**,manifest `verdict=empty|blocked`,绝不编造数据。
5. 代理/账号走环境变量。

## Quality checklist
- [ ] 环境自检通过(curl_cffi/bs4/playwright 可 import)
- [ ] 抓取成功(count > 0,非反爬挑战页)
- [ ] 关键字段非空
- [ ] data.jsonl + manifest.json 已落盘且能打开
- [ ] manifest 记录真实 fetcher 档位与 verdict
- [ ] 反爬升级 / 整站前已告知或确认
- [ ] 未把私有/密钥数据写进产物

## Failure handling
- **L1 被挡** → 自动升 L2(告知)→ 仍挡升 L3。
- **L3 仍失败/被封** → 停,如实报:被哪种机制挡、试了哪些档、建议(换代理/降频/人工)。manifest `verdict=blocked`。
- **字段全空** → 选择器可能错或页面改版;`--selector` 留空 dump 结构样本让用户重圈,不硬塞空数据。manifest `verdict=empty`。
- **超时/抓量失控** → 中止,报已抓条数,问是否继续。

## When to upgrade to scrapling(扩展位,信号触发)
本 skill 用本机栈覆盖一次性/偶发抓取。当出现 **"固定几个站 + 长期自动重跑 + 怕改版断"** 的真实任务(如英语外刊流水线),再考虑装 `scrapling` 接入其**自愈选择器**(页面改版自动重定位元素)——届时在 L1 之上加一档,骨架不变。在此之前不装,避免多余依赖。

## Examples

### 例 1:信息完整
用户:"抓 https://example.com/products 的商品名和价格,存 jsonl。"
→ 环境自检 → `scrape.py <url> --selector '.product .name'` 成功(L1)→ 写 data.jsonl + manifest → 报"48 条,L1,存 evidence/scrape/data.jsonl"。

### 例 2:信息不完整
用户:"把这个页面数据抓下来 https://example.com/list"
→ 字段不明 → `scrape.py <url>`(selector 留空)dump 结构样本 → 问"每条有 标题/作者/日期/标签,要哪几个?" → 用户圈定后正式提取。

### 例 3:涉及反爬/危险操作
用户:"把 example-shop 整站商品爬下来,被 Cloudflare 挡了。"
→ 识别两红线:整站(抓量)+ Cloudflare(反爬+ToS)。
→ 停下报:"要绕 Cloudflare(踩目标站 ToS)且整站抓量大。建议:限定某分类页 + 限流 + 上限 N 条,用 L2/L3。确认范围和上限再开始?"
→ 确认后:L1→挡→L2(告知)→必要 L3 → 限流爬 → 出口验证 → 报真实条数。
