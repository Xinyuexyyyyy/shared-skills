# ROUTING — 规则调用层

> 日期：2026-07-13（v3，补 25 skill 全量路由 + GitHub mac↔win 同步后更新）
> 借鉴：semantic-router（决策层：意图→路由，规则=话术样例不是if-else）、lmos-router（LLM/向量/混合三法）、Uno-Orchestra（吝啬路由：简单任务直接答，别浪费预算）。
> 它是什么：用户说人话，agent 据本表实时**决策"这句话该调什么"**——可以是 skill、skill 链、插件、或直接答。不是预写死的编排流水线。
> 配套：[ARCHITECTURE.md](ARCHITECTURE.md)。

---

## 一、怎么用（agent 每轮开局后）

1. 听用户第一句 → 在下面的「规则表」里找**最匹配的意图话术**那一行（语义匹配，由我这个 LLM 直接做，等于天然的 LLM-based 路由）。
2. **先吝啬判断**（Uno 原则）：这事是不是简单到直接做就行？是 → 直接答，**不路由**。
3. 需要路由 → **先报一句**："这像【X】，我调 `<目标>`，开始？" 用户点头再走。
4. 拿不准匹配哪条 → 直接问，不硬套。

**核心心法**：路由是"决策调什么"，不是"必须套个流程"。简单直接答 > 套链。

---

## 二、规则表（意图话术 → 调用什么）

每条规则 = 一组**意图话术样例** + **调用目标** + **要不要路由**。调用目标不限于 skill。

| # | 意图话术样例（用户大概会怎么说） | 调用什么 | 路由? |
|---|---|---|---|
| 1 | "写段代码 / 修 bug / 加个功能 / 重构 / 实现…" | **superpowers 插件**（已装，自动触发 spec→plan→TDD） | 重活→路由 |
| 2 | "写篇文章 / 公众号 / 内容稿 / 帮我写…" | `content-pipeline`（链：interview→debate→studio→output）；单访谈稿→`interview-writer` | 重活→路由 |
| 3 | "调研 / 研究 / 竞品 / 产品调查 / 综合决策 / 文献综述 / 找论文 / 模糊想法想挖…" | `deep-research`（所有调研请求的唯一用户可见总入口；内部可调 research-layer-v2 / research / academic-deep-research / idea-to-research / harvest-tool / source-intake） | 重活→路由 |
| 4 | "明确点名 academic-deep-research / paper-discovery / paper-screening…" | 显式调用对应学术子 skill；否则默认先进 `deep-research` | 点名才直达 |
| 5 | "明确点名 idea-to-research / 只想先判路线…" | 显式调用 `idea-to-research`；否则默认由 `deep-research` 内部判断是否需要它 | 点名才直达 |
| 6 | "找能借鉴的 GitHub 项目…" | `harvest-tool` | 路由 |
| 7 | "读下这个 URL/PDF/资料…" | `source-intake` | 轻，多数直接做 |
| 7b | "抓这个网站的数据/字段 / 爬下来 / curl 抓不到被反爬挡了…" | `web-scrape`（轻量优先自动升级，输出 jsonl） | 看情况 |
| 7c | "总结/分析这个视频/播客 / 这个 B站·YouTube·小宇宙链接讲了啥 / 把视频转成文字…" | `bilibili-video-analyzer`（下载→转写→LLM 分析，产 transcript+analysis JSON） | 重活→路由 |
| 8 | "做个 PPT / 演示…" | `ppt-master-bridge`→`ppt-master` | 重活→路由 |
| 9 | "连 Win/服务器 / 部署 opencove…" | 先查 `DEVICES.md`；opencove 部署→`opencove-remote-deploy` | 看情况 |
| 10 | 复杂、要拆的活（任意类型） | 前置 `task-analyze`→`task-decompose`，再进对应行 | 路由 |
| 10b | 生成结构化任务文件、规划大任务 | `task-crafter`（生成 TASK/state/context/artifacts/log 五件套） | 路由 |
| 10c | 新项目、写蓝图、全流程管理 | `project-sop`（蓝图→拆任务→开发→测试→收尾） | 路由 |
| 10d | 审问我、grill me、这个方案有什么问题 | `grillme`（分层诊断式提问，复杂方案提交前压力测试） | 路由 |
| 10e | 初始化工作区 / 整理工作区 | `workspace-init` / `workspace-tidy` | 看情况 |
| 11 | 任何活做完 | `closeout`（收尾+提议更新 tasks/记忆） | 收尾必走 |
| 12 | 润色 / 去 AI 味 / 改得像人话 / 输出成品(Obsidian/docx/pdf) / 画流程图 | `output-layer`（公共输出路由，可内调 humanizer / output-polisher / output-style-checker / drawio-diagram-agent） | 看情况 |
| 12b | 画 draw.io 图 / 流程图 / 架构图 / 路线图 | `drawio-diagram-agent`（文字→紧凑 draw.io） | 轻量→直接做 |
| 13 | 评测 skill / skill 评分 / 优化 skill / 对齐工作方式 | `skill-optimizer` | 路由 |
| 13b | 打开技能面板 / 看看我的技能 / 有什么 skill | `skill-dashboard` | 轻量→直接做 |
| 13c | 引入外部 skill / 这个 GitHub skill 能用吗 | `skill-reforge`（外部引入→验证→适配） | 路由 |
| 0 | **简单问答 / 查个事实 / 闲聊 / 一句话能答** | **直接答，不调任何东西** | ❌ 不路由 |

### 调研入口边界（别混）

第 3/4/5 行都沾"研究/调研"，但现在只有一个默认用户入口：

- **默认**：凡是调研、研究、竞品、市场、学术/论文、产品发现、PRD、模糊想法探索，都先进入 `deep-research`。它负责判断要不要正式调研、当前阶段、是否需要 brainstorm / grillme / 取证 / PRD 或降级。
- **内部能力**：`research-layer-v2` 是内部方法层；`research` 是模板包/取证层；`academic-deep-research` 是学术子链；`idea-to-research` 是模糊想法的路线判断能力；`harvest-tool` / `source-intake` / `web-scrape` 是证据或资料处理能力。
- **显式点名例外**：用户明确说"调用 academic-deep-research""直接用 idea-to-research""跑 paper-discovery"时，才允许绕过 `deep-research` 直达子 skill。
- **轻量例外**：如果只是名词解释、单点事实、随口问一句，直接答，不进入正式 `deep-research`。
- **PRD 方法卡 smoke 例外**：如果用户只问"PRD 该用哪些方法卡 / PRD vs brief / MVP 和未来边界混了 / PRD Gate 失败回哪层 / Gate 发现问题后转成追问 / Grok 式重复追问 / PRD 太长 / 缺按钮、状态、数据、验收路径"，尤其写了"只做路由 smoke"，不要理解成前端页面路由测试，也不要直接写 PRD。先读 `methodology-distiller` 的 PRD 方法卡 overlay，并在回答里引用具体卡片路径。

一句话：**调研先找 deep-research；子 skill 是它内部可调用的能力，不再默认跟它抢入口。**

### 网页处理三件事别混（第 7/7b/9 行）

- **读懂一个页面/资料讲什么** → `source-intake`（第 7 行）。给人看的理解,不落结构化数据。
- **从页面批量提字段、抓数据** → `web-scrape`（第 7b 行）。轻量优先,被反爬挡了自动升级到浏览器,输出 jsonl+manifest。
- **操控一个网站做交互**(点按钮/填表单/连 Notion/gh) → `opencli browser`（不在本表,直接调命令）。
- **读懂一个视频/播客的内容**(B站/YouTube/小宇宙链接) → `bilibili-video-analyzer`（第 7c 行）。下载→转写→LLM 分析,产 transcript+analysis JSON,供上游消费。小宇宙 yt-dlp 直接吃,无需额外适配。

一句话：**读内容找 source-intake,抓数据找 web-scrape,操控网站用 opencli,听/看视频播客找 bilibili-video-analyzer。**

---

## 三、三条决策原则

1. **吝啬优先**（Uno）：先问"用直接答能不能解决"。能 → 第 0 行，不路由。路由是给重活的，不是给每句话的。
2. **调用目标开放**：路由终点可以是 skill、skill 链、插件（superpowers）、外部命令、或"直接答"——本表是"调什么"的决策层，不只是 skill 编排。
3. **报而后行**：路由前先报"这像 X，调 Y，开始？"，用户可拦截/改道。规则是建议不是枷锁。

---

## 四、为什么不用向量库

semantic-router 等用 Python 向量算相似度，因为它们的宿主是无脑程序。**我这个 LLM 本身就能做语义匹配**——读这张话术表，判断用户这句最像哪行，等于天然的 LLM-based 路由，不需要额外向量库。符合"纯 markdown、不要黑箱"。

## 五、维护

- 新高频任务类型 → 加一行（话术样例 + 调用目标 + 路由与否）。
- 某条老路由不准 → 改它的话术样例，让匹配更准。
- superpowers 重启会话后生效；它 always-on 自触发，本表只负责把编程类指向它。
