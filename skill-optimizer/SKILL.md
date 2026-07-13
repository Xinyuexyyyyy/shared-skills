---
name: skill-optimizer
description: Skill 评测、锐评、优化与工作方式对齐的统一主入口。整合 critique（锐评）+ rubric（8维评分）+ optimizer（优化循环+棘轮），并吸收原 setup-daily-work-skills 的方法论职责：先对齐“要改什么、按什么口径改、怎么验收”，再进入优化闭环。触发词：评测skill、skill评分、优化skill、skill质量检查、锐评skill、review skill、对齐工作方式、校准协作方式。当用户提到 skill 质量、评分、优化、打分、锐评，或想先对齐本工作区协作方式时使用。
status: stable
---

# Skill Optimizer — Skill 治理统一入口

## 定位

对 SKILL.md 进行**工作方式对齐 → 量化评分 → 深度锐评 → 定向优化 → 棘轮验证**的完整闭环。

**依赖**：Python 3（无外部 API key，无 LLM 调用）

它既是工具，也是方法论主入口。

- 工具部分：评分、锐评、优化、回滚、日志
- 方法部分：先对齐目标、协作方式和验收口径，再进入优化

`setup-daily-work-skills` 现在只保留为兼容入口，不再维护第二套独立方法论。

## 它在防什么坑

- skill 看起来很多，但没人知道先优化哪个
- 只谈分数，不谈对齐方式和验收标准
- 评分、锐评、优化、回滚各做各的，缺少统一入口
- 用户还没说清要改什么，就先开工

## 什么时候用

- 用户要评测某个 skill 的质量
- 用户要锐评、优化、回滚 skill
- 用户想先对齐这次 skill 治理的工作方式
- 用户想把一套 skill 的评价与优化收成统一闭环

## 不什么时候用

- 用户只是在写业务功能，不关心 skill 质量
- 用户要的是普通任务拆解，不是 skill 治理
- 用户已经明确要用别的专属 skill，不需要先评测

## 默认工作方式

先对齐，再评分，再锐评，再优化。

如果用户一开始只说“帮我改 skill”，默认先补这 3 件事：
- 改什么
- 改到什么程度算好
- 最终怎么验收

如果关键分歧不在工具层，就先回到 `task-analyze`。

对齐阶段默认读取：
1. `AGENTS.md`
2. `docs/agents/issue-tracker.md`
3. `docs/agents/triage-labels.md`
4. `docs/agents/domain.md`
5. `.claude/CLAUDE.md`
6. `CONTEXT.md`
7. `.claude/memory/current-position.md`
8. `.claude/memory/timeline.md`
9. `skill-index.json`

然后收成一份“工作方式确认单”：
- 我理解的目标
- 我会怎么推进
- 哪些地方先问
- 哪些地方不会擅自做
- 做完怎么一眼验收

## 四阶段流程

```
Phase 0: Align（对齐）    — 先确认要改什么、怎么推进、改到哪、怎么验收
Phase 1: Score（评分）    — 8维静态分析，量化输出
Phase 2: Critique（锐评） — 扫描文件，落盘 critique/manual，并保留可选深评 prompt
Phase 3: Optimize（优化） — 生成改进 prompt → Claude 生成 → 应用编辑 → 重评
Phase 4: Ratchet（棘轮）  — 涨分保留，降分回滚
```

## 用户可见检查点

### 检查点 1：先对齐目标

先说清：
- 这轮到底改哪个 skill
- 优先改什么问题
- 默认按什么工作方式推进
- 做成什么效果算好

### 检查点 2：先看分数和锐评，再动手

不要直接改。至少先经过：
- `score`
- `critique`

### 检查点 3：优化后必须能复核

最后要能回答：
- 分数有没有变
- 低分项有没有改善
- 如果变差了，能不能回滚

### 检查点 4：入口路由要能回归

这轮如果改到了 skill 触发词、索引、推荐逻辑或治理展示层，结束前至少跑一次：

```bash
cd /Users/sure/Daily\ Work
python3 skills/skill-recommend-regression.py
```

通过标准：
- 输出最后一行是 `OK`
- 常见问法的 top1 命中不漂移
- 结果列表里不再出现同一 `short_id` 的重复推荐

## 8维评分体系（100分）

| 维度 | 权重 | 评分方式 |
|------|------|---------|
| Frontmatter质量 | 8 | name规范、description含触发词 |
| 工作流清晰度 | 15 | 步骤有序号、输入输出清晰 |
| 边界条件覆盖 | 10 | 异常/超时/fallback 关键词 |
| 检查点设计 | 7 | 用户确认点 |
| 指令具体性 | 15 | 代码示例、参数说明、无模糊词 |
| 资源整合度 | 5 | 引用路径、依赖声明 |
| 整体架构 | 15 | 标题层次、模块化 |
| 实测表现 | 25 | **Claude 在对话中评估**，或启发式降级 |

## CLI 用法

### Phase 0 — 对齐

```text
先在对话里说清：你要优化哪个 skill、优先改哪类问题、什么结果算好。
```

### Phase 1 — 评分

```bash
python skill.py score <skill_path>
```

**示例**：
```bash
cd /Users/sure/DailyWork2/skills/skill-optimizer
python3 skill.py score ../harvest-tool
```

输出：结构化评分报告，含各维度得分和最低分维度提示。

### Phase 2 — 锐评

```bash
python skill.py critique <skill_path>
```

**Claude 使用流程**：
```
1. 运行 critique 命令
2. 自动生成 `critique.md` + `manual.md`
3. 如需更重的人审，再把附带 prompt 发给 Claude 做深评
```

### Phase 3 — 优化（单轮）

```bash
# Step 1: 生成改进 prompt
python skill.py prompt <skill_path> <dimension>

# Step 2: Claude 根据 prompt 生成改进内容，保存到文件

# Step 3: 应用编辑 + 棘轮
python skill.py optimize <skill_path> <dimension> <edit_file>
```

**完整优化循环（由 Claude 编排）**：
```
用户：优化 harvest-tool
→ Claude:
  1. python3 skill.py score ../harvest-tool → 基线评分（如 62/100）
  2. 找最低分维度（如 boundary 3/10）
  3. python3 skill.py prompt ../harvest-tool boundary → 获取改进 prompt
  4. Claude 根据 prompt 生成改进内容，保存到 /tmp/edit.md
  5. python3 skill.py snapshot ../harvest-tool → 打快照
  6. python3 skill.py optimize ../harvest-tool boundary /tmp/edit.md → 应用+重评
  7. 比较分数：涨分保留，降分回滚
  8. 重复直到满意
```

### 其他命令

```bash
# 快照管理
python skill.py snapshot <skill_path>          # 打快照
python skill.py restore <skill_path> <snap>    # 从快照恢复

# 状态查询
python skill.py status <skill_name>            # 查看优化历史
python skill.py health <skills_root>           # skills 目录健康检查

# 日志
python skill.py log <skill> <action> <result>  # 记录执行日志
```

## 数据目录

```
output/skill-optimizer/
├── final/
├── draft/
├── assets/
└── runs/
    ├── snapshots/      # 棘轮快照
    │   └── {skill_name}/{ts}/
    ├── scores/         # 评分历史
    │   └── {skill_name}.json
    ├── logs/           # 优化日志 + 执行日志
    │   ├── round-{ts}.md
    │   └── executions/{date}.jsonl
    └── critiques/      # 锐评产出
        └── {skill_name}/
            ├── critique.md
            └── manual.md
```

## 与原版的主要变更

| 原版 | 当前版 | 原因 |
|------|--------|------|
| qwen3.5-flash API | **Claude 对话中完成** | 效果更好，无需 API key |
| sessions_spawn | **inline 扫描 + Claude 锐评** | Claude Code 无 sessions_spawn |
| ~/.openclaw/ 硬编码 | **参数传入 + 环境变量** | 适配任意目录结构 |
| DASHSCOPE_API_KEY | **已删除** | 无外部 LLM 调用 |
| critique 独立 skill | **整合为 Phase 2** | 统一入口，流程闭环 |

## 使用示例

```
用户：评测一下 harvest-tool
→ Claude 运行: python3 skill.py score ../harvest-tool
→ 输出评分报告
→ Claude 分析最低分维度

用户：锐评一下 harvest-tool
→ Claude 运行: python3 skill.py critique ../harvest-tool
→ 自动落盘 critique/manual，必要时再用 prompt 做深评

用户：优化 harvest-tool 的边界条件
→ Claude:
  1. score 获取基线
  2. prompt 生成改进 prompt
  3. 自己生成改进内容
  4. optimize 应用 + 棘轮
  5. 报告结果

用户：先对齐一下我现在的 skill 工作方式
→ Claude：
  1. 先读取规则、记忆和技能索引
  2. 输出“工作方式确认单”
  3. 再决定是否进入 score / critique / optimize
```

## 最小验收

这轮至少要做到：

1. 能先把对齐目标说清楚
2. 能说清默认工作方式和验收口径
3. 能进入 score / critique / optimize 任一条
4. 能说清改动后怎么验收
5. 能回滚到上一个稳定版本
5. 不是只有工具命令，而是有方法论入口

---

## 产出去向

产出物落盘与命名遵循全局规范 `~/shared-skills/STORAGE-SPEC.md`：产出可存任何位置，但每件正式产出须在所属任务 `tasks/<任务>/artifacts.md` 登记坐标；用语义名不用纯时间戳；同主题反复生成覆盖或归档旧版。
