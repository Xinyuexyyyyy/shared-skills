# shared-skills

> 25 个 AI agent skill，按调研/任务/输出/运维四层组网。Mac 和 Win 通过 GitHub 同步同一份技能池。
> 这是 [LiveWithOpenCove](https://github.com/Xinyuexyyyyy/LiveWithOpenCove) 工作区方法的**技能引擎**——LiveWithOpenCove 管记忆和规则，这里管技能和路由。

---

## 这套东西解决什么

- Claude Code / Codex 在两个平台上各维护一份 skill，改了这头忘那头 → **GitHub 同步，一处改两边生效**
- skill 越堆越多，找不到哪个干什么 → **四层目录 + 触发词索引，一眼定位**
- 不同 agent 进来不知道哪些 skill 可用 → **每个 skill 都有 SKILL.md，agent 读了就知道怎么触发**
- 做完的事记不住、下次聊又失忆 → **跟 LiveWithOpenCove 的记忆系统咬合（closeout 收尾→建议写记忆）**

---

## 快速接入

### Claude Code

```bash
# 1. clone 仓库
git clone https://github.com/Xinyuexyyyyy/shared-skills.git ~/shared-skills

# 2. 在你的工作区建软链接（按需，不一定要全部）
mkdir -p ~/my-workspace/skills
ln -sf ~/shared-skills/deep-research ~/my-workspace/skills/deep-research
ln -sf ~/shared-skills/output-layer ~/my-workspace/skills/output-layer
# ... 按需添加其他 skill

# 3. 工作区的 .claude/skills 指向 skills/
ln -sf ~/my-workspace/skills ~/my-workspace/.claude/skills
```

### Codex

```bash
# 同上，但工作区入口不同
mkdir -p ~/my-workspace/skills
ln -sf ~/shared-skills/deep-research ~/my-workspace/skills/deep-research
# ... 

# Codex 用 .codex/skills
ln -sf ~/my-workspace/skills ~/my-workspace/.codex/skills
```

### Windows

```powershell
git clone https://github.com/Xinyuexyyyyy/shared-skills.git C:\Users\sure\shared-skills
# Win 上 Claude Code 的 skills 路径指向这里即可
```

## Mac ↔ Win 同步

```
Mac (~/shared-skills/) ── git push ──→ GitHub ── git pull ──→ Win (C:\Users\sure\shared-skills\)
       ↑                                                              │
  改 skill 在这改                                              Win 看 / 跑 skill
```

两边都能改，改了 commit + push。另一方 `git pull` 就同步。冲突就正常 resolve。

---

## Skill 目录

### 调研层 — 8 个

> 想法 → 证据 → 方法 → PRD 就绪

| Skill | 做什么 | 触发词 |
|---|---|---|
| `deep-research` | 调研总入口。Gate/Clarify → Research Map → 证据 → Brainstorm → Grillme → 验证 → PRD 就绪 | 调研、研究、竞品、产品调查、文献综述、找论文 |
| `research` | 四类模板取证包（学术/竞品/发现/全面），deep-research 内部引擎 | 用户显式点名才直达 |
| `research-layer-v2` | deep-research 的方法编排参考（Gate→Map→Evidence→Verify） | 内部方法层，不直接调 |
| `idea-to-research` | 模糊想法→路线判断→对接调研层；太模糊就停澄清层 | 有个想法、想调研但不知道从哪开始 |
| `harvest-tool` | 找 GitHub 可借鉴项目→筛成熟方案→抓资料→落共识文档 | 找 GitHub 项目借鉴、有没有类似的开源 |
| `source-intake` | URL/PDF/粘贴材料第一轮分析：是什么、讲什么、值不值得继续 | 读一下、快速读资料、整理资料 |
| `web-scrape` | URL→提取结构化数据，curl_cffi→playwright 反爬逐级升级 | 抓取、爬数据、提取字段 |
| `methodology-distiller` | grillme/PRD 中遇到专业方法缺口→提炼专家实践/方案对比/推荐默认值 | PRD 该用什么方法、MVP 和未来边界怎么定 |

### 任务层 — 7 个

> 需求 → 拆解 → 执行 → 收尾

| Skill | 做什么 | 触发词 |
|---|---|---|
| `task-analyze` | 分析用户意图，提取核心目标、约束、缺失信息 | 帮我分析下、看看这个需求、有个想法 |
| `task-decompose` | 已分析的任务拆为可执行子任务（≤5 个） | 拆任务、分解任务 |
| `task-crafter` | 复杂需求→生成结构化任务文件（TASK/state/context/artifacts/log） | 生成任务、规划任务、复杂项目 |
| `project-sop` | 项目全流程：蓝图→拆任务→开发→测试→收尾 | 新项目、brainstorm、写蓝图 |
| `grillme` | 分层诊断式提问，提交复杂方案前压力测试 | 审问我、grill me、这个方案有什么问题 |
| `workspace-init` | 一键搭工作区目录结构（调研/任务/输出三层） | 初始化工作区、init workspace |
| `workspace-tidy` | 整理跑乱的工作区，先出方案确认再移动，绝不自动删 | 整理工作区、tidy workspace |

### 输出层 — 7 个

> 内容 → 总闸 → 路由 → 成品

| Skill | 做什么 | 触发词 |
|---|---|---|
| `output-control-layer` | 输出前总闸：二审（真实意图/防过度执行）+ 规则段 + 执行步长 | 常驻注入，不显式调用 |
| `output-layer` | 公共输出路由：润色/去AI味/收紧，Obsidian/docx/pdf 成品化 | 润一下、去AI味、改得像我、输出成品 |
| `output-polisher` | 轻量排版 + Obsidian 三档导出，不改正文 | 排版、导出 Obsidian |
| `output-style-checker` | 最小规则检查：先抓硬伤，不主生成 | 检查一下、有没有问题 |
| `humanizer` | AI 痕迹专项审计：30 条 AI 写作模式检测→定向去除 | 太像 AI 了、humanize、审一下 AI 痕迹 |
| `drawio-diagram-agent` | 文字描述→紧凑 draw.io 流程图/架构图/学习路径 | 画个图、流程图、架构图、draw.io |
| `closeout` | 任务结束/暂停时产出可读总结 + 验证路径 + 记忆更新建议 | 收尾、总结一下、完事了 |

### 运维层 — 4 个

> skill 质量 → 治理 → 进化

| Skill | 做什么 | 触发词 |
|---|---|---|
| `skill-optimizer` | 锐评（8 维评分）+ 优化闭环 + 工作方式对齐 | 评测 skill、skill 评分、优化 skill |
| `skill-dashboard` | 技能仪表盘：agent 不遗忘能力，用户看得见功能 | 打开技能面板、看看我的技能、有什么 skill |
| `skill-reforge` | 从外部（GitHub/粘贴）引入 skill→验证→适配→本地化 | 引入一个 skill、这个外部 skill 能用吗 |
| `external-skill-adoption` | harvest-tool 发现外部 skill 后，决定引入/试用/本地化/拒绝 | harvest-tool 入口间接触发 |

### 在库但暂不纳入 Win 同步 — 5 个

| Skill | 做什么 | 暂不纳入原因 |
|---|---|---|
| `anchor-spark` | 创作骨架：主题→锚点池→6 种叙事切角 | 写作专用，待验证 Win 需求 |
| `debate-engine` | 两 AI 辩论→提取核心张力 | 同上 |
| `dream-catcher` | 想法对撞：半成品×锚点池×想法池→火花 | 同上 |
| `ui-design` | UI/页面/组件设计与截图验收 | 同上 |
| `web-scrape` | URL→数据抓取 | 同上 |

---

## Harness 调度：怎么决定调哪个 skill

**不是 if-else，是语义路由。** 见 [ROUTING.md](ROUTING.md)。

核心逻辑：

```
用户说人话 → agent 读 ROUTING.md 的意图话术表 → 语义匹配 → 决定调什么
```

三条原则：
1. **吝啬优先**：简单问题直接答，不路由
2. **报而后行**：路由前先说"这像【X】，我调 Y，开始？"
3. **调用目标开放**：可以是 skill、skill 链、外部命令、或"直接答"

具体匹配规则都在 [ROUTING.md](ROUTING.md) 第二章的规则表里。

---

## 记忆体系：跟 LiveWithOpenCove 的关系

**这两个仓库是一套东西的两个部分：**

| 仓库 | 管什么 | 受众 |
|---|---|---|
| [`shared-skills`](https://github.com/Xinyuexyyyyy/shared-skills)（这里） | **技能引擎**：25 个 skill、触发词、路由表、调用约定 | 你 + agent（执行层） |
| [`LiveWithOpenCove`](https://github.com/Xinyuexyyyyy/LiveWithOpenCove) | **工作区骨架**：6 文件记忆模型、规则层、写入权限、自进化经验库 | 你（组织方法） |

**记忆流向**：agent 用这里的 skill 执行任务 → closeout 收尾时建议更新记忆 → 按 LiveWithOpenCove 的 6 文件模型写入（用户确认才写）：

```
工作区的 memory/
├── workspace-brief.md     # 这个工作区是什么、做什么
├── workspace-map.md       # 活跃项目地图
├── timeline.md            # 会话流水（倒序追加）
├── current-position.md    # 当前焦点、下一步、阻塞
├── decisions.md           # 拍板决策（为什么这么做）
└── lessons.md             # 复盘经验（带 scope/计数，自进化）
```

**举例**：你在 Win 上用 `deep-research` 做了个 Ansys 调研，closeout 会提示"要不要把这次调研的结论和下一步记到 Win 工作区的 memory/ 里？"——这就把技能执行和长期记忆串起来了。

---

## 工作区怎么接这套东西

完整 setup（一台新机器）三步走：

```
1. git clone shared-skills    → 拿到所有 skill
2. git clone LiveWithOpenCove → 拿到记忆骨架 + 规则模板
3. ./LiveWithOpenCove/bin/init-workspace.sh ~/my-workspace → 搭好工作区
```

之后用 skill 的热更新：`cd ~/shared-skills && git pull`。

---

## 每个 skill 的约定

- 每个 skill 目录下必须有一个 `SKILL.md`——这是 agent 读取的唯一入口
- `SKILL.md` 里必须声明 `description`（功能一句话）、触发词、依赖的其它 skill、产出去向
- `CLAUDE.md` 是 `SKILL.md` 的软链接，兼容 Claude Code 的自动发现机制
- 新 skill 先在某工作区试用（`status: draft`），验证好了再提交到本仓库（`status: stable`）。完整流程见 [EVOLUTION-PACT.md](EVOLUTION-PACT.md)

---

## 治理文档索引

| 文档 | 管什么 |
|---|---|
| [README.md](README.md)（本文件） | skill 目录 + 接入指南 + LiveWithOpenCove 关系 |
| [ROUTING.md](ROUTING.md) | 语义路由：意图话术→调什么 skill |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 架构全景：分层、同步、历史 |
| [EVOLUTION-PACT.md](EVOLUTION-PACT.md) | 进化公约：draft/stable/deprecated 生命周期 |
| [STORAGE-SPEC.md](STORAGE-SPEC.md) | skill 产出物存储 + 命名规范 |
| [CONTEXT-SPEC.md](CONTEXT-SPEC.md) | 上下文调用规范（什么时机读什么、读多深） |
| [EXPORTS.md](EXPORTS.md) | 权威源→开源仓库单向导出登记 |
| [DEVICES.md](DEVICES.md) | 设备与连接权威清单 |
| [DIRECTORY-SPEC.md](DIRECTORY-SPEC.md) | 工作区目录命名规范 |

---

## License

MIT
