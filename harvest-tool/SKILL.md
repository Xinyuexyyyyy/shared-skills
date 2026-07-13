---
name: harvest-tool
description: 当用户想找可借鉴的 GitHub 项目、筛成熟方案、抓仓库资料并沉成共识文档时使用。它负责把“借鉴什么、怎么借、哪些不抄”收成一条稳定流程，不负责替用户拍板产品方向；依赖 gh CLI，若未登录或输入不是 GitHub 仓库链接就先停下并提示。
status: stable
agents: main
---

# Harvest Tool

## 定位

把“我想找能借鉴的 GitHub 项目”收成一条可复用路径：先发现，再筛选，再抓取，最后沉成结构化共识。

它在防的坑很明确：

- 一上来就硬抄，没先看清仓库在解决什么
- 候选太多，但没有先收敛 shortlist
- 只抓到资料，没沉成可继续讨论的共识
- 最后写成参考笔记，却没有明确哪些能直接借、哪些要改造、哪些只参考

先看什么：
1. 先看本文件，确认什么时候该用 `harvest-tool`
2. 如果用户给了 GitHub 仓库并要求生成共识草稿，读取 [docs/github-harvest-to-consensus.md](docs/github-harvest-to-consensus.md)
3. 需要样例时读取 [docs/github-harvest-examples.md](docs/github-harvest-examples.md)，需要验收时读取 [docs/github-harvest-acceptance.md](docs/github-harvest-acceptance.md)
4. 再看 [README.md](README.md)，看完整操作和验收方式
5. 排错时再看 `skill.py` 和 `scripts/`

## 什么时候用

- 用户说“帮我找几个能借鉴的 GitHub 项目”
- 用户已经有方向，但想快速比较 5 到 10 个开源仓库
- 用户已经给出 GitHub 仓库链接，想抓 README、目录和关键代码做拆解
- 用户想把借鉴结论沉成 `task_draft/consensus/...` 里的共识文档

## 不什么时候用

- 用户还在做“这个想法值不值得研究”的路线判断
- 用户要的是产品调研、社会调研、论文综述，而不是 GitHub 借鉴
- 用户没有 GitHub 仓库链接，却要求直接抓取具体代码
- 用户希望工具替他自动决定“最终就抄哪个”，这一步必须保留人工判断

## 默认工作方式

不要让用户自己手敲命令。用户只需要讲目标，你在内部按阶段调用。

如果用户已经给了明确 GitHub 仓库链接，就直接进入 `harvest`，不要重复 discover/evaluate。

如果用户的目标是“把 GitHub 项目借鉴结果沉成共识草稿”，按 `github-harvest-to-consensus` 任务书执行：补全仓库链接、运行 harvest/analyze、分出“直接用 / 改造用 / 只参考 / 不抄”、落盘到 `task_draft/consensus/<独立子目录>/`，最后给出可验证文件路径。

## 六阶段流程

```text
Stage 1: Discover  -> 搜索一批候选仓库
Stage 2: Evaluate  -> 结合用户目标做第一轮筛选
Stage 3: Select    -> 给用户看 shortlist，等用户确认抓哪几个
Stage 4: Harvest   -> 抓 README / 目录结构 / 关键代码
Stage 5: Analyze   -> 提炼“能直接借鉴什么、风险是什么”
Stage 6: Consensus -> 落成共识文档，方便后续执行
```

## 用户可见检查点

### 检查点 1：发现后先确认 shortlist

先展示候选仓库，再等用户确认：
- 要继续看哪 1 到 3 个
- 哪些可以直接排除
- 是否需要换关键词重搜

### 检查点 2：正式抓取前先确认范围

等用户确认后再批量抓取，避免一口气 harvest 太多仓库。

### 检查点 3：写共识前先确认结论方向

先给出“准备直接借鉴什么 / 只参考什么 / 明确不抄什么”，等用户确认后再正式落盘。

### 检查点 4：结论必须能一眼复核

最后输出里必须有：
- 这个仓库解决什么问题
- 哪些东西可以直接借
- 哪些东西要改造后借
- 哪些东西只做方法参考

**出口断言(调研层验证,出本层前必过)**：结论里引用的仓库/数据/事实,交付前要真取证(`gh repo view`、原文链接、`lsof` 等),不靠"我记得"。硬断言:引用的东西必须真实存在,不过则停下回退调研;软建议:候选够不够全,提醒可继续。详见全局 `~/.claude/CLAUDE.md`「验证层」。

## Action

### `discover`

```bash
python3 skill.py discover "关键词" [数量]
```

用在还没锁定仓库时，先搜一批候选。

### `harvest`

```bash
python3 skill.py harvest <github-url>
```

用在用户已经点名某个 GitHub 仓库时，抓 README、目录结构和关键代码。

### `evaluate`

```bash
python3 skill.py evaluate
```

读取上一轮 discover 结果，整理成便于评估的输入材料。

### `analyze`

```bash
python3 skill.py analyze [repo_name]
```

读取上一轮 harvest 结果，整理成便于分析的输入材料。

### `compare`

```bash
python3 skill.py compare [repo_name ...] [--goal <type>]
```

把多份 `analyze` 摘要汇总成 shortlist 对比材料。

### `compare-consensus`

```bash
python3 skill.py compare-consensus [repo_name ...] [--goal <type>]
```

先跑一轮 compare，再把 `consensus_seed` 直接落成正式共识目录。

### `consensus`

```bash
python3 skill.py consensus '{"做什么": "...", "从哪里抄": {"直接用": [...], "改造后用": [...], "只参考": [...]}}'
```

把已经讨论好的结论保存成共识文档。

### `github-harvest-to-consensus`

不是独立 CLI 命令，而是一条上层任务书。用户给 GitHub 仓库和主题任务时，按 [docs/github-harvest-to-consensus.md](docs/github-harvest-to-consensus.md) 执行，最终必须产出独立共识目录和验收说明。

## 结果长什么样

一眼要能看到这 4 件事：

- 仓库解决什么问题
- 哪些做法可以直接借
- 哪些做法要改造后借
- 哪些只做方法参考

## 边界条件

### 情况 1：用户目标太模糊

**条件**：只说“帮我找项目”，但没说领域、用途、约束。
**处理**：先追问 1 到 3 个关键限制（做什么、技术栈、借鉴重点），不要直接大搜一轮。
**对用户怎么说**：先告诉我你要借鉴的是产品形态、技术方案，还是工作流，我再帮你缩小范围。

### 情况 2：`gh` 未登录或不可用

**条件**：`gh auth status` 失败，或命令执行报错。
**处理**：停止 discover / harvest，先提示检查 `gh` 登录状态。
**对用户怎么说**：当前机器的 GitHub CLI 还没登录好，这轮先不能抓仓库，先运行 `gh auth status` 看状态。

### 情况 3：链接不是 GitHub 仓库

**条件**：输入不是 `https://github.com/<owner>/<repo>` 形式。
**处理**：不要硬跑 harvest，先让用户补正确仓库链接。
**对用户怎么说**：这不是标准 GitHub 仓库链接，我先不抓，给我完整仓库地址再继续。

### 情况 4：搜索结果太杂或命中为空

**条件**：discover 结果和目标明显不匹配，或基本没有可用候选。
**处理**：展示当前结果，建议换关键词、补限定词或缩小数量。
**对用户怎么说**：这轮搜出来的结果偏散，我建议先换关键词或加限定词，不然继续分析只会浪费时间。

### 情况 5：抓取结果不够支撑结论

**条件**：仓库缺 README、目录太薄、关键实现抓不到。
**处理**：明确标注“信息不足”，只输出观察，不强行给抄法结论。
**对用户怎么说**：这个仓库公开信息不够，我可以先记下值得继续看的点，但现在还不该把它写成确定方案。

## Tool 依赖

- `gh` CLI：负责 GitHub 搜索和抓取
- `skill.py`：CLI 入口
- `scripts/`：各阶段脚本
- 目录：`skills/harvest-tool/data/`
- 目录：`task_draft/consensus/`

## 最小验收

```bash
gh auth status
python3 skills/harvest-tool/skill.py discover "deep research" 3
python3 skills/harvest-tool/skill.py evaluate
```

验收通过标准：
- discover 能返回候选仓库列表
- evaluate 能输出可供人工筛选的输入材料
- 整个过程不要求用户自己理解内部脚本结构
- 最终共识能稳定落到 `task_draft/consensus/<独立子目录>/`

---

## 产出去向

产出物落盘与命名遵循全局规范 `~/shared-skills/STORAGE-SPEC.md`：产出可存任何位置，但每件正式产出须在所属任务 `tasks/<任务>/artifacts.md` 登记坐标；用语义名不用纯时间戳；同主题反复生成覆盖或归档旧版。
