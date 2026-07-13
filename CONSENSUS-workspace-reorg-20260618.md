# 共识：工作区与 Skill 体系重整

> 日期：2026-06-18
> 范围：DailyWork / ContentWork / study-research 三工作区 + shared-skills 权威池 + 两个开源仓库 + 全局记忆/规则
> 状态：决策已锁定，调研已完成，等待按顺序开工。本文件是后续所有重整动作的依据。

---

## 一、背景与触发

为 OpenCove 配套的多工作区 setup（3 目录 = 3 角色：做事/写作/研究，共享一份 skill 池，agent 不擅自写记忆）在长期使用后长歪了。用户提出对工作区配置文件、skills、目录排布方式整体重组。

本文件汇总一次完整讨论 + 调研的结论。讨论全程未改动任何文件。

---

## 二、扫描发现的客观现状（实测数据）

1. **全局入口马甲泛滥**：`~/.claude/skills/` 共 **84 条**，其中 **21 组是马甲**（指向同一实体的多个软链）。
   - 9 个共享 skill 各被挂 5 遍（无前缀 + dw + dw2 + sr + cw）
   - interview-writer 挂 3 遍
   - 11 个 DailyWork 本地 skill 各挂 2 遍（无前缀 + dw2）
   - 去重后真实 skill 约 35 个。
2. **目录双重身份**：`Daily Work`(带空格) 与 `DailyWork`(软链) 指向同一物理目录；`content work` / `Content Work` 同 inode（macOS 不区分大小写）。dw/dw2 两套前缀由此而来。
3. **该露没露**：thunderbird、ui-design、source-intake、academic-plotting、rigor-reviewer 等有用本地 skill 未进全局入口。
4. **权威源散三处**：
   - `shared-skills/`（无 git remote，声明的唯一权威，15 skill）
   - `LiveWithOpenCove/`（已开源，教学骨架，5 skill，closeout 已分化为 302 行删减版 vs 权威 498 行）
   - `research-skills-pack/`（已开源，学术发行包，24 skill，含 paper-* 全套 + Windows 安装）
   - 三者不是简单复制，是 1 个本地权威 + 2 个面向不同受众的开源发行版。
5. **记忆模型缺一层**：6 文件（timeline/workspace-map/current-position/decisions/lessons/workspace-brief）全是**工作区级**记忆，缺**任务级**记忆。current-position 一个文件被迫扛所有任务的"现在"，任务一多就糊。无成果/资产登记位，导致"记得住进度记不住成果"。
6. **执行步长一刀切**：全局 CLAUDE.md 铁律要求每轮都输出确认块，不分任务大小，导致小事也走确认仪式。
7. **skill 无存储规范**：各 skill 产出"乱存、不知道放哪"，没有统一的存哪+怎么命名的规矩。

---

## 三、锁定的核心决策（7 条）

1. **权威源唯一**：`shared-skills/` 是唯一权威。LiveWithOpenCove 和 research-skills-pack 是**单向导出的裁剪快照**，只能从权威池导出，不反向手改。
2. **入口去前缀**：一个 skill 一个入口；只有"同名不同内容"才加前缀消歧。角色隔离交给各工作区自己的 `skills/` 目录，不靠全局入口前缀。
3. **目录名统一**：不带空格——DailyWork / ContentWork / study-research。不改物理目录，确保不带空格名可用，后续软链统一用不带空格路径。
4. **光盘层**：留作约定写进架构文档，**暂不实现**。比喻——光盘机=共享 skill 引擎（逻辑，唯一权威），光盘=工作区只放配套差异配置。补的是"纯共享"与"整份 fork"之间缺失的中间档。真需求出现再激活（届时在工作区放 `<skill>.config.md`，共享 skill 启动时读它）。
5. **记忆分两层**：
   - 长期层（现有 6 文件）**不动**。
   - 新增**任务级层** `.claude/memory/tasks/<语义任务名>/`：
     - `state.md` — 状态机锚点：当前阶段 / 下一步 / 必须遵守的规矩（每轮重读，治流水线失忆）
     - `artifacts.md` — 产出物登记：是什么 / 存哪（含跨设备路径如 Win 的 D:\...）/ 怎么连接复现 / 关联项目（治"记不住成果"）
     - `context.md` — 该任务背景与已定决策
6. **存储规范**：制定全局 skill 产出物"存哪+怎么命名"规范，各 SKILL.md 写清自己产出去向，新 skill 照此走。与第 5 条同根：东西存哪 + 怎么找回。
7. **执行步长按大小分级**：
   - 小事（改几个文件 / 可逆 / 不改架构）→ 直接做完报告。
   - 大事（动架构 / 删数据 / 不可逆 / 新增功能）→ 走确认块。

---

## 四、调研结论（借鉴四档）

**调研方式**：web 概念调研 + harvest-tool 抓取 GitHub 真实实现。
**抓取仓库**：`hudrazine/claude-code-memory-bank`、`zhangfengcdt/memoir`（cathedral 抓取返回空，未补，前两个已足够支撑设计）。

### ✅ 直接借（抄结构）
- memory-bank 的**工作流 slash 命令**：把"调研→需求→脑暴→排布→完成→输出"做成 `/flow:调研`、`/flow:设计`… 可重入命令，每阶段独立、可跳回。治"流水线失忆"的核心。
- memory-bank 的 **`update-memory` 独立阶段**：写记忆是流程里显式一步，不靠 agent 自觉。

### 🔧 改造借
- 任务级记忆落地为 `.claude/memory/tasks/<任务名>/`（state + artifacts + context 三文件），对标 memory-bank 的 activeContext 但**一任务一份**。
- memoir 的**语义路径命名**：任务目录用有意义的名字（如 `2026-汽车课设`），不用 UUID。

### 📖 只参考方法
- memoir 的诊断框架：**"Global Variable 反模式"**（flat 文件当全局存储会撞上下文污染/token 房租/记忆漂移）+ **"token 房租"**（大 timeline 每改一点就失效整段前缀缓存）→ 论证为什么要拆层、为什么 DailyWork 的 43KB timeline + 430KB 归档要瘦身。
- memoir 的 git 版本控制思想 → 现有 markdown 本就在 git 里，够了。

### ❌ 明确不抄
- memoir 的 pip Python 系统 + 向量/语义搜索引擎（违背"纯 markdown、不要黑箱"原则）。
- memory-bank 的 init 自动探测代码栈（用户非纯代码项目）。

---

## 五、任务台账（9 条 / 5 工作流）

| # | 任务 | Stream | 需求 | 风险 |
|---|---|---|---|---|
| 1 | 备份当前 skills 软链结构 | A 入口 | 已定 | 零 |
| 3 | 统一工作区目录名为不带空格 | A 入口 | 已定 | 低 |
| 2 | 去马甲：删 49 条重复软链 84→35 | A 入口 | 已定 | 中·可回滚 |
| 4 | 逐个确认后补暴露本地 skill | A 入口 | 已定 | 低 |
| 5 | 梳理 skill 定位、合并可合并项 | A 入口 | 已定 | 仅分析 |
| 6 | 单一权威源 + 单向导出 + 光盘层留约定 | B 架构 | 已定 | 低·纯文档 |
| 7 | 任务级独立记忆 + 产出物定位 | C 记忆 | 方向定·待出设计 | 中 |
| 9 | skill 产出物存储+命名规范 | E 规范 | 方向定·待出草案 | 中 |
| 8 | 执行步长按任务大小分级 | D 规则 | 已定 | 中·改全局规则 |

---

## 六、执行顺序

1. **A 入口**：#1 备份 → #3 目录名 → #2 去马甲（删前列 49 条过目）→ #4 逐个确认补暴露 → #5 出合并分析。落地 84→35。
2. **B 架构**：#6 写 EXPORTS.md + 更新 ARCHITECTURE.md（含光盘层约定）。
3. **C+E 设计落盘**：先出 #7/#9 设计草案，用户拍板后再改记忆模型、写存储规范。
4. **D 规则**：#8 改全局 CLAUDE.md，影响面最大，单独验证。

---

## 七、可验证检查点

- 每步只动软链/文档，不碰实体 skill 文件；阶段 0 备份是回滚基线。
- 每改一批跑 `scan-skills.py` 重新生成索引，对照"能力没丢、断链为零"。
- 收尾出"重整前后对照表"：84→35，哪些被合、哪些新增。

---

## 八、第二轮：能力层/自动化层/演化层 + 开局精简（2026-06-18 同日续）

第一轮收口后，用户追加了系统级重组诉求，并要求"优先汲取成熟项目经验"。

### 8.1 新增任务（F/G/H + 开局精简）
- **F skills 收拢**：折叠纯下游入口（撤 output-polisher / output-style-checker / debate-engine 的全局入口，实体保留），44 个入口。学术线全局隔离（动作B）暂缓。
- **G hook 重整**：archive 脚本从带空格路径挪到 `~/.claude/hooks/`；新增 `memory-nudge.py`（Stop 事件，有产出但 INDEX 没更新就提醒，只提醒不写）。
- **H 进化公约**：`EVOLUTION-PACT.md`，draft/stable/deprecated 三状态 + 开分支/验证/收回/丢弃流程。
- **开局精简**：记忆改 lazy load（开局只读规则，记忆等第一句后按需读）；AGENTS.md 消重指向全局 CLAUDE.md；memory-nudge 性能修复（不再 rglob 1084 文件）。开局读取 7900→5209 token。

### 8.2 harvest 调研结论（验证方向）
抓取 Continuous-Claude-v3(3.8k⭐) + russbeye/claude-memory-bank。结论：用户的方向（lazy load、hook 联动记忆、skill 收拢、进化公约）全部被高星项目验证正确，差距只在自动化成熟度。
- **可借**：hook 按生命周期事件归类；PreCompact/SessionEnd 联动记忆；`/context-query` 按需取上下文（lazy load 成熟版）。
- **不抄**：TLDR 5 层分析、daemon、109 skill 规模、重型 MCP 依赖（对单人轻代码场景过重）。

---

## 九、最终成果对照表

### 全局 skill 入口
| 阶段 | 入口数 | 说明 |
|---|---|---|
| 重整前 | 84 | 49 条重复马甲（dw/dw2/sr/cw 前缀） |
| 去马甲后 | 35 | 一个 skill 一个入口，零重复 |
| 撤僵尸后 | 33 | 撤 setup-daily-work-skills、research-academic |
| 补暴露后 | 47 | 补 13 个本地 skill（ui-design/source-intake/workspace-* 等） |
| 折叠下游后 | 44 | 撤 3 个纯下游入口 |

### 新增/修改的文档与规则
| 产物 | 位置 | 作用 |
|---|---|---|
| CONSENSUS-workspace-reorg | shared-skills/ | 本文件，全程决策依据 |
| EXPORTS.md | shared-skills/ | 权威源 + 单向导出登记 |
| STORAGE-SPEC.md | shared-skills/ | skill 产出存储+命名规范 |
| EVOLUTION-PACT.md | shared-skills/ | 进化公约（分支/收回） |
| ARCHITECTURE.md（更新） | shared-skills/ | 加权威源/单向导出/光盘层约定 |
| HOOKS-RESPONSIBILITY.md | ~/.claude/hooks/ | hook 职责表 |
| 全局 CLAUDE.md（更新） | ~/.claude/ | 执行步长分级 + 开局 lazy load |
| tasks/ 体系 | DailyWork/.claude/memory/ | 任务级记忆 INDEX+四件套模板 |
| memory-nudge.py | ~/.claude/hooks/ | 记忆提醒 hook |
| 20 个 SKILL.md | 各 skill | 补"产出去向"指针 |

### 待续（等 Win 开机）
- #7 收尾：汽车课设真实迁入 tasks/ + 改 DailyWork/CLAUDE.md units 规则 + closeout 接入强制更新
- #10 动作B：学术线全局隔离
- 开局精简推广到另两工作区的 AGENTS（如需）

