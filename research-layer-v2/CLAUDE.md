---
name: research-layer-v2
description: deep-research 内部方法层/编排参考。从模糊想法到可执行 PRD 或 brief 的转换方法：Gate/Clarify → Research Map → Evidence Backend Selection → 宽证据与可见 brainstorm → 自适应 grillme / methodology-distiller → Narrowed Verification → readiness。支持搜索、网页阅读、浏览器实测、结构化抓取、GitHub、论文/报告等多证据后端。不作为默认用户可见入口；用户调研请求先进 deep-research。
---

# 调研层 v2.1（内部方法层）

## Purpose

为 `deep-research` 提供内部方法层参考：把用户的模糊想法、调研问题、产品发现、竞品/市场问题、论文方向或 PRD 前需求，收敛成**可验证、可追溯、可降级**的交付物。

本层不是用户默认入口。用户说"调研一下 X"时，默认先进入 `deep-research`，再由 `deep-research` 按需使用本方法层。

v2.1 的重点是把调研从"搜资料/找开源项目"升级成**多证据后端编排**：搜索、网页阅读、浏览器实测、结构化抓取、GitHub 项目、论文/报告、用户评论、产品文档都可以成为证据，但必须被分层记录和映射到决策。

## When to use

- `deep-research` 需要方法框架时。
- 维护调研阶段、证据格式、工具选择规则、PRD readiness 时。
- 用户明确点名要看或改 `research-layer-v2`。
- 调研结果需要从"资料摘要"升级为"产品/决策/PRD 可用证据"时。

## When not to use

- 用户只是自然语言说"帮我调研一下 X"（应先进 `deep-research`）。
- 用户只要一句 quick fact 或概念解释。
- 用户已经在执行具体任务，需要的是改代码/写文档。
- 用户只是闲聊发散，不想正式调研。

## Workflow

```text
Phase 0: Gate / Clarify
Phase 1: Research Plan
Phase 2: Wide Evidence + Visible Brainstorm
Phase 3: Adaptive Grillme
Phase 4: Narrowed Verification
Phase 5: PRD / Brief Readiness
```

阶段可以合并执行，但不能跳过它们代表的判断。尤其不能跳过：Research Plan、Narrowed Verification、readiness。

## Phase 0：Gate / Clarify

目标：判断这是不是正式调研，并确认最容易导致跑偏的变量。

先判断：

- **quick answer**：名词解释、单点事实、轻量判断 → 直接答，不进正式流程。
- **formal research**：市场/竞品/论文/产品发现/PRD/综合决策/模糊想法 → 进入流程。

正式调研前优先确认 3 个强问题：

1. **给谁用？** 目标用户、读者、客户、决策者是谁？
2. **什么痛点或决策？** 不做这次调研会怎样？
3. **做成什么样算成功？** 用户怎么验收？

这 3 个问题不是固定问卷。上下文已经回答时不要重复问。用户不答时可以带假设进入 Phase 1，但必须标注"待确认"。

内部记录：

```text
Goal:
Audience:
Decision / pain:
Success:
Known constraints:
Assumptions:
Unknowns:
```

## Phase 1：Research Plan（信息地图 + 证据计划）

目标：先确定这次调研需要看哪些对象、为什么要看、用什么证据后端、最低可信证据是什么。

不要一上来就只搜 GitHub 或竞品。先画 Research Plan：

| 地图块 | 要回答的问题 | 是否必看 |
|---|---|---|
| Market / category | 这个问题属于哪个市场、类别或问题域？ | 看任务 |
| Users / pains | 谁痛、痛在哪里、现在怎么绕路？ | 产品/决策类必看 |
| Workflow / JTBD | 当前任务链路、触发条件、前后置步骤、失败点、人工替代方案是什么？ | 工具/流程类必看 |
| Competitors / alternatives | 现有替代方案是谁？怎么定位、定价、交付？ | 市场/产品类必看 |
| Tools / open source | 有哪些可借鉴、可改造、不能抄的项目？ | 工具/实现类必看 |
| Methodology / framework | 这个领域成熟做法、判断标准、流程是什么？ | 方法/成长/系统类必看 |
| Official pages / docs | 官网、文档、定价页、demo 是否支撑关键说法？ | 竞品/工具类必看 |
| Community / reviews | 用户真实反馈、抱怨、绕路是什么？ | 体验/需求类优先看 |
| Distribution / business | 用户从哪里发现、谁付费、免费/付费边界、采用或切换成本是什么？ | 商业/工具类看任务 |
| Integration / ecosystem | 依赖哪些平台、API、账号、权限、插件或外部系统？ | 自动化/集成类必看 |
| Data availability / rights | 数据从哪里来、是否有权限、质量是否够、是否有隐私/历史数据问题？ | 数据类必看 |
| Feasibility / implementation risk | 是否有开放 API、实时性、账号/支付门槛、平台条款或明显不可行点？ | 高风险实现类必看 |
| Academic / reports / data | 是否有论文、报告、指标或数据支持？ | 学术/高风险决策类必看 |
| Policy / constraints | 是否有合规、平台、时间、地域约束？ | 涉及法律/平台/教育/医疗等必看 |

输出给内部使用：

```text
Research Plan:
- Map block:
- Why it matters:
- Evidence backend:
- Minimum evidence:
- Downgrade if missing:
- Biggest unknown:
```

停止条件：知道至少 3 个应看的地图块，并为关键地图块写出最低证据标准；或明确这是轻量任务无需正式调研。

### Evidence Backend Matrix

| 证据后端 | 什么时候用 | 典型产物 | 何时不用 |
|---|---|---|---|
| `WebSearch` | 找入口、找候选、看广度、确认是否存在 | 候选列表、关键词、初始来源 | 已有明确 URL 时不要只搜 |
| `WebFetch` / `source-intake` | 读单个网页、PDF、本地资料、文档 | 页面摘要、关键段落、来源记录 | 需要点页面/看登录后 UI 时不够 |
| Browser / opencli / 自动化浏览器 | 需要真实打开页面、点菜单、看 UI、确认功能/价格/demo、截图留证 | 浏览器实测记录、截图、可观察功能 | 只需静态文字时不用上浏览器 |
| `web-scrape` / 结构化抓取 | 需要从列表页/定价页/评论页抽字段 | JSONL/表格、字段清单、抓取 manifest | 只读一两页时不要重爬 |
| `harvest-tool` / GitHub | 要找开源项目、仓库活跃度、可借实现 | 候选仓库、活跃度、借鉴/不抄分类 | 不是开源/实现问题时不要主导调研 |
| Academic / paper tools | 找论文、SOTA、研究空白、系统综述 | 候选论文、纳排、证据表、综述骨架 | 普通市场调研不要硬走学术链 |
| `research` 模板包 | 需求清楚且要系统性竞品/学术/综合报告 | route-specific 报告片段 | 模糊想法应先走 Phase 0/1 |
| Manual user interview / pasted material | 用户有一手经验、旧资料、私有语境 | 访谈事实、约束、原始上下文 | 不能替代外部证据 |

### 选择规则

- 先用 `WebSearch` 找入口，不把搜索摘要当最终证据。
- 单页可读用 `WebFetch` / `source-intake`。
- 页面需要交互、功能确认、定价确认、视觉/UI 判断时，用 browser/opencli。
- 需要批量字段时，用 `web-scrape`，并记录字段定义。
- 用户明确要开源项目时，GitHub 是一条证据泳道，不是全部调研。
- 用户选定方向后，Phase 4 至少用一种更靠近事实的证据后端核验，不只复述搜索结果。

最低证据标准：

| 调研问题 | 不能只用什么 | 最低应使用什么 |
|---|---|---|
| 竞品有什么功能？ | 搜索摘要 / 二手榜单 | 官网、docs、demo 或浏览器观察 |
| 价格是多少？ | 第三方博客 / 旧截图 | 官方 pricing page；无法确认则标时间戳和不确定 |
| 开源项目靠谱吗？ | README / star 数 | commit、issues、release、license、demo 或代码/文档成熟度 |
| 用户是否抱怨这个问题？ | 单篇帖子 | 评论/社区样本，并标注样本偏差 |
| 论文方法是否有效？ | 摘要 | 方法、benchmark、limitations 或综述证据 |
| 能不能接某 API？ | 搜索结果 | 官方 docs、rate limits、权限/认证说明、changelog |

如果最低证据拿不到，不要硬写 PRD；降级为 `evidence_brief`、`decision_brief` 或带明确待验证项的 `discovery_note`。

## Phase 2：Wide Evidence + Visible Brainstorm（宽证据与可见发散）

目标：先看足够广的可能性，再让用户选择方向。

### 做什么

1. 按 Research Plan 并行收集证据，至少覆盖 3 条相关证据类型。
2. 记录来源、证据类型、关键 claim、观察方式、置信度、支撑哪个决策。
3. 做 visible brainstorm：列出 3-5 个可能方向。
4. 每个方向写清：一句话价值、关键证据、主要优点、主要缺点。
5. 做 idea collision：至少让 2 个相邻领域做法、竞品解法、开源工具或方法论与当前问题相撞，产出 1-3 个混合选项；只允许碰撞与当前用户、场景、工作流、商业模式或实现路径存在明确相似性的相邻方案，避免强行类比。
6. 明确放弃项：哪些方向暂不做，为什么。

### 证据类型

| evidence_type | 含义 | 例子 |
|---|---|---|
| `search_discovery` | 搜索发现，只说明可能存在 | 搜索结果、目录页、榜单 |
| `page_reading` | 读过具体页面/文档 | 官网、定价页、docs、报告 |
| `browser_observation` | 浏览器实测看到的功能/UI/流程 | 打开 demo、点击菜单、截图 |
| `structured_scrape` | 批量抓字段得到的结构化证据 | 价格表、评论字段、产品目录 |
| `community_signal` | 社区/评论/用户反馈 | Reddit、HN、论坛、评论区 |
| `open_source_signal` | GitHub/开源项目证据 | star、commit、issue、README、demo |
| `academic_data` | 论文/报告/数据集证据 | paper、benchmark、survey、白皮书 |
| `user_provided` | 用户提供的一手材料 | 旧简历、访谈、内部记录 |
| `inference` | 基于证据的推断 | 明确标注，不当作事实 |

### Evidence Table Schema

证据表至少包含：

| 字段 | 说明 |
|---|---|
| `id` | 证据编号 |
| `evidence_type` | 证据类型 |
| `source` | URL、文件、仓库、访谈来源 |
| `claim` | 这条证据支持的具体说法 |
| `observed_by` | search / fetch / browser / scrape / github / paper / user |
| `confidence` | confirmed / high / medium / low / unverified |
| `supports_decision` | 支撑哪个方向或决策 |
| `gap` | 缺口或下一步验证 |

### 给用户看的 Phase 2 输出

```text
我先看到了这些方向：

方向 A：...
- 支撑证据：...
- 优点：...
- 缺点：...

方向 B：...
- 支撑证据：...
- 优点：...
- 缺点：...

方向 C：...
- 支撑证据：...
- 优点：...
- 缺点：...

可借工具 / 项目：...
可借方法论 / 框架：...
碰撞产生的新选项：...
需要浏览器/页面核验的点：...
暂时放弃：...

我建议先深入 X，因为 ...
你想选哪条，或者要我继续发散？
```

不做什么：

- 不在 Phase 2 写 PRD。
- 不把搜索摘要当结论。
- 不让开源项目调研淹没竞品、方法论、用户痛点或页面核验。
- 不把 brainstorm 写成单纯方向列表；必须说明至少一个"为什么这样组合更好/更差"。

停止条件：用户选择方向、要求继续发散，或所有方向都明显不可行。

## Phase 3：Adaptive Grillme / Layered Diagnosis（分层诊断）

目标：在收窄和 PRD/brief 前，把产品、交互、前端、后端、数据、证据、验收这些关键层的缺口放到正确位置。

不要把 grillme 固定成某个轮数，也不要只问几个边界问题就收官。按域诊断：

- **用户能回答的**：一次问一个高价值问题。
- **用户不能合理回答的**：不要逼用户答，转为方法论蒸馏、专家实践对比、开源/竞品证据检索或方案推荐。
- **仍不确定的**：记录为假设、风险或验证任务。

### 诊断域

| 域 | 要诊断什么 |
|---|---|
| Product | 用户、痛点、场景、优先级、non-goals |
| Interaction / UX | 用户步骤、页面状态、按钮、空/错/加载状态 |
| Frontend | 页面、组件、UI 状态、响应式、可访问性 |
| Backend | 业务规则、接口、权限、任务流、异步处理 |
| Data | 字段、文件目录、存储位置、生命周期、备份/迁移 |
| Evidence | 用户一手材料、竞品/开源/方法论/专家经验 |
| Acceptance | 谁验收、最短测试路径、可衡量完成标准 |

### 继续追问条件

1. 仍有会影响下一产物正确性的 ask-user gap。
2. 不回答会改变用户、场景、交互、实现边界、数据位置或验收标准。
3. 当前无法判断要走 PRD、decision brief、evidence brief 还是继续调研。
4. 用户回答引入新的关键不确定点。

### 转蒸馏条件

1. 问题属于前端、后端、数据、PRD 写法、架构、brainstorm 方法或领域方法论，用户明显不需要亲自懂。
2. 这个问题有成熟方法、专家经验、开源实现或竞品做法可比较。
3. 继续追问用户只会增加负担，不能提升决策质量。

优先调用 `methodology-distiller`，把问题转成方法论、专家实践、开源/竞品证据或默认方案对比。不要只写"需要蒸馏"而没有返回结果或明确验证任务。

蒸馏任务格式：

```text
Distillation needed:
- Domain:
- Question:
- Why user should not be forced to answer:
- Sources/method to inspect:
- Expected decision:
- How it feeds PRD/brief:
```

蒸馏返回格式：

```text
Distillation:
- Domain:
- Gap:
- Method used:
- Options:
- Recommendation:
- Main artifact insertion:
- Appendix / ADR / evidence note:
- Assumptions:
- Risks:
- Verification:
```

### 停止条件

1. 每个关键域都已经 answered / distilled / assumed / deferred。
2. `distilled` 必须有返回结果；不能只留下一个待办名义。
3. 剩余强缺口可以用明确假设处理，并标注待验证。
4. 用户明确接受 unresolved risk。
5. 继续问的收益低于打断用户的成本。

输出给下游：

```text
Goal:
Non-goals:
Key decisions:
Domain decisions:
- Product:
- Interaction / UX:
- Frontend:
- Backend:
- Data:
- Evidence:
- Acceptance:
Ask-user answered:
Distillation needed:
Assumptions:
Risks:
Acceptance:
Readiness: Ready / Partially ready / Not ready
Next step:
```

## Phase 4：Narrowed Verification（窄向打中核验）

目标：用户选定方向后，确认现有证据真的支撑当前方向。

这一步是 v2.1 的关键。不能只把 Phase 2 的宽证据换个说法写进 PRD。

### 必做判断

在写 PRD 或 decision brief 前，至少完成一种打中核验：

| 核验动作 | 什么时候做 | 产物 |
|---|---|---|
| 官网/文档确认 | 竞品、工具、功能存在性 | URL + 关键 claim |
| 定价页确认 | 涉及商业模式、价格、套餐 | 价格字段 + 时间 |
| 浏览器实测 | 需要确认 UI、demo、流程、功能入口 | 观察记录 / 截图路径 |
| 评论/社区抽样 | 需要确认用户痛点或满意/不满 | 样本、主题、代表性限制 |
| 结构化抓取 | 需要比较多个产品/字段 | 字段表 + manifest |
| GitHub 活跃度核验 | 需要判断开源项目可借程度 | star、commit、issue、license、demo |
| 论文/报告核验 | 需要理论、指标、研究证据 | paper/report + 关键结论 |
| 证据映射 | 无需再取新证据时 | Phase 2 证据如何支撑当前决策 |

### Narrowed Evidence Mapping

| 已确认决策 | 支撑证据 id | 证据强度 | 仍缺什么 | 下一步验证 |
|---|---|---|---|---|
| ... | E1, E4 | high / medium / low / unverified | ... | ... |

如果无法完成任何打中核验：

- 不能写 PRD。
- 降级为 `discovery_note` 或 `decision_brief`。
- 明确告诉用户缺哪类证据。

### 三张边界清单

核验后再定：

- **MVP**：第一版必须做什么。
- **Future**：有意义但不在第一版。
- **Out of Scope**：这个方向不碰什么。

停止条件：方向、边界、证据映射足以支持 PRD/brief，或明确降级。

## Phase 5：PRD / Brief Readiness

目标：选择正确交付物，而不是把所有东西都包装成 PRD。

### PRD 定位

PRD 不是执行文档，也不是想法说明书。PRD 是产品判定文档：让用户和下游执行者判断第一版做什么、不做什么、做到什么样算成功、什么情况下必须停下来问人。

不要新增 `Execution Handoff` 模块，也不要把 PRD 改成开发计划。把 codex-dev-loop / OpenSpec / Superpowers 的经验吸收到 PRD 的表达里：

- 目标写成用户可见结果，不写内部动作。
- MVP 写成第一版用户能完成的闭环，不写功能名清单。
- 关键能力用 `Requirement / Scenario`，必要时用 `Given / When / Then` 表达可验证行为。
- 风险写成 `Stop Conditions`：什么情况下必须停止、回到用户确认、回到调研或降级。
- 下一步只能指向：继续调研、回 `grillme` 补问题、回 `methodology-distiller` 蒸馏、任务拆解、执行，或降级交付。

### Independent PRD Quality Gate

PRD 不直接继承 Phase 3 的 handoff。即使 `grillme` 已经问完，也必须重新判断草稿本身是否能让实现者执行：

```text
Ready PRD = Boundary x Detail x Evidence x Acceptance x Stop Conditions
```

硬指标：

- **Boundary:** 目标用户、场景、MVP、Non-goals、Future、Out of Scope、假设、限制、未解决风险。
- **Detail:** 主 PRD 必须写清用户流程、页面/区域、关键按钮/命令、核心状态、输入输出和会影响产品判断的数据位置；API 设计、数据库结构、文件目录、组件层级、详细技术选型默认进附录 / ADR / implementation note，除非它们会改变范围、验收、权限、数据风险或 Stop Conditions。
- **Acceptance:** 最短验收路径、成功标准、失败标准、至少一个边界用例。
- **Stop Conditions:** 目标、边界、验收、证据、账号/付费/外部服务/数据迁移等条件不清时，必须停止并问人或降级。

Gate verdict：

- `Ready`：边界、细节、证据、验收和 Stop Conditions 足够支撑当前范围，可以写 PRD。
- `Needs Loopback`：缺口会改变范围、行为、实现、数据或验收，必须先回滚补齐。
- `Downgrade`：无法支撑 PRD，改交付 `idea_note` / `discovery_note` / `decision_brief` / `reader_brief` / `evidence_brief`。

PRD Gap Triage：

每个缺口必须先判归属，再决定去处。不要把所有缺口都问用户。

| Owner | 归属判断 | Route | Ask user? | Agent can resolve? |
|---|---|---|---|---|
| `User` | 只有用户知道的目标、取舍、偏好、真实场景、不能接受什么 | `grillme` / `prd-grok-loop` | Yes | No |
| `Evidence` | 外部事实、竞品、API 行为、工具限制、开源成熟度、当前页面行为、平台/账号/价格/权限等外部依赖不足 | Phase 4 / narrowed verification | No | Yes, by research；若发现外部条件卡住，转为 Stop Condition |
| `Method` | PRD 写法、前端、后端、API、数据、架构、UX、验收的专业默认值 | `methodology-distiller` | No | Yes, by distillation |
| `Spec` | 已有信息足够，只是 PRD 没写成步骤、状态、字段、路径、验收 | PRD detail / UI state / data / acceptance / subtraction pass | No | Yes, by spec pass |
| `Too fuzzy` | 目标、用户、场景或问题本身仍不成立 | 降级或回 Phase 0 / `grillme` | Maybe | No |

PRD Gate 输出必须对每个 Gap 写：

```text
Gap:
Owner: User / Evidence / Method / Spec / Too fuzzy
Route:
Ask user: Yes / No
Agent can resolve without user: Yes / No
Minimal next action:
```

Loopback routing：

- 用户、场景、优先级、偏好、边界冲突不清楚 → 回 `grillme`。
- 外部事实、竞品、来源置信度、当前页面/产品行为、平台/账号/权限/价格等外部依赖不足 → 回 Phase 4 / narrowed verification；若无法由 agent 解决，写成 Stop Condition。
- 前端、后端、API、数据、架构、PRD 写法等专业默认值缺失 → 回 `methodology-distiller`。
- UI 行为、按钮、状态、数据字段、路径、验收步骤不够 → 做 PRD detail pass；必要时再蒸馏。
- 正文太胀、方法论和规格混在一起 → 做 PRD subtraction pass。

PRD 缺口回到 `methodology-distiller` 时，优先使用：

```text
/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/INDEX.md
```

按缺口选择中文方法卡，不临场发明 PRD 结构。

### PRD readiness

只有满足以下条件才写 PRD：

- 目标用户明确。
- 用户问题或决策明确。
- Non-goals 明确。
- MVP wedge 明确，且写成用户可见结果。
- Boundary 过门：MVP / Future / Out of Scope / 假设 / 约束没有互相冲突。
- Detail 过门：主 PRD 的用户流程、核心 UI 行为、关键数据位置、验收路径足够具体；工程级 API、数据库、目录、组件细节已进入附录 / ADR / implementation note，或明确不影响产品判断。
- 至少核心能力能写成 `Requirement / Scenario`；关键场景可以用 `Given / When / Then` 验证。
- 至少 3 个关键假设被列出。
- 每个关键假设有证据或验证动作。
- Narrowed Verification 已完成：做过打中核验，或完成证据映射。
- 强问题已回答，或用户明确接受 unresolved risk。
- 验收标准可观察、可验证。
- Stop Conditions 明确：什么情况下不能继续写 PRD、不能进入执行、必须回滚补问题。
- 证据强度已标注。

如果 readiness 失败，不要先写完整 PRD。先输出 `PRD Quality Gate` 卡片，说明 `Ready / Needs Loopback / Downgrade`，再按最小回滚路径补齐或降级。

### 降级出口

- `idea_note`：想法仍太模糊。
- `discovery_note`：方向存在，但证据或假设还不够支撑 PRD。
- `decision_brief`：这是决策备忘，不是产品规格。
- `reader_brief`：只是资料理解，不应强行 PRD。
- `evidence_brief`：用户主要需要证据清单、竞品表、价格表或页面核验结果。

降级时必须说明：本轮能交付什么、哪些是假设、补哪些证据可升级。

### PRD 输出要求

先做 PRD 减法：把 `grillme`、`methodology-distiller`、证据表和 brainstorm 产物压成决策，不把全过程塞进正文。

主 PRD 必须包含：

1. 一句话目标。
2. 当前事实 / 背景。
3. 目标用户与核心场景。
4. MVP 范围（用户可见结果）。
5. Out of Scope。
6. Future / Roadmap / Vision。
7. 用户流程与页面 / 区域。
8. Requirements / Scenarios。
9. 数据与存放位置。
10. 验收标准。
11. 关键风险 / Stop Conditions。
12. 证据映射摘要。
13. 下一步。

主 PRD 只放产品判断和可执行的用户可见细节；方法论、来源、长对比、被放弃方案放进附录 / evidence brief；API 设计、数据库结构、文件目录、组件层级、具体技术选型、迁移策略、详细错误状态放进 ADR / implementation note。只有这些技术细节会改变产品判断时，才进入主 PRD。

当用户要求"系统 / 成长 / 长期 / 平台 / 生态 / 可扩展"时，PRD 不能只写轻量 MVP，必须保留 Roadmap 和 Vision，并说明为什么第一版不做。

## Evidence Confidence Ladder

证据强度按离事实的距离排序。写结论时要标置信心，不要把弱证据说成强证据。

| 等级 | 典型证据 | 用法 |
|---|---|---|
| `confirmed` | 自己浏览器实测、官方页面当前可见、结构化抓取字段可复查、用户一手材料确认 | 可支撑关键决策 |
| `high` | 官方文档/定价页/论文原文/可信报告，来源明确且当前可访问 | 可支撑主要判断 |
| `medium` | 第三方报道、评论样本、社区讨论、GitHub 活跃度信号 | 支撑趋势或假设 |
| `low` | 搜索摘要、单条评论、二手转述、未完整打开的页面 | 只能作为线索 |
| `unverified` | 推断、用户未确认假设、无法访问来源 | 必须标注待验证 |

规则：

- 搜索摘要最多是 `low`，不能直接支撑 PRD。
- 浏览器实测和官方当前页面优先级高于第三方总结。
- 社区评论能说明痛点信号，但样本偏差必须标注。
- GitHub star 不能单独证明项目可用，必须结合 commit、issue、license、demo 或代码质量。
- 论文结论不能直接推出产品需求，必须映射到用户/场景/指标。

## 用户确认规则

必须在以下节点停下来确认，不能自动推进：

1. Phase 0：目标/痛点/成功标准，或用户接受假设。
2. Phase 2 → Phase 3：用户选择要深入的方向。
3. Phase 3：强问题是否足够清楚，或用户是否接受 unresolved risk。
4. Phase 4：MVP / Future / Out of Scope 边界。
5. Phase 5：PRD/brief 确认。

如果用户明确说"你先按你的判断推进"，可以继续，但必须把关键假设标为待确认。

## Output format

### 给用户看

```text
我建议做 [X]。

目标用户：[...]
痛点 / 决策：[...]
本轮证据地图：[看了哪些块，没看哪些块]
最关键证据：[2-4 条，带置信度]

推荐方向：
1. ...

MVP：
1. ...

不做：
1. ...

未来：
1. ...

验收标准：
1. ...

风险：
- 已验证：...
- 待验证：...

下一步：
- 需要你确认 ...
```

### 给自己记

```text
research_map.md
backend_plan.md
source_log.md
evidence_table.md
assumptions_log.md
brainstorm_options.md
grillme_handoff.md
narrowed_evidence_mapping.md
PRD.md / discovery_note.md / decision_brief.md / evidence_brief.md
```

## Tools

### 直接工具

| 工具 | 用途 |
|---|---|
| `WebSearch` | 找入口、候选、关键词、市场/社区线索 |
| `WebFetch` | 读取具体网页、文档、定价页、报告 |
| Browser / opencli | 打开页面、点 UI、确认功能、观察 demo、截图 |
| `Agent` | 并行扫描多个方向或多个证据泳道 |
| `Write` | 写 PRD、brief、证据文件 |
| `Edit` | 修改已有 PRD/brief |
| `Bash` | 运行本地脚本或工具 |
| `AskUserQuestion` | 关键阶段门确认 |

### 可调用 skill

调用前判断是否满足触发条件。调完必须把产物接回来整理，不能把原 skill 输出直接丢给用户。

| Skill | 何时调 | 接回来怎么用 |
|---|---|---|
| `source-intake` | 用户给 URL/PDF/文件/资料包，或需要先读具体材料 | 摘关键发现进 evidence_table |
| `web-scrape` | 需要从网页批量提字段、抓列表、抓价格/评论/产品目录 | 产出字段表和 manifest，标为 `structured_scrape` |
| `harvest-tool` | 用户要找 GitHub 可借鉴项目 | 形成"直接借/改造借/只参考/不抄"和开源活跃度证据 |
| `idea-to-research` | 想法太模糊，不确定走 GitHub/产品/信息调研哪条 | 把路线判断整理进 Research Map |
| `methodology-distiller` | 用户不懂 PRD、前端、后端、数据、架构、UX、brainstorm 或验收方法时 | 形成方法选择、方案对比、推荐默认值、PRD 插入项、附录/ADR/evidence note |
| `research` | 需求具体，要系统性竞品/学术/综合模板 | 摘结果进 evidence_table，不直接给原报告 |
| `academic-deep-research` / paper skills | 明确论文、纳排、综述、SOTA、研究空白 | 把候选论文、筛选、证据表接回本层 |

### 调用原则

1. 能轻量完成就不启动重工具。
2. 能用单页阅读解决就不爬。
3. 需要真实页面状态时必须浏览器实测，不能只看搜索摘要。
4. 需要多对象字段比较时用结构化抓取，不手抄一堆页面。
5. 工具失败要降级：浏览器失败 → WebFetch；WebFetch 失败 → 搜索缓存/摘要；仍失败 → 标注不可验证。
6. 所有工具产物都要回填 evidence_table 和 narrowed_evidence_mapping。

## Smoke prompts

用这些 prompt 检查本方法层是否执行稳定：

1. **竞品官网调研**
   - Prompt：`帮我调研一下 AI 会议纪要工具，重点看官网功能、定价和真实 demo 能不能用。`
   - 期望：Research Plan 包含 competitors / official pages / pricing / browser observation，并写出最低证据标准；Phase 4 要求官网或 demo 核验。

2. **结构化抓取调研**
   - Prompt：`帮我比较 10 个 AI 简历工具的价格、核心功能和是否支持中文。`
   - 期望：Research Plan 包含 structured scrape 和字段定义；evidence_table 有 `structured_scrape`；不能只写搜索摘要。

3. **开源 + 官网混合调研**
   - Prompt：`帮我找能借鉴的开源 RAG UI 项目，同时看它们有没有在线 demo 和文档。`
   - 期望：GitHub 只是一个泳道；还要 browser/page verification；GitHub star 不能单独作为可借依据。

4. **轻量问题**
   - Prompt：`简单解释一下 RAG 是什么。`
   - 期望：直接答，不进入正式 research-layer-v2。

## Safety

1. 不主动输出 consensus.md。
2. 证据包不给用户看，除非用户主动要。
3. 用户必须在关键阶段门确认或接受风险：方向选择、强问题风险、边界、PRD/brief。
4. 不能说"我觉得"，必须说"基于 A、B、C，我认为"。
5. 每个关键结论都标注置信度。
6. 搜索摘要不能当高置信证据。
7. 没有 Narrowed Verification，不能写 PRD。
8. 开源项目调研不能默认主导所有调研；它只是证据泳道之一。
