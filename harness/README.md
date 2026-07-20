# Reusable Harness

## Harness v3 第一阶段：脚本优先治理基础

`core-workspace-v3@0.1.0+draft` 是 v1/v2 之外的新增治理层，不删除也不替换旧 bundle。v3 将 Agent、workflow、memory、policy 和 capability 分成五个独立 YAML 配置域；Markdown 只保留运行时入口的短语义契约。

从仓库根目录运行：`python harness/harnessctl validate`、`python harness/harnessctl assemble`、`python harness/harnessctl health --json`、`python harness/harnessctl doctor`。Windows 也可使用根目录的 `harnessctl.cmd`。

`validate` 检查 Schema、assembly、manifest 文件和 SHA-256、bundle 内外 checks、预算、legacy draft 与 hard-enforced 证据；`assemble` 确定性生成 v3 bundle；`health` 输出预算、能力分类、测试状态、release blocker、候选资格、稳定资格和回滚目标；`doctor` 只检查当前仓库可证明的运行环境与模板。

当前 v3 已实现配置 Schema、确定性 assembly、manifest/检查路径校验、文件与文本预算、健康报告、静态负向测试、行为 fixture 和 draft 发布门。Codex/Claude 的 Turn Protocol 目前是 `contract-only`，真实新会话行为是 `unverified`；没有两端新会话证据时，`stable_eligible` 必须为 `false`。

manifest 声明的 check 会在只读临时/仓库上下文中实际执行并记录退出码；只检查路径存在不算通过。runtime evidence 在第一阶段没有受信评测器时固定为 `unverified`，手工把 JSON 改成 `passed` 不会获得发布资格。health 在结构校验失败时返回非零退出码，`--allow-unhealthy` 仅用于明确的诊断调用。

v3 回滚目标为 `core-workspace-v2@0.1.0+draft`。第一阶段不重构业务 skills、不持久化 Turn Envelope、不启用输入捕获，也不修改全局 Agent 配置。

本目录是可复用 agent 运行规则的权威入口。它统一管理 agent 如何理解输入、选择能力、执行、验证、输出、维护工作区记忆及适配不同运行时。其中，**单次输出工作流不是建议文案，而是核心 bundle 的强制执行契约**。

## 1. 定位

Harness 位于模型能力和具体任务之间，负责解决：

- 同一套工作方法可以在不同工作区复用。
- Codex 与 Claude 消费同一份核心规则，不各自维护分叉正文。
- 输出控制、上下文加载、记忆维护、验证和收尾形成闭环。
- 工作区只保存私有状态，通用方法集中管理并版本化。
- 发布物可以独立校验、存储、恢复和迁移。

领域 skill 决定“某类任务怎么做”，Harness 决定“agent 收到任何任务后按什么制度运行”。

## 2. 权威边界

本目录负责：

- 单次输出工作流。
- 输出控制和防过度执行规则。
- 路由与上下文加载规则。
- 工作区私有记忆的方法、空模板和维护工具。
- 完成后的 closeout 规则。
- 不同运行时的接入适配器。
- Bundle 的 manifest、版本、校验和发布约定。
- 可直接复制验证的示例工作区。

本目录不负责：

- 具体项目的真实记忆、任务历史和决策内容。
- 跨设备任务状态、设备信息和协作进度。
- 凭证、账号、网络地址及机器专属配置。
- 领域 skill 的完整实现和运行依赖。
- 运行时本身的安装与全局私有配置。
- 未经明确启用的用户输入捕获。

跨设备公共状态与工作区私有记忆必须分开。Harness 只提供工作区记忆制度，不携带任何真实记忆数据。

## 3. 目录地图

```text
harness/
├── README.md
├── METHODOLOGY.md
├── MANIFEST-SPEC.md
├── components/
│   ├── output-control/
│   ├── routing-context/
│   ├── memory-system/
│   ├── workflow/
│   ├── closeout/
│   ├── runtime-adapters/
│   │   ├── codex/
│   │   └── claude/
│   └── input-capture/
├── assemblies/
│   ├── core-workspace-v2.yaml
│   └── core-workspace-v3.yaml
├── bundles/
│   ├── runtime-baseline/
│   ├── core-workspace-v1/        # 历史摘要版，只保留校验快照
│   ├── core-workspace-v2/        # 当前完整迁移草稿
│   └── core-workspace-v3/        # 脚本优先治理基础，仍为 draft
├── examples/
│   └── livewithopencove-workspace/
├── scripts/
└── tests/
```

| 路径 | 职责 |
|---|---|
| `METHODOLOGY.md` | Harness 的设计原则、边界和演进方法 |
| `MANIFEST-SPEC.md` | Bundle manifest 的字段、版本和校验规范 |
| `components/` | 唯一可手工修改的通用机制源文件 |
| `assemblies/` | 声明 bundle 由哪些源组件、版本和策略组成 |
| `bundles/` | 从 assembly 物化出的可发布副本，带文件校验值 |
| `examples/` | 自包含示例和最短接入路径 |
| `scripts/` | Bundle 物化、结构检查和校验工具 |
| `tests/` | 结构检查、负向测试和运行时烟测 |

维护时只改 `components/` 和 `assemblies/`，不要手工修改 `core-workspace-v2/` 或 `core-workspace-v3/` 内的生成文件。Bundle 和示例副本由物化命令重新生成，校验会拒绝源组件与发布副本不一致的状态。v1 的旧 assembly 已归档，防止历史摘要版被新组件原地重建。

## 4. 核心组件

### Output Control

包含完整 `SKILL.md`、`TWO-STAGE.md`、文档渲染验收、长会话触发稳定性、写入前二审和四段交付；同时提供注入器、危险命令、先读后改、过度执行和两段制提醒 hooks。

### Routing Context

包含完整路由表与 `CONTEXT-SPEC`；负责判断直接回答、skill、工具或完整流程，按需加载上下文，并在调用前确认目标能力真实可发现。

### Memory System

采用 LiveWithOpenCove 的完整空模板、归档模板和维护方法，并带 `memory_gc`、`lessons_gc`、`check_map`、`organize`、checkpoint 与记忆提醒。真实记忆永远留在工作区。

### Workflow

负责把一次用户输入变成一次可验证、可收尾的完整运行。核心 bundle 必须强制引用该组件，运行时适配器不得删除、调序或改写其阶段语义。

### Closeout

包含完整 closeout skill 与扩展说明，覆盖完成、部分完成、失败、阻塞、叫停、证据预算和可选记忆候选；未经人工确认不得写入长期记忆。

### Runtime Adapters

负责把同一 bundle 接入 Codex 与 Claude 的原生规则入口、skill 入口和 hook。适配器只处理“如何接入”，不得维护另一份核心规则正文。

### Input Capture

输入捕获的适配器、桥接器、敏感信息过滤和本地记录器随 v2 提供，但默认关闭、未注册、零写入。显式启用后只写当前工作区 `.claude/capture/`，不得自动建任务或写长期记忆。

## 5. 单次输出工作流制度

### 5.1 强制契约

每次真实用户输入都必须经过以下固定顺序：

```text
输入洁净
-> Digest
-> 宽路由
-> 主题提示适配
-> 产物闸
-> 执行
-> 验证
-> 输出控制
-> closeout
-> 灵感旁路（仅人工触发）
```

制度要求：

- 阶段不得跳过，但允许输出“本阶段无需动作”。
- 无人工触发时，灵感旁路必须关闭。
- 运行时可以增加内部实现步骤，但不得改变阶段语义。
- 任何适配器都不得把执行放到产物闸之前。
- 未通过验证时，不得在输出控制或 closeout 中宣称完成。
- 单次输出工作流必须进入 bundle manifest 和发布验收，不得只写在提示词里。

### 5.2 阶段契约

| 阶段 | 输入 | 必须产出 | 暂停或停止条件 |
|---|---|---|---|
| 输入洁净 | 原始输入和当前会话 | 当前请求、约束、授权和禁止事项 | 指令冲突无法消解，或缺失信息会导致高风险误执行 |
| Digest | 洁净后的输入 | 目标、范围、交付物、验收点和未知项 | 无法形成最小可回答或可执行闭环 |
| 宽路由 | Digest 和已注册能力 | 直答、skill、工具或流程的内部决定 | 必需能力不存在，或路线分叉会产生实质不同结果 |
| 主题提示适配 | 路由结果和任务领域 | 当前角色、语言、证据和输出约束 | 缺少不可推断的专业判断或关键材料 |
| 产物闸 | 拟执行动作和拟生成产物 | 允许执行、降级只读或请求确认 | 未授权写入、改变全局行为、价值不足或超出范围 |
| 执行 | 已确认范围和方法 | 回答、文件变更或明确状态变化 | 范围扩张、不可逆动作、新权限需求或重复失败 |
| 验证 | 执行结果和验收标准 | 通过、部分通过或失败的当前证据 | 无法验证时停止成功声明并标记未验证 |
| 输出控制 | 结果、证据和用户意图 | 结论、必要依据、验收和下一步 | 过度执行、过程喧宾夺主或完成状态不清 |
| closeout | 受控输出和剩余状态 | 结果、怎么验、未完成和相邻下一步 | 不得把过程数据伪装成交付，不得自动写记忆 |
| 灵感旁路 | 人工明确触发 | 可审阅的灵感或记忆候选 | 未触发时立即结束，不建文件、不建任务 |

允许的内部信号：

- `continue`：下一阶段可以继续。
- `ask`：缺少必须由用户决定的信息。
- `stop`：不应继续执行。
- `rewrite`：当前草稿必须重写。
- `verify`：必须取得最小可靠证据。
- `discard`：输入是噪声或非用户请求。
- `promote_candidate`：只提出候选，不自动写入。

### 5.3 默认行为

- 所有用户可见输出和生成产物默认使用中文；用户明确要求其他语言时再切换。
- 路由、工具链和内部判断默认隐藏。
- 写文件、改配置、持久化数据前必须通过产物闸。
- 问判断、问方法或问状态时，不自动落文件或启动完整流程。
- 用户要求执行时，动作只能发生在已确认范围内。
- 验证证据采用足以支持结论的最小量。
- 结果先于过程，用户可见效果先于技术实现。
- 灵感和长期记忆只在人工明确触发或确认后写入。
- 扩大范围、改变目标或触及高风险配置时必须暂停确认。

### 5.4 Manifest 要求

任何包含该工作流的 bundle 都必须声明：

- 工作流 ID 和契约版本。
- 固定阶段及其顺序。
- 必选组件和可选组件。
- 规则入口与运行时适配器入口。
- 记忆读写策略。
- 输入捕获是否启用。
- 权限和外部依赖。
- 结构检查、负向测试和烟测命令。
- 来源版本和文件校验值。

Manifest 与实际文件不一致时，bundle 不得发布。

### 5.5 运行时接入

每个运行时适配器必须：

1. 提供唯一规则入口并指向同一工作流契约。
2. 声明哪些阶段由 hook 执行，哪些由规则入口执行。
3. 避免同一阶段被多个入口重复注入。
4. 提供 skill 发现路径和失效入口检查。
5. 不使用机器专属绝对路径。
6. 不复制核心规则形成运行时分叉。
7. 提供可重复的启动烟测。

不支持 hook 的运行时，必须通过规则入口保持完整阶段契约，并在 manifest 中声明能力差异。

### 5.6 最低验收

1. 用户只问判断时，不产生文件变更。
2. 用户未授权修改配置时，产物闸阻止写入。
3. 用户明确要求执行时，动作不超出确认范围。
4. 路由选择的 skill 在当前运行时真实可发现。
5. 验证失败时，最终输出不会宣称完成。
6. 内部工具链不会默认淹没用户结果。
7. closeout 包含结果和最短验收方式。
8. 未触发灵感旁路时，不新增灵感、任务或长期记忆。
9. 记忆候选未经确认，不写入工作区记忆。
10. 不同运行时对相同输入保持一致的阶段语义。

## 6. 记忆系统边界

工作区私有记忆采用以下基本结构：

```text
.claude/memory/
├── MEMORY.md
├── workspace-brief.md
├── workspace-map.md
├── current-position.md
├── timeline.md
├── timeline-archive.md
├── decisions.md
├── lessons.md
├── lessons-archive.md
└── tasks/
    └── INDEX.md
```

记忆制度：

- 开局先读规则，记忆按任务需要延迟加载。
- 继续已有任务时，从索引和当前位置开始。
- 一次性问答不得无故读取完整记忆。
- 真实记忆只留在对应工作区。
- Bundle 只携带空模板、维护规则和通用工具。
- closeout 只生成候选，人工确认后才能写入。
- 不把聊天全文、原始日志或敏感数据当作长期记忆。

## 7. Bundle 与适配器

完整迁移草稿 `core-workspace-v2@0.1.0` 已包含：

```text
core-workspace-v2/
├── CAPABILITY-MAP.yaml
├── rules/
│   ├── workflow.md
│   ├── ROUTING.md
│   ├── CONTEXT-SPEC.md
│   └── memory-system.md
├── skills/
│   ├── output-control-layer/
│   └── closeout/
├── hooks/
├── tools/memory/
├── templates/memory/
├── runtime/
└── optional/input-capture/
```

`input-capture` 文件随包存在但默认关闭。修改核心制度时更新 bundle 版本；仅修改运行时接入方式时更新适配器版本。适配器不得覆盖固定工作流。

物化与一致性检查：

```bash
python3 scripts/materialize-bundle.py \
  --assembly assemblies/core-workspace-v2.yaml \
  --output bundles/core-workspace-v2

python3 scripts/materialize-bundle.py \
  --assembly assemblies/core-workspace-v2.yaml \
  --output bundles/core-workspace-v2 \
  --check
```

示例工作区的 bundle 使用同一 assembly 物化到其 `harness/bundles/` 下，不维护另一份规则源。

## 8. 最小接入

1. 选择明确版本的 bundle；试用完整迁移成果时选择 `core-workspace-v2@0.1.0` 并保留 `draft` 标记。
2. 创建工作区规则入口。
3. 接入对应运行时适配器。
4. 初始化空的工作区记忆模板。
5. 建立工作区 skill 发现入口。
6. 生成并校验 manifest。
7. 运行结构检查、负向测试和启动烟测。
8. 用示例输入验证单次输出工作流。
9. 记录 bundle 版本、来源和校验值。

```text
workspace/
├── AGENTS.md
├── .agents/skills/
├── .claude/
│   ├── CLAUDE.md
│   ├── memory/
│   └── skills/
├── harness/
│   ├── HARNESS.md
│   ├── manifest.yaml
│   ├── bundles/
│   └── skills/
└── project-files/
```

完整示例见 `examples/livewithopencove-workspace/`。

## 9. 发布与存储

- 权威内容在版本控制中维护。
- 发布物必须有明确版本，不用含义不明的“最新版”作为唯一标识。
- 已发布版本不可原地修改；修正必须发布新版本。
- 发布前必须通过 manifest 校验、结构测试、负向测试和运行时烟测。
- 发布物必须记录来源版本和文件校验值。
- 存储镜像只是已发布 bundle 的副本，不是新的编辑源。
- 发布物不得包含真实记忆、凭证、日志或设备配置。
- 示例工作区使用相对路径或可替换变量。
- 旧版本可以归档，但不得无记录删除。

## 10. 当前状态

| 内容 | 状态 |
|---|---|
| 方法、README、manifest 规范 | 已落地 |
| `core-workspace-v1@0.1.0` | 历史摘要版，保留不再扩展 |
| 完整输出控制、两段制、路由、上下文、closeout | 已进入 v2 |
| LiveWithOpenCove 记忆模板与四个维护工具 | 已进入 v2 |
| 10 个运行 hooks 与双运行时注册模板 | 已进入 v2，按 runtime 启用 |
| Input Capture 完整实现 | 已进入 v2，默认关闭 |
| `core-workspace-v2@0.1.0` | 已物化，状态为 `draft` |
| `core-workspace-v3@0.1.0+draft` | 脚本优先治理基础已实现，仍为 `draft`；Codex/Claude 真实新会话尚未验证 |
| LiveWithOpenCove 风格示例 | 已切换到 v2 |
| 结构、校验值、负向、hook、memory fixture | 已通过本机验证 |
| Win Codex、Claude v2 新会话烟测 | 待执行 |
| Win 用户根全局 Harness 接入 | 未执行，与独立示例分开处理 |
| 存储镜像草稿副本 | 已生成并完成提交号、校验值复核 |
| 正式发布版本 | 尚未发布 |

在以下条件全部满足前，不得把 `core-workspace-v3` 标记为 Candidate 或 Stable：

- Codex 和 Claude 都在新会话中读到同一 bundle ID、版本和工作流阶段。
- 问判断、未授权写入、验证失败和记忆确认四类行为烟测通过。
- 发布版本和来源提交已记录，且发布物不含真实工作区数据。
- health 报告中的预算、checks、静态测试和行为评测均无 release blocker。
- 存储镜像与本机发布提交、目录和校验值一致，并完成回滚演练。
