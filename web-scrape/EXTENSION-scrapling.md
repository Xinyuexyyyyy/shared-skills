# EXTENSION: scrapling 接入预案

> 本文件是**预案**,不是接入说明。当前 web-scrape skill **未装 scrapling**,本文档说明"何时该装、怎么装、装错了怎么撤"。
> 接入前请先核对 §1 的触发信号是否真实发生。**不要因为"听起来有用"就装。**

---

## 0. 一句话定位

scrapling 唯一对本 skill 有增量价值的能力是 **adaptive selector**:页面改版后,用元素相似度算法把旧选择器"自愈"到新位置。其余三档抓取(HTTP/Stealth/Browser)在本机已用 `curl_cffi` + `playwright` 覆盖,**装它不会让普通抓取变快或变稳**。

---

## 1. 触发信号(没出现就别装)

接入 scrapling 的成本(装库 + 装浏览器 + 多一个心智模型)只有在**同一目标站长期自动重跑、且改版会真实打断流水线**的场景才回本。判据要可观测,不能凭感觉。

### 1.1 硬信号(全部满足才考虑)

- **重跑次数**:同一 URL(或同一站的同模板 URL)被本 skill 抓过 **≥ 20 次**(在 manifest.json 或调用方日志里可数)。
- **失效频次**:过去 **6 个月**内,该 URL 至少发生 **2 次**"选择器失效"事件——表现为 manifest 的 `verdict=empty` 且关键字段全空,而 fetcher 档位返回 HTTP 200(即站还在,只是结构变了)。
- **修复成本**:每次失效后,人工重新圈选择器 + 回填脚本的时间 **≥ 15 分钟**(短于这个数,人工修比自愈便宜)。

### 1.2 软信号(任一出现可加权)

- 该抓取任务接了 cron / scheduler,**无人值守**,改版当天就会出错数据。
- 下游消费方(如 english-app、外刊 pipeline)对**当日数据缺失敏感**——空 jsonl 直接影响用户能不能做题/阅读。
- 抓取目标 ≥ **3 个不同模板** 但都属于"长期重跑"序列;单站不够,多站才摊得开 scrapling 的安装成本。

### 1.3 反信号(出现一个就别装)

- 抓取任务是**一次性**或**偶发**(< 月度频率)——改版了人工重圈就行。
- 目标站结构非常稳定(如 example.com、维基百科条目页)——adaptive 永远不触发,纯负担。
- 真正的痛点是**反爬绕过**而不是改版自愈——这是 L2/L3 的事,scrapling 不解决新增反爬。
- 当前流水线已经依赖 `gh-proxy` 直接拉文件(如 english-zine-pipeline 拉 EPUB),根本没在解析 HTML——装了也用不上。

---

## 2. 接入方式(如果触发信号已满足)

### 2.1 接入位置

**不替换现有三档**。在 `fetch_html` 之上加一层"adaptive 调度":

```
                       ┌──────────────────────────────┐
                       │  fetch_html(url, level=auto) │
                       └──────────────┬───────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
       L1 curl_cffi             L2 stealth              L3 playwright
       (现状不变)               (现状不变)               (现状不变)
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            │       extract(html, selector)  ← 现状不变          │
            └─────────────────────────┬─────────────────────────┘
                                      │
                            selector 命中 0 条?
                                      │
                              yes  ┌──┴──┐  no  → 直接返回
                                   ▼     ▼
                          (新增)adaptive 重定位 → 命中后写回 selector
```

也就是说,adaptive 是 `extract()` 的**兜底分支**,不是抓取档位。原 L1/L2/L3 完全不动。

### 2.2 启用条件

- CLI 显式传 `--adaptive`,或
- manifest 配置 `"long_running": true`(由调用方在抓取任务注册时写入,本 skill 不主动判断)

**默认关闭**。开启后才加载 scrapling,避免冷启动多花 1~2s。

### 2.3 持久化

scrapling 用 `auto_save=True` 把元素"签名"写到本地 pkl。本 skill 把它落到任务目录下,跟 evidence 并列:

```
<任务目录>/evidence/scrape/
├── data.jsonl
├── manifest.json
└── _adaptive_cache/
    ├── <url_hash>.pkl       # scrapling 自己的签名缓存
    └── selectors.json       # 我们维护的映射:url + selector_id → 最近一次命中位置
```

`_adaptive_cache/` 加进 `.gitignore`(或 evidence 整目录本就 gitignore)。**不进产物**(下游消费 data.jsonl,缓存只为下次启动加速)。

### 2.4 伪代码骨架(≤ 20 行,只展示分支)

```python
# 在 scripts/scrape.py 的 extract() 末尾加这一段。不要现在写,装了 scrapling 再写。
def extract(html, selector=None, attr=None, limit=None, adaptive=False, cache_dir=None):
    nodes = soup.select(selector) if selector else []
    if nodes or not adaptive:
        return _to_values(nodes, attr, limit)        # 现状路径
    # ↓ 仅当 adaptive=True 且选择器命中 0 条时进入
    from scrapling.parser import Adaptor             # lazy import,默认不加载
    adaptor = Adaptor(html, storage_file=cache_dir / "elements.pkl")
    relocated = adaptor.css(selector, adaptive=True) # 用签名自愈
    if not relocated:
        return []                                    # 自愈也失败:如实报 empty
    _persist_new_selector(cache_dir, selector, relocated.css_path)  # 写回新位置
    return _to_values(relocated, attr, limit)
```

(API 名以 scrapling 当时版本为准,这里只示意分支结构。)

### 2.5 manifest 增字段

接入后,manifest.json 增加两个字段,供回放和审计:

```json
{
  "adaptive_enabled": true,
  "adaptive_hit": "relocated|hit_original|miss"
}
```

- `hit_original`:原 selector 直接命中,adaptive 没动 → 一切正常。
- `relocated`:原 selector 0 条,adaptive 重定位成功 → 报警提醒"网站改版了,新 selector 已写回缓存"。
- `miss`:adaptive 也失败 → `verdict=empty`,等同于现在的失败路径。

---

## 3. 依赖成本(装之前先算账)

### 3.1 pip 安装

- `pip install "scrapling[fetchers]"`:拉 scrapling 本体 + curl_cffi + playwright + 一堆解析器(`cssselect`/`lxml`/`tldextract` 等)。本机大多已有,增量约 **20~40 MB** wheels。
- `scrapling install`:下载并配置 fingerprint 浏览器二进制 + camoufox patch。**首次运行**约 **300~500 MB**(camoufox + 修补的 Chromium),时间 1~5 分钟,取决于网络。
- Python ≥ 3.10。本机已满足(查 `python3 --version`)。

### 3.2 运行时开销

- 不开 adaptive:`from scrapling.parser import Adaptor` 也不导入,**零开销**。
- 开 adaptive 首次:加载 scrapling 模块 + 读 pkl ≈ **0.5~1.5s**。后续同进程内忽略。
- adaptive 命中重定位:多一次相似度计算,**< 200ms**(scrapling README 自报数据,未实测)。

### 3.3 维护成本

- camoufox/Chromium 二进制要跟着 scrapling 升级走,**多一个升级渠道**(本机已有的 playwright Chromium 是另一套,二者并存)。
- scrapling 的 adaptive 算法是黑盒(README 提"intelligent similarity",未公开签名字段和算法名),自愈失败时**只能看 pkl 不能调参**。
- BSD-3 许可,自用/内部用无合规风险。

---

## 4. 决策门(if-then 清单)

按顺序问自己,任何一条答 NO 就先不接。

1. **"过去半年里,真的有 ≥ 2 次因为选择器失效导致 verdict=empty 吗?"**
   - 答 NO → 不装。问题还没出现,装了是猜需求。
   - 答 YES → 进下一条。

2. **"失效的目标是同一个 URL/同一个模板,还是分散在多个一次性站?"**
   - 分散 → 不装。adaptive 缓存以 URL 为粒度,一次性站没有"下次"。
   - 同一模板 → 进下一条。

3. **"这套抓取是无人值守的(cron/调度器)吗?"**
   - 否(每次人工触发)→ 不装。人在场,失效当场重圈更快。
   - 是 → 进下一条。

4. **"每次失效后,人工修选择器的耗时 × 失效频次,是否大于 1 次性装 scrapling 的成本(~30 分钟 + 500 MB)?"**
   - 算不过来 → 不装。
   - 算得过来 → 进下一条。

5. **"接入后,谁负责定期检查 `_adaptive_cache/` 里有没有 `relocated` 事件?"**
   - 没人负责 → 不装。adaptive 静默重定位等于"无声改版",几个月后 selector 已经飘到不知哪去,数据可能在错位置上对齐。
   - 有人/有 cron 巡检 → **可以接入**。

---

## 5. 回退方案

接入后若发现 scrapling 出问题(库 bug、误判重定位到错元素、camoufox 升级炸了),按以下顺序回退,**每一步都可独立做、不会把现有三档抓废**。

### 5.1 一级回退:关 adaptive,保留依赖

- 调用方移除 `--adaptive` 参数,或把 manifest 的 `long_running` 改回 false。
- 效果:`extract()` 的 lazy import 分支不再触发,行为退回到当前三档。scrapling 还在 site-packages 里但不工作。
- 适用:怀疑是 adaptive 算法误判,想保留库做对比测试。

### 5.2 二级回退:删 cache 重新学习

- 删除 `<任务目录>/evidence/scrape/_adaptive_cache/`。
- 下次抓取以原 selector 重新建签名(`auto_save=True` 自动重写)。
- 适用:cache 内容被污染(比如某次抓到的是反爬挑战页,签名记错了)。

### 5.3 三级回退:卸载 scrapling

```bash
pip uninstall scrapling
# camoufox 二进制单独清:位置见 scrapling 文档,通常在 ~/.cache/scrapling/
rm -rf ~/.cache/scrapling/
```

- 同时把 `scripts/scrape.py` 里 `extract()` 的 adaptive 分支移除(或留着 lazy import,反正进不去)。
- 效果:回到本文件起草前的状态,本机三档抓取不受影响。
- 适用:scrapling 主线 bug 影响其他 import,或决定长期不用。

### 5.4 回退后清单

- [ ] `python3 scripts/scrape.py <已知工作 URL>` L1 抓取仍 200 + 命中字段
- [ ] `manifest.json` 不再出现 `adaptive_*` 字段(或字段恒为 `null`)
- [ ] 相关任务目录的 `_adaptive_cache/` 已清空(或保留作日后取证)
- [ ] english-zine-pipeline 等下游消费方未感知到 schema 变化

---

## 6. 与现有 SKILL.md 的对接点

接入当天需要改的位置(预先记下,不现在改):

- `SKILL.md` § "Transformation modes":三档结构不变,补一句"`--adaptive` 开启 selector 自愈兜底"。
- `SKILL.md` § "Optional inputs":加 `--adaptive` 开关。
- `SKILL.md` § "When to upgrade to scrapling":把现在那段"未来扩展位"的简述指向本文件。
- `scripts/scrape.py`:`extract()` 加 adaptive 分支(见 §2.4);`_cli()` 加 `--adaptive` 参数;`write_manifest()` 加 `adaptive_enabled`/`adaptive_hit` 字段。
- 共识文件 `web-scrape-skill-consensus-v1.md` § 8 "待确认项"标记 scrapling 接入完成日期。

---

## 7. 不在本预案范围内的事

明确**不**因为装 scrapling 而做的事,避免范围漂移:

- 不替换 L1/L2/L3 现有实现。scrapling 的 Fetcher/StealthyFetcher/DynamicFetcher 与本机 curl_cffi/playwright 重叠,**重复装一套没有收益**。
- 不引入 scrapling 的 spider/session/proxy 模块。本 skill 不做整站爬,不维护长会话。
- 不把 scrapling 当默认 import。lazy import,只在 `--adaptive` 时触发。
- 不在 skill 外部维护 selector 注册表。adaptive cache 跟着任务目录走,任务删,cache 删。

---

## 8. 参考

- scrapling 官方文档:https://scrapling.readthedocs.io/en/latest/
- scrapling 仓库:https://github.com/D4Vinci/Scrapling (BSD-3)
- 本 skill 当前共识:`/Users/sure/Daily Work/task-draft/consensus/web-scrape-skill-consensus-v1.md`
- 最接近候选场景:`english-zine-pipeline`(目前用 gh-proxy 拉 EPUB,没在解析 HTML,**目前并不是触发场景**;若未来转为抓 HTML 版外刊页才进入候选)
