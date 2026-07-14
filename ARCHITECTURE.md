# 跨工作区 Skill 共享架构

> 日期：2026-07-13
> 本文件是 `~/shared-skills/` 的权威架构文档。GitHub 仓库 `Xinyuexyyyyy/shared-skills` 是跨平台（Mac/Win）的唯一权威源。

## 治理文档索引

| 文档 | 管什么 |
|---|---|
| [README.md](README.md) | 入口：skill 目录 + 双平台接入指南 + LiveWithOpenCove 关系 |
| ARCHITECTURE.md（本文件） | 架构全景：分层、GitHub 同步、权威源、历史 |
| [ROUTING.md](ROUTING.md) | 语义路由：意图话术→调什么 skill（agent 每轮开局读） |
| [EVOLUTION-PACT.md](EVOLUTION-PACT.md) | 进化公约：draft/stable/deprecated 生命周期 |
| [STORAGE-SPEC.md](STORAGE-SPEC.md) | skill 产出物存储 + 命名规范 |
| [CONTEXT-SPEC.md](CONTEXT-SPEC.md) | 上下文加载策略（什么时机读什么、读多深） |
| [EXPORTS.md](EXPORTS.md) | 权威源→开源仓库单向导出登记 |
| [DEVICES.md](DEVICES.md) | 设备与连接权威清单（Win/ECS/userysys，实测） |
| [DIRECTORY-SPEC.md](DIRECTORY-SPEC.md) | 工作区目录命名规范 |
| [harness/README.md](harness/README.md) | 可复用 harness、版本化 bundles 与示例工作区 |

---

## 一、核心原则

**GitHub 仓库 `Xinyuexyyyyy/shared-skills` 是唯一的权威源。** Mac 和 Win 通过 `git push/pull` 共享同一份 skill 池。每台机器本地 `git clone` 后，工作区按需软链接到 clone 目录。

---

## 二、GitHub 同步架构

```
     GitHub: Xinyuexyyyyy/shared-skills  ← 权威源
      ↑ git push                ↓ git pull
   Mac (~/shared-skills/)   Win (C:\Users\sure\shared-skills\)    Mac 其他工作区
        │ softlink                   │ softlink                        │ softlink
   Mac 工作区 (DailyWork2 等)    Win 工作区 (DailyWorkAnsys 等)     ContentWork / study-research
   ↓ closeout 建议写记忆           ↓ closeout 建议写记忆
   各自 memory/                  各自 memory/
   (按 LiveWithOpenCove           (按 LiveWithOpenCove
    6 文件模型)                    6 文件模型)
```

**同步规则：**
- 改 skill 只在本地 clone 目录改 → `git commit` → `git push`
- 另一边 `git pull` 即同步
- 两边同时改了同一文件 → 正常的 git merge 冲突解决，后来的一方处理
- 每台机器的 memory/ 是本地独立的（不改它人记忆），不在 GitHub 同步

## 三、目录结构

```
~/shared-skills/                    ← GitHub 权威仓库：Mac push, Win pull
│   # ===== 根文件 =====
├── README.md                       # 入口：skill 目录 + 接入指南
├── ROUTING.md                      # 语义路由表：用户话术→调什么
├── ARCHITECTURE.md                 # 本文件
├── EVOLUTION-PACT.md               # 进化公约：draft/stable/deprecated
├── STORAGE-SPEC.md                 # 产出物存储 + 命名
├── CONTEXT-SPEC.md                 # 上下文加载策略
├── EXPORTS.md                      # 单向导出登记
├── DEVICES.md                      # 设备连接清单（实测）
├── DIRECTORY-SPEC.md               # 目录命名规范
├── harness/                        # 可复用 harness 方法、bundle、示例和校验
│
│   # ===== 调研层（8） =====
├── deep-research/          # 调研总入口 v2.1
├── research/               # 模板取证包（引擎）
├── research-layer-v2/      # 方法编排参考
├── idea-to-research/       # 模糊想法路由
├── harvest-tool/           # GitHub 项目收割
├── source-intake/          # 材料第一轮分析
├── web-scrape/             # 网页数据提取
├── methodology-distiller/  # 专家方法提炼
│
│   # ===== 任务层（7） =====
├── task-analyze/           # 意图分析
├── task-decompose/         # 任务拆解
├── task-crafter/           # 任务文件生成
├── project-sop/            # 项目全流程
├── grillme/                # 诊断式提问
├── workspace-init/         # 工作区初始化
├── workspace-tidy/         # 工作区整理
│
│   # ===== 输出层（7） =====
├── output-control-layer/   # 输出前总闸
├── output-layer/           # 公共输出路由
├── output-polisher/        # 排版 + Obsidian 导出
├── output-style-checker/   # 硬伤检查
├── humanizer/              # AI 痕迹审计
├── drawio-diagram-agent/   # draw.io 流程图
├── closeout/               # 任务收尾
│
│   # ===== 运维层（4） =====
├── skill-optimizer/        # 锐评 + 优化闭环
├── skill-dashboard/        # 技能仪表盘
├── skill-reforge/          # 外部 skill 引入
├── external-skill-adoption/# skill 采纳决策
│
│   # ===== 待激活（5） =====
├── anchor-spark/           # 创作激发器
├── debate-engine/          # AI 辩论引擎
├── dream-catcher/          # 想法对撞机
├── ui-design/              # UI 设计验收
│
│   # ===== 工具 + 数据 =====
├── _tools/                 # 管理工具（不被扫描为 skill）
├── methodology-vault/      # 方法卡片库（数据，非 skill）
├── backups/                # skill 备份快照
└── .gitignore
```

---

## 四、平台接入关系

| 平台 | 工作区 | 接入方式 | 共用 skill 数 |
|---|---|---|---|
| **Mac** | `~/DailyWork2/` | skills/ 下软链接指向 `~/shared-skills/` | 25（全量） |
| **Mac** | `~/Content Work/` | skills/ 下软链接指向 `~/shared-skills/` | 9（按需） |
| **Mac** | `~/study-research/` | skills/ 下软链接指向 `~/shared-skills/` | 9（按需） |
| **Win** | `C:\Users\sure\` | git clone 到 `C:\Users\sure\shared-skills\`，Win 工作区 skills/ 软链接指向它 | 25（全量） |

### Mac 本地 skill（不在 shared-skills，各工作区独有）

| 工作区 | 本地 skill |
|---|---|
| DailyWork2 | ppt-master, ppt-master-bridge, bilibili-video-analyzer, douyin-video-analyzer, opencove-remote-deploy, content-pipeline, info-head, topic-collector, interview-writer, english-daily-session, autostudy, fast-onboard 等 |
| Content Work | interview-writer（权威版）, sure-content-studio |
| Study Research | paper-discovery, paper-reading, paper-screening, academic-deep-research, supervisor-scout, survey-writer 等 |

---

## 五、Skill 分层

```
┌─────────────────────────────────────────────────┐
│         共用层 (~/shared-skills/) — 25 skill     │
│                                                  │
│  调研: deep-research, research, research-layer-v2│
│        idea-to-research, harvest-tool,            │
│        source-intake, web-scrape,                 │
│        methodology-distiller          (8)         │
│                                                   │
│  任务: task-analyze, task-decompose,              │
│        task-crafter, project-sop, grillme,        │
│        workspace-init, workspace-tidy (7)         │
│                                                   │
│  输出: output-control-layer, output-layer,        │
│        output-polisher, output-style-checker,     │
│        humanizer, drawio-diagram-agent,           │
│        closeout                         (7)       │
│                                                   │
│  运维: skill-optimizer, skill-dashboard,          │
│        skill-reforge, external-skill-adoption (4) │
│                                                   │
│  待激活: anchor-spark, debate-engine,             │
│         dream-catcher, ui-design        (5)      │
└─────────────┬───────────────────────────────────┘
              │ GitHub push/pull (跨平台)
              │ 或 软链接 (同机跨工作区)
    ┌─────────┼─────────┬──────────────┐
    │         │         │              │
 DailyWork2  Content  Study       Win 工作区
 (Mac)       Work     Research    (Win)
             (Mac)    (Mac)       git clone →
                                  C:\Users\sure\
                                  shared-skills\
```

> LiveWithOpenCove 是这套架构的"公开文档版"——它用 5 个教学骨架 + 示例工作区向开源用户展示方法。shared-skills 是你的**实际运行版**（25 skill，完整逻辑）。两个仓库的关系见 [README.md](README.md) 的"记忆体系"节。注意：架构图中的方向是"推哪个 skill 到哪个仓库"，实际同步方向是 `权威源 → 开源仓库`，反向禁止。

---

## 六、约定

### 6.1 新增共用 skill（GitHub 工作流）

1. `git pull` 拉最新，避免冲突
2. 在 `~/shared-skills/` 下创建目录，写 `SKILL.md`
3. 运行 `_tools/auto-link.sh` 自动建 `CLAUDE.md -> SKILL.md`
4. `git add -A && git commit -m "feat: add <skill>" && git push`
5. Win 端 `cd C:\Users\sure\shared-skills && git pull`
6. 各工作区如需接入，建软链接到 clone 目录

### 6.2 新建工作区接入

1. 在新工作区下创建 `skills/` 目录
2. 按需建软链接到 `~/shared-skills/` 下的 skill
3. 建 `.claude/skills -> skills/` 软链接
4. 创建 `.claude/memory/` 目录 + 6 个标准模板文件
5. 创建 `AGENTS.md`，列出共用 skill 和本地 skill
6. 创建 `.claude/CLAUDE.md`，写 Skills 边界表

### 6.3 Skill 命名冲突

- 共用 skill 改名时，需要同时更新所有工作区的软链接
- 如果某个工作区需要对共用 skill 做个性化，优先走第八节"光盘层"约定（只放配置差异）；只有逻辑确实要分叉时，才把它移回本地，不要在 shared-skills 里加条件分支
- 全局入口（`~/.claude/skills/`）一个 skill 只保留一个入口，不加工作区前缀；只有"同名不同内容"才加前缀消歧。角色隔离交给各工作区自己的 `skills/` 目录

### 6.4 管理工具使用

`_tools/` 是本机公共工具层，只负责扫描、追踪、推荐、治理和 dashboard 数据，不放业务 skill。

```bash
# 在任意工作区下运行，生成该工作区的 skill-index.json
python3 ~/shared-skills/_tools/scan-skills.py

# 指定输出位置
python3 ~/shared-skills/_tools/scan-skills.py --output ./skill-index.json

# 只看层级结构
python3 ~/shared-skills/_tools/scan-skills.py --tree

# 搜索 skill
python3 ~/shared-skills/_tools/scan-skills.py --query "调研"
```

默认验收链：

```bash
python3 skills/scan-skills.py
python3 skills/skill-trace.py
python3 skills/skill-governance.py --query "先对齐一下工作方式"
python3 skills/skill-recommend-regression.py
```

通过标准：

- `skills/skill-index.json` 和根目录 `skill-index.json` 内容一致
- `skills/skill-dashboard.data.js` 和根目录 `skill-dashboard.data.js` 内容一致
- `skill-governance.snapshot.json` 写在当前工作区的 `skills/` 下
- `skill-recommend-regression.py` 输出 `OK`

---

## 七、验证方法

```bash
# 确认软链接完整性（在任意工作区 skills/ 下）
ls -la skills/ | grep "^l"

# 确认同一 skill 跨区指向同一文件（inode 一致）
stat -f "%i" ~/shared-skills/task-analyze/SKILL.md ~/Daily\ Work/skills/task-analyze/SKILL.md

# 重新生成索引并检查
python3 ~/shared-skills/_tools/scan-skills.py --tree
```

---

## 八、权威源与开源发布（单向导出）

> 完整登记表见 [EXPORTS.md](EXPORTS.md)。本节只讲规则。

### 7.1 两个权威源（按领域分）

- **通用层权威** = `~/shared-skills/`：task / output / research 底座 / harvest / idea-to-research 等
- **学术线权威** = `~/study-research/skills/`：paper 流水线 / academic-* / survey / supervisor-scout / topic-framing / method-design 等

不是所有 skill 挤在一处，而是按领域各有一个权威源。

### 7.2 两个开源仓库是单向导出快照

| 仓库 | 受众 | 来源 |
|---|---|---|
| `LiveWithOpenCove/`（已开源） | 想抄这套 setup 的人 | 从 shared-skills 导出 5 个基础 skill 的精简骨架 |
| `research-skills-pack/`（已开源） | 做学术科研的人 | 从 shared-skills + study-research 导出学术线全套 |

**铁律**：改 skill 只在权威源改，导出方向永远是 `权威源 → 开源仓库`，**禁止反向手改开源仓库再指望同步回来**。在开源仓库发现要改，回权威源改，再重新导出。

---

## 九、光盘层约定（保留，暂不实现）

> 这是一个**已确认方向但暂不落地**的约定，记在这里防止以后重复讨论。

**比喻**：光盘机 = 共享 skill 引擎（逻辑，唯一权威）；光盘 = 工作区只放配套的差异配置，插进引擎里跑。

**它补的空档**：现在对一个 skill 只有两档处理——纯共享（软链，零差异）或整份 fork（复制回本地）。光盘层是中间档：**逻辑不动，只换配置**。

**为什么暂不建**：目前没有"同一逻辑、每个工作区要不同配置"的真实案例。为未出现的需求预埋机制，违反"不主动新增复杂架构"。

**真需求出现时怎么激活**（一个文件的事）：在该工作区放 `<skill>.config.md`，让共享 skill 启动时先读它，按配置调整行为。不需要现在预埋整套机制。

---

## 十、历史

- **2026-07-13**：Win 重装后重建。shared-skills 推 GitHub（`Xinyuexyyyyy/shared-skills`），Mac↔Win 同步链路打通。新增 13 个 DailyWork2 独有 skill 入仓，harvest-tool 合并入仓。skill 从 11→25（+ web-scrape / anchor-spark / debate-engine / dream-catcher / ui-design 待激活）。ARCHITECTURE 补 GitHub 同步章节。README 重写为双平台接入本。ROUTING 更新全量 skill 路由。明确 LiveWithOpenCove = 记忆骨架 / shared-skills = 技能引擎 的分工。
- **2026-06-18**：工作区重整。全局入口去马甲 84→33；目录名统一不带空格；确立两个权威源 + 单向导出（见 [EXPORTS.md](EXPORTS.md)）；新增光盘层约定（暂不实现）。完整决策见 [CONSENSUS-workspace-reorg-20260618.md](CONSENSUS-workspace-reorg-20260618.md)。
- **2026-05-27**：新增 `source-intake` 到公共池，先接入 Daily Work。
- **2026-05-27**：新增 `ui-design` 到公共池，先接入 Daily Work。
- **2026-05-21**：初始建立。从 Daily Work 迁出 9 个 skill 到公共池。
