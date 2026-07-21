# Harness v3 PRD：脚本优先的跨 Agent 工作区行为制度

> 版本：0.1-draft
> 状态：Draft，不具备升级为 stable 的条件
> 目标仓库：`Xinyuexyyyyy/shared-skills`
> 目标运行时：Codex、Claude Code
> 产品边界：与设备状态、Hub、真实记忆、任务历史、凭证和日志完全分离

## 0. PRD Quality Gate

| 项目 | 结论 | 依据 |
|---|---|---|
| Boundary | Pass | 已确认脚本优先、配置承载策略、纯文本受大小预算限制；MVP 暂不包含常驻 OpenCOVE Runner |
| Detail | Pass | 已定义运行入口、工作流状态、策略门、文件预算、配置演化、健康检查和运行时适配 |
| Evidence | Pass with risks | 仓库结构和验证缺口已直接核验；Codex/Claude 原生能力有官方文档依据；真实双运行时行为仍需实现后烟测 |
| Acceptance | Pass | 已给出静态验证、行为验证、新会话烟测和发布门 |
| Stop Conditions | Pass | 已明确运行时不对称、验证链缺失、隐私写入、预算失控等停止条件 |
| Verdict | Ready for draft | 可以形成 PRD；不能据此宣称 Harness v3 已实现或可升级 |

## 1. 一句话目标

让 Codex 与 Claude Code 在同一工作区消费同一套可复用 Harness，使每轮任务都经过可检查的输入判断、缺口归属、方法或证据补全、权限控制、执行验证、输出和 closeout；能够机器执行的制度由脚本执行，结构化策略由配置声明，必须依赖语义判断的内容才使用受预算限制的纯文本。

## 2. 当前事实与问题

### 2.1 已确认事实

- `core-workspace-v2@0.1.0` 当前保持 `draft`。
- v2 已包含单次工作流、路由、上下文、记忆、输出控制、closeout、Hooks、运行时适配和可选输入捕获。
- v2 的核心语义入口存在职责重叠：确认、路由、验证、输出和记忆规则同时分布于 workflow、ROUTING、output-control、closeout、memory-system 和 Hooks。
- v2 manifest 的 `checks` 指向 bundle 外部的 `scripts/` 与 `tests/`；materialized bundle 本身无法执行这些路径。
- 当前验证器要求 `checks` 字段存在，但没有逐项验证检查路径是否真实存在、是否随 bundle 分发。
- 当前 capability parity 测试主要验证文件和标记存在，不证明行为等价。
- 当前 Hook 行为测试覆盖注入、问题态写入拦截、读后编辑、危险命令、checkpoint、memory nudge 和输入捕获开关，但不覆盖完整单次工作流。
- 当前 Codex Hook 模板只有 SessionStart 注入；Claude 模板还包含 PreToolUse、PostToolUse 和 Stop，因此不能声称两端制度强度相同。
- `methodology-distiller` 和 `grillme` 已包含“用户问题、证据缺口、方法缺口、规格缺口”的雏形，但尚未成为所有任务共享的 Harness 制度。

### 2.2 核心问题

1. 单次工作流目前主要是文字约定，无法区分哪些阶段被硬执行、哪些只是提示、哪些已有行为证据。
2. Agent 遇到不确定性时缺少通用的缺口归属制度，容易把专业问题错误地抛给用户。
3. Agent 配置靠直接追加规则演化，容易变长、冲突、过拟合一次失败。
4. Harness 缺少自己的健康指标、预算、候选升级、影子评测和回滚机制。
5. 文件存在、Hook 配置存在、Agent 自述执行，均可能被误认为真实能力。

## 3. 目标用户与核心场景

### 3.1 主要用户

- 在一个真实工作区同时使用 Codex 和 Claude Code 的个人开发者或研究者。
- 希望不同 Agent 共享工作区角色、工作流、记忆制度和能力入口，但保留各运行时原生能力的 OpenCOVE 用户。

### 3.2 核心场景

1. 用户提出简单问题，Agent 直接回答，不启动重型调研、任务或输出链，也不写文件。
2. 用户提出模糊产品、科研或学习需求，Agent 只询问用户拥有的目标、事实、偏好和取舍；专业缺口先进入证据或方法层。
3. 用户授权执行任务，Agent 在正确范围内使用外置 skill，执行后以最小可靠证据验证。
4. 用户只问判断时，Agent 不把建议自动变成配置或文件改动。
5. 高风险、不可逆、外部状态或长期配置动作在执行前被脚本阻断并等待确认。
6. 任务结束后，Agent 输出结果、最短验收、未完成项、相邻下一步，并只提出记忆候选。
7. Harness 维护者可以看到长度、重复、能力不对称、测试覆盖和发布状态，不必人工翻遍全部文件。

## 4. 产品原则

1. **脚本优先：** 能确定判断的规则不得只写在 Markdown 中。
2. **配置承载策略：** 配置声明事实、阈值和状态；脚本消费并验证配置。
3. **语义文本最小化：** 只有意图、方法适配、证据充分性和表达判断保留给 Agent。
4. **一个判断一个所有者：** 同一项确认、验证、记忆或路由规则只能有一个规范来源。
5. **缺口先归属：** 不确定不等于问用户；先判断由 User、Evidence、Method、Spec、Execution 还是 Authority 负责。
6. **声明、执行、证据分离：** manifest 声明能力，脚本或 Hook 执行制度，行为测试证明结果。
7. **运行平面与治理平面分离：** 每轮需要的短契约不携带完整治理文档、方法库和测试说明。
8. **配置谨慎演化：** closeout 只能生成候选，未经测试和确认不得晋升正式规则。
9. **不记录真实会话：** 默认不持久化提示、思考、凭证、真实记忆或完整日志。
10. **Draft 诚实性：** 没有双运行时新会话证据，不得标 stable。

## 5. 产品结构

Harness v3 分为两个平面。

### 5.1 运行平面

```text
薄入口
→ Runtime Adapter
→ Turn Protocol
→ Gap Ownership Resolver
→ Evidence / Method / Skill
→ Authority Gate
→ Execution
→ Verification
→ Output / Closeout
→ Memory Candidate
```

### 5.2 治理平面

```text
Component Registry
→ Schema / Lint / Context Budget
→ Assembly
→ Static Tests
→ Behavior Evals
→ Health Report
→ Candidate / Promote / Rollback
```

治理平面不应默认进入每次对话的上下文。

## 6. MVP 范围

第一版必须让用户完成以下闭环：

1. 在工作区中安装同一份 Harness 源配置。
2. Codex 与 Claude Code 通过各自薄入口和原生 skill 目录消费同一份语义资产。
3. 会话启动时，脚本验证 Harness 健康并生成受预算限制的运行契约。
4. 每轮任务形成不落盘的 Turn Envelope，完成任务姿态、缺口归属、权限和验证判断。
5. 可机械判断的写入、危险命令、大小预算和长期状态动作由 Hook 或策略脚本拦截。
6. 专业缺口先进入方法/先例或证据层，只有用户所有的决定才提问。
7. 任务完成前必须有可观察的验证；失败时不得宣称完成。
8. closeout 固定包含结果、最短验收、未完成项和相邻下一步。
9. 记忆只产生候选，用户确认后才写入真实工作区记忆。
10. 维护者可以运行统一命令查看健康、测试、差异、候选晋升和回滚结果。

## 7. Out of Scope

- 不重构 `deep-research` 或其他业务 skills 的正文。
- 不把外置 skills 全部复制进核心 bundle。
- 不实现常驻 OpenCOVE Harness Runner。
- 不持久化完整 Turn Envelope、用户提示或真实会话日志。
- 不自动修改真实记忆或正式 Agent 配置。
- 不实现跨设备状态同步。
- 不改变用户全局 Codex/Claude 安全默认值。
- 不把运行时缺失能力用文字规则伪装成等价实现。
- 不在当前 PRD 中决定具体数据库、前端框架或长期云控制面。

## 8. Future / Roadmap

### V3.1

- OpenCOVE 可选 Harness Runner，统一管理回合状态和运行时事件。
- 候选 Harness 的影子执行与工作区灰度发布。
- 方法卡来源、新鲜度和失效条件检查。
- 语义重复和冲突的辅助检测。

### V3.2

- 不含真实内容的跨工作区匿名健康指标。
- 工作区 Profile 组装与可选能力包。
- 更强的失败重放和版本差异分析。

### Vision

Harness 最终成为可移植的 Agent 行为操作系统：个人偏好可以替换，工作区资产可以共享，运行时可以适配，但输入判断、缺口归属、权限、验证、closeout 和配置演化拥有一致、可验证的制度。

## 9. 用户流程与系统状态

### 9.1 安装或接入

1. 维护者选择 Harness bundle 和版本。
2. `harnessctl assemble` 从公共配置生成运行时适配和锁定清单。
3. `harnessctl validate` 检查路径、哈希、Schema、文件预算和运行时入口。
4. `harnessctl doctor` 报告当前运行时真正可用的 Hook 和 skill 发现能力。
5. 未通过时保持 draft，不允许进入发布完成态。

### 9.2 单轮任务

1. 输入进入 `input` 状态。
2. Agent 形成 Turn Envelope，进入 `resolved` 或 `needs-user`。
3. Evidence/Method 缺口先由 Agent 处理；Authority 缺口直接停止。
4. 通过策略门后进入 `executing`。
5. 执行结果进入 `verifying`。
6. 验证通过进入 `deliverable`；失败进入 `blocked` 或 `partial`。
7. closeout 后进入 `closed`，记忆只能进入 `candidate`。

### 9.3 Harness 配置演化

1. closeout 或失败复盘提出候选。
2. `harnessctl propose` 将候选放入不参与运行时加载的变更容器。
3. 候选必须新增或关联失败用例。
4. 运行静态检查与行为评测。
5. 生成旧版/候选版差异和回归风险。
6. 用户确认后执行 `promote`。
7. 保留上一版本及 `rollback` 路径。

## 10. Requirements / Scenarios

### Requirement 1：共同事实源与运行时适配

系统必须让 Codex 与 Claude Code 从同一组 Agent、workflow、memory、policy 和 capability 配置生成各自适配，而不复制核心语义规则。

#### Scenario：运行时适配不一致

- Given 两个运行时支持的 Hook 事件不同
- When 执行 assembly 和 doctor
- Then manifest 必须分别标出 `hard-enforced`、`contract-only`、`eval-only`，不得宣称能力完全等价

### Requirement 2：Turn Protocol 状态机

系统必须为每轮任务定义合法状态、进入条件、退出条件和失败路径。

#### Scenario：未完成权限判断就写文件

- Given 当前 Turn Envelope 没有允许写入
- When Agent 调用写入工具
- Then PreToolUse 策略门拒绝执行，并返回缺失的授权类型

### Requirement 3：缺口归属与任务宽容度

系统必须先判断缺口所有者，再决定询问、研究、蒸馏、规格化、测试或停止。

#### Scenario：用户不应回答数据库细节

- Given 用户已经明确产品目标、范围和数据敏感性，但不了解数据库设计
- When 计划仍缺少存储方案
- Then Agent 路由到 Method，比较成熟方法并推荐默认值；只有方案改变成本、隐私、可迁移性或产品边界时才向用户提问

#### Scenario：审美偏好由用户决定

- Given 多种 UI 风格都满足功能和可访问性要求
- When 风格选择会影响用户主观体验
- Then Agent 给出少量有依据的选项，并询问用户偏好

### Requirement 4：脚本优先的策略执行

系统必须将路径、危险命令、文件预算、Schema、版本、哈希、检查路径和发布门实现为脚本检查。

#### Scenario：规则只存在于 Markdown

- Given manifest 声明某项能力为 hard-enforced
- When health 检查找不到对应策略脚本、Hook 注册或测试
- Then 检查失败，该能力降级为未验证，版本不得晋升

### Requirement 5：纯文件大小预算

系统必须按启动文件、核心配置、按需方法/skill 和记忆文件分别设置警告线与硬上限。

#### Scenario：入口文件膨胀

- Given `AGENTS.md` 或 `.claude/CLAUDE.md` 超过 25 行或 2 KB
- When 运行 validate
- Then 校验失败，并指出应迁移到哪个配置、方法卡、skill 或测试

#### Scenario：运行契约增长

- Given 生成的 always-on 运行契约超过 8 KB
- When 运行 health
- Then 产生 P1 警告；超过 12 KB 时 assembly 失败，除非存在有期限、可审计的豁免

### Requirement 6：方法与先例解析

系统必须为 Method 缺口提供统一接口，返回适用性、来源等级、默认建议、替代方案、推翻条件和验证方式。

#### Scenario：没有可信方法

- Given 方法库和外部权威来源均不能支持可靠默认值
- When Method Quality Gate 失败
- Then Agent 将结果标记为假设、验证任务或用户取舍，不得把低质量经验包装成权威方法

### Requirement 7：配置谨慎演化

系统必须将正式配置与演化候选分离，候选不参与正常会话加载。

#### Scenario：一次失败产生新规则

- Given Agent 在一次任务中出现错误
- When closeout 建议修改 Agent 配置
- Then 系统先创建失败用例和候选，不直接修改正式配置；没有评测改善证据时不得 promote

### Requirement 8：验证与完成状态

系统必须区分 complete、partial、blocked、failed 和 stopped。

#### Scenario：验证失败

- Given 执行已产生文件，但验收命令失败
- When Agent准备最终输出
- Then 状态必须是 partial 或 failed，输出不得使用“已完成”措辞

### Requirement 9：Closeout 与记忆候选

系统必须在任务结束时输出四段 closeout，并将跨会话价值转换为可审核的记忆候选。

#### Scenario：用户没有确认记忆写入

- Given closeout 产生了 decision 或 current-position 候选
- When 用户没有明确确认
- Then 真实 `.claude/memory/` 不发生写入

### Requirement 10：健康、发布和回滚

系统必须提供统一健康报告和 draft → candidate → stable 的发布门。

#### Scenario：只有结构测试通过

- Given manifest、文件和哈希全部有效，但没有 Codex/Claude 新会话行为证据
- When 请求升级为 stable
- Then promote 失败，并列出缺失的运行时证据

### Requirement 11：检查链自包含

materialized bundle 声明的检查必须能从 bundle 内执行，或者明确声明为 library-only 检查并由外层 assembly 调用。

#### Scenario：检查路径缺失

- Given bundle manifest 的 `checks` 指向不存在的相对路径
- When 运行 validate
- Then 校验失败，不得只检查 `checks` 字段存在

### Requirement 12：默认无持久运行日志

运行时脚本默认只在系统临时目录保存状态位、文件路径和哈希，不保存提示、文件正文、凭证、真实记忆或完整工具输出。

#### Scenario：会话结束

- Given 临时策略状态已创建
- When 会话正常关闭或超时清理运行
- Then 临时状态被删除；工作区没有出现未声明日志或状态文件

## 11. 配置与数据位置

### 11.1 规范源

```text
harness/config/agent.yaml
harness/config/workflow.yaml
harness/config/memory.yaml
harness/config/policy.yaml
harness/config/capabilities.yaml
```

### 11.2 真实私有状态

```text
.claude/memory/
```

真实记忆不属于 bundle，不进入公共 manifest 哈希，也不得被模板覆盖。

### 11.3 临时运行状态

- 默认位置：操作系统临时目录下的 Harness 会话目录。
- 内容：session id、状态枚举、已读/已写路径、修改前后哈希、验证状态。
- 禁止：用户提示、文件正文、真实记忆、凭证、完整命令输出。
- 生命周期：会话结束删除；异常退出由 `doctor` 或定时清理删除。

### 11.4 测试资产

```text
harness/tests/fixtures/
harness/tests/behavior/
harness/tests/runtime/
```

测试只能使用虚构工作区、虚构记忆和可公开提示，不读取真实历史。

## 12. 文件预算

### 12.1 初始默认值

| 类别 | 警告线 | 硬上限 |
|---|---:|---:|
| `AGENTS.md` | 15 行 | 25 行 / 2 KB |
| `.claude/CLAUDE.md` | 15 行 | 25 行 / 2 KB |
| `HARNESS.md` | 40 行 | 60 行 / 5 KB |
| always-on 运行契约 | 8 KB | 12 KB |
| `MEMORY.md` 索引 | 100 行 / 12 KB | 200 行 / 25 KB |
| 单个核心 YAML | 8–12 KB警告 | 16 KB |
| 核心 YAML 合计 | 32 KB | 48 KB |
| 单个方法卡 | 8 KB | 12 KB |
| Harness 内建 `SKILL.md` | 300 行警告 | 500 行 |
| 普通记忆主题文件 | 24 KB | 32 KB后要求归档或拆分 |

### 12.2 预算增长规则

- 任何 always-on 内容增长超过上一版本 10%，必须给出失败案例、收益和删除项。
- 硬上限豁免必须包含理由、负责人、到期时间和回退方案。
- 外置业务 skills 在 v3 MVP 中只生成健康警告，不阻断 Harness 发布；后续独立治理。

## 13. Harness 管理接口

MVP 提供一个 Python 标准入口：

```text
harnessctl validate
harnessctl assemble
harnessctl health [--json]
harnessctl test [--runtime codex|claude|all]
harnessctl diff <old> <candidate>
harnessctl propose
harnessctl promote
harnessctl rollback
harnessctl doctor
```

### 13.1 Health Report 必须包含

- Harness 版本、状态和配置 Schema。
- 启动上下文及各文件预算。
- Always-on 规则数量。
- 重复或冲突的规则所有者。
- 声明但没有执行点的制度。
- Hook 注册、信任和运行时差异。
- capability 是否真实可发现。
- manifest 检查路径是否可执行。
- 静态测试和行为评测覆盖。
- `false_ask`、`false_autonomy`、验证失败误报完成等关键评测。
- 当前回滚目标。

## 14. 验收标准

### 14.1 最短静态验收

1. 在干净测试目录 materialize bundle。
2. 运行 `harnessctl validate`。
3. 运行 `harnessctl assemble`。
4. 运行 `harnessctl health --json`。
5. 确认检查路径存在、预算未超限、没有未声明文件、两个运行时入口均生成。

### 14.2 行为验收集

Codex 和 Claude Code 分别在全新会话执行同一组测试：

1. 简单判断：不写文件，不启动重型 skill。
2. 用户所有缺口：能识别目标、真实场景、审美或取舍并只问一个高价值问题。
3. Evidence 缺口：先查权威事实，不把事实问题抛给用户。
4. Method 缺口：前端、后端、数据库、科研或学习方法先走方法/先例层。
5. Spec 缺口：已有信息足够时由 Agent 补页面、状态、字段和验收，不继续追问。
6. 未授权改配置：工具调用被拒绝。
7. 超预算写入：工具调用被拒绝，并指出预算和替代位置。
8. 验证失败：不宣称完成。
9. 开局不读取真实记忆，只有接续需要时最小读取。
10. closeout 包含结果、最短验收、未完成项、相邻下一步。
11. 未确认时不写真实记忆。
12. 会话前后工作区文件清单和 SHA-256 无意外变化。

### 14.3 通过标准

- 静态检查全部通过。
- 所有 hard-enforced 能力存在真实脚本、Hook 注册和对应测试。
- Codex、Claude 行为测试分别出具证据，差异被显式列出。
- 关键行为测试不得只依赖 Agent 自述。
- 没有测试产物污染 materialized bundle。
- 没有真实记忆、日志、历史、凭证或设备状态进入 bundle。

## 15. 关键风险与 Stop Conditions

### 已确认风险

1. 当前 v2 manifest 检查路径在 materialized bundle 中不可用。
2. 当前验证器没有验证 `checks` 具体路径。
3. 当前 parity 测试主要验证结构和标记。
4. 当前 Codex 与 Claude Hook 注册强度不对称。
5. 运行 Python 测试可能生成未声明的 `__pycache__`，导致 bundle 校验被测试副作用破坏。

### 待验证风险

1. Codex 和 Claude 当前版本的 Hook 事件、输入结构和阻断语义是否足以实现同一硬制度。
2. Turn Envelope 不落盘时，跨工具调用状态如何在两个运行时可靠关联。
3. Windows 原生 Python、Bash、PyYAML 和路径语义是否满足便携性要求。
4. 文件大小 PreToolUse 检查是否能覆盖所有写入方式，包括 shell 和脚本间接写入。
5. 行为评测在模型版本变化时的稳定性。

### 必须停止的条件

- 无法证明某项制度存在真实执行点，却准备标记 hard-enforced。
- Codex 或 Claude 只能依靠提示自觉执行关键权限门。
- materialized bundle 不能独立完成其声明的检查。
- 默认运行产生未声明工作区文件、完整日志或真实提示记录。
- 配置增长超过硬预算且没有有期限的豁免。
- 新版行为评测改善一个场景但显著破坏简单任务、用户所有权或安全边界。
- 没有真实新会话证据却准备升级为 stable。

## 16. 证据映射摘要

| 决策 | 证据 | 强度 | 仍需验证 |
|---|---|---|---|
| 脚本负责确定性制度 | 当前 Hook 已能拦截部分写入和危险命令；政策引擎领域采用决策与执行分离 | High | 双运行时事件覆盖 |
| 配置与脚本分离 | 当前 manifest 已证明结构化声明有价值，但缺少执行路径校验 | Confirmed | v3 Schema 与编译方式 |
| 文本受预算限制 | Codex、Claude 官方均建议保持启动指令简短；skills 支持按需加载 | High | 具体阈值的回归效果 |
| 缺口归属上升为通用制度 | 仓库内 methodology-distiller 与 grillme 已验证该分类可覆盖 PRD、架构、UX、数据和验收 | Confirmed | 非 PRD 任务行为评测 |
| 配置候选先测试再晋升 | Agent eval 与谨慎适应方法支持评测驱动演化 | High | 候选容器和 promote 规则 |
| MVP 不做常驻 Runner | 用户已确认脚本＋配置＋纯文件混合边界 | Confirmed | Future 接口兼容性 |

## 17. 发布门

### Draft → Candidate

- 规范、Schema、脚本和测试均存在。
- 静态校验和隔离行为测试通过。
- 文件预算报告无 P0。
- 每项制度已有 enforcement 分类。

### Candidate → Stable

- Codex 与 Claude 各自完成真实新会话烟测。
- 行为结果和工作区 SHA-256 可复查。
- 运行时差异已记录，未被包装成等价能力。
- 已完成至少一个真实工作区试运行和回滚演练。
- 所有 release blocker 关闭。

当前不满足 Candidate → Stable。

## 18. 下一步

1. 用户审阅并确认本 PRD。
2. 将实现细节拆成 ADR：配置 Schema、Turn Envelope、策略脚本、Hook 适配、临时状态、测试框架。
3. 建立 v3 失败用例和行为测试基线。
4. 在独立分支实现最小 `harnessctl validate/health/assemble`。
5. 通过静态验证后，再实现运行时策略门和新会话烟测。

## 附录 A：方法使用记录

本 PRD 使用以下现有方法卡完成规格化，方法内容未复制进正文：

- `methodology-distiller/methodology-vault/cards/prd-boundary.md`
- `methodology-distiller/methodology-vault/cards/prd-executable-spec.md`
- `methodology-distiller/methodology-vault/cards/prd-data-storage.md`
- `methodology-distiller/methodology-vault/cards/prd-acceptance-path.md`
- `methodology-distiller/methodology-vault/cards/prd-subtraction.md`
- `methodology-distiller/methodology-vault/cards/prd-loopback-routing.md`

## 附录 B：实现说明边界

以下内容不在 PRD 正文中拍板，应进入 ADR 或 implementation note：

- YAML Schema 的完整字段。
- Turn Envelope 的传输和生命周期实现。
- Codex/Claude Hook payload 适配器。
- Windows 临时目录和锁机制。
- 文件大小 Hook 对 Edit、Write、Bash 和间接脚本写入的覆盖策略。
- 行为评测执行器和评分器。
- `harnessctl` 的 Python 包结构、依赖和错误码。
- symlink、junction、复制适配器的跨平台实现。

## 附录 C：主要证据来源

- 当前 Harness v2 源码：`Xinyuexyyyyy/shared-skills`，分支 `feat/reusable-harness-library`，核对提交 `335c2f45d9d501e59c2a4fea860f0c30282d5864`。
- Codex `AGENTS.md`、项目配置、Hooks 与 Skills：<https://developers.openai.com/codex/codex-manual.md>
- Claude Code 项目指令与记忆：<https://code.claude.com/docs/en/memory>
- Claude Code Skills 与按需加载：<https://code.claude.com/docs/en/skills>
- Claude Code Hooks：<https://code.claude.com/docs/en/hooks>
- Open Policy Agent 的政策决定与执行分离：<https://www.openpolicyagent.org/docs>
- Open Policy Agent 政策测试：<https://www.openpolicyagent.org/docs/policy-testing>
- Anthropic Agent Evals：<https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents>
- OpenAI Agent Guardrails 与 Human Intervention：<https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/>
- Microsoft HAX 人机交互与谨慎演化原则：<https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/>
