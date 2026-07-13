# github-harvest-to-consensus

## 定位

把一个 GitHub 仓库和用户主题任务，转成可继续执行的共识草稿。

这不是新工具，也不是新 skill。它是 `harvest-tool` 的上层任务书：复用现有 `discover / harvest / analyze / consensus`，把过程收成固定交付物。

## 适用输入

- 用户给出 `https://github.com/<owner>/<repo>`
- 用户给出 `owner/repo`
- 用户说“借鉴这个 GitHub 项目”“用 harvest 后转成共识草稿”“这个项目怎么抄”

## 不适用输入

- 没有 GitHub 仓库，也没有明确领域：先问清用途或走 `discover`
- 用户要产品市场调研、论文综述、社会调研：不要硬套 GitHub harvest
- 用户要求直接照搬代码：必须先拆“直接用 / 改造用 / 只参考 / 不抄”

## 用户可见效果

用户最后应该看到：

- 这个仓库解决什么问题
- 值得借鉴的成熟做法是什么
- 哪些可以直接用
- 哪些必须改造后用
- 哪些只做方法参考
- 明确不抄什么
- 下一步最小任务点
- 共识文件落在哪里

## 最小流程

### 1. 补全仓库链接

如果用户输入是 `owner/repo`，补成：

```text
https://github.com/<owner>/<repo>
```

如果不是 GitHub 仓库格式，停下让用户补链接。

### 2. 检查 GitHub CLI

```bash
gh auth status
```

失败时不要继续抓取，提示用户先修 `gh` 登录。

### 3. 抓取仓库

```bash
python3 skills/harvest-tool/skill.py harvest https://github.com/<owner>/<repo>
```

抓取结果会落到：

```text
skills/harvest-tool/data/harvest_<owner>_<repo>.json
```

### 4. 生成分析材料

```bash
python3 skills/harvest-tool/skill.py analyze <owner>/<repo>
```

重点看：

- 仓库画像
- 材料置信度
- README
- 目录结构
- 核心代码文件
- 抓取警告

### 5. 做借鉴分层

必须分成 4 类：

| 类别 | 含义 |
|---|---|
| 直接用 | 不改或轻改就能采用的结构、文案、流程、验收方式 |
| 改造用 | 思路可用，但需要换成本工作区语义、路径或边界 |
| 只参考 | 适合学习方法，不适合进入 MVP |
| 不抄 | 会偏离用户目标、过重、风险高或不符合工作区偏好的内容 |

不能只写“值得参考”，必须说清“怎么借”和“为什么不全抄”。

### 6. 生成共识

用 `consensus` action 保存结构化结果：

```bash
python3 skills/harvest-tool/skill.py consensus '<json>'
```

共识目录必须落到：

```text
task_draft/consensus/<slug-timestamp>/
```

建议至少包含：

- `README.md`
- `consensus.md`
- `consensus.json`
- `final-report.md`
- `research_plan.md`

如果用户明确要求“拆任务”，再补：

- `copy_task_breakdown.md`

### 7. 验收回复

完成回复必须告诉用户：

- 输出目录
- 核心文件
- 本轮做了什么
- 用户怎么验证
- 下一步要拍板什么

## 输出结构建议

### consensus.md

用于沉淀“共识”：

- 做什么
- 为什么做
- 目标
- 从哪里抄
- 怎么做
- 实施优先级
- 不确定性
- 风险
- 来源仓库

### final-report.md

用于人读：

- 本轮结论
- 仓库成熟度快照
- 借鉴分层
- 对当前主题任务的共识
- 推荐 MVP 切口
- 下一步最小行动
- 不抄什么
- 验收方式

### research_plan.md

用于后续继续调研：

- 调研目标
- 调研范围
- 分析框架
- 转化问题
- 推荐第一版方案
- MVP 边界
- 验收清单

### copy_task_breakdown.md

用于用户问“怎么抄、拆任务”：

- 先说结论
- 不抄什么
- 最多 5 个任务点
- 每个任务点写目标、输入、输出、验收、依赖
- 标明需要用户确认的点

## MVP 边界

第一版只做：

- GitHub 仓库抓取
- 借鉴分析
- 共识落盘
- 验收说明

第一版不做：

- 新建全平台 installer
- 自动 hook
- 默认改写用户沟通风格
- 自动替用户拍板产品方向
- 把所有 skill 重构成新架构

## 失败处理

### gh 未登录

停止并提示：

```text
当前机器 GitHub CLI 未登录，先运行 gh auth status 检查。
```

### 仓库格式错误

停止并提示：

```text
这不是标准 GitHub 仓库链接，请提供 https://github.com/<owner>/<repo>。
```

### 抓取信息不足

照样可以输出观察，但必须降低确定性：

```text
README/关键代码不足，本轮只能做方向判断，不能写成确定抄法。
```

### 用户主题太泛

先收敛到一个主题：

```text
你要借鉴产品形态、工程结构、规则写法，还是分发方式？先选一个。
```

## 最小验收

任务完成时必须满足：

- 有独立共识目录
- 有 `consensus.md`
- 有 `consensus.json`
- JSON 格式可解析
- 明确“直接用 / 改造用 / 只参考 / 不抄”
- 明确用户可验证路径
- 没有新增超出用户确认范围的功能
