---
name: skill-dashboard
status: stable
description: >
  Skill / 功能管理仪表盘。解决"agent 遗忘自己有什么能力"和"用户记不住开发了什么功能"两大痛点。
  触发词："打开技能面板"、"skill dashboard"、"看看我的技能"、"你有什么 skill"、"你有什么能力"、"展示所有功能"。
  当用户询问自己有哪些能力、功能、skill 时触发。
---

# Skill Dashboard — 技能管理仪表盘

## 一句话定位

**Agent 的能力目录 + 用户的记忆辅助工具**。让 agent 能回答"我有什么 skill"，让用户一览所有功能状态。

## 响应流程（节点）

收到触发词后按以下节点顺序处理，每个节点的输入/输出都明确：

1. **判断意图节点** — 输入：用户原话。输出：判定走"模式 A 列出"还是"模式 B 开面板"。问"有什么/能做什么"走 A；说"打开面板"走 B。
2. **读取索引节点** — 调用：读取 `~/DailyWork2/skills/skill-index.json`。输入：索引文件。输出：已入库 skill 列表（含 status、triggers）。读不到则进异常处理。
3. **组织响应节点** — 输入：索引数据。输出：按"主链 / 治理·调研·专项 / 公共工具层 / 内置"分类的回答，或面板访问地址。
4. **校验节点** — 调用：必要时跑 `skill-recommend-regression.py`。输入：响应内容。输出：确认未编造、状态准确、子包已提及后再返回用户。

## 触发条件

### 高优先级（必须触发）
- "打开技能面板"
- "skill dashboard"
- "看看我的技能"
- "你有什么 skill"
- "你有什么能力"
- "展示所有功能"
- "我有哪些工具"

### 中优先级（结合上下文）
- "你能做什么"
- "你支持什么"
- "这个功能在哪里"
- "之前写的那个工具"

## 两种响应模式

### 模式 A：列出 Skill（对话中）

当用户问"你有什么 skill"时，读取 `~/DailyWork2/skills/skill-index.json`，按分类回答：

```
我当前有若干已扫描入库的 skill，先按“你现在最可能要用哪类”回答：

【主链 Skills】
- task-analyze：新需求先分析
- task-decompose：需要时再拆任务
- closeout：结束时统一收尾

【治理 / 调研 / 专项 Skills】
- skill-optimizer：skill 治理统一入口，先对齐工作方式，再评分、锐评、优化
- harvest-tool：借鉴 GitHub 成熟项目并沉成共识
- research：调研总入口（含 academic / competitive / discovery / comprehensive 子包）
- paper-reader、interview-writer、remote-openclaw、project-sop 等按场景使用

【本机公共工具层】
- shared-skills/_tools/：scan-skills.py、skill-trace.py、skill-recommend.py、skill-governance.py、skill-recommend-regression.py
- 这层负责扫描、追踪、推荐、治理和回归，不是业务 skill

【内置 Skills】
claude-api、update-config、keybindings-help、simplify、fewer-permission-prompts、loop、schedule、init、review、security-review
```

如果用户问的是 skill 治理相关问题，优先提醒：
- `skill-optimizer` 现在是统一主入口
- `setup-daily-work-skills` 只是兼容入口，不是第二套体系

### 模式 B：打开可视化面板（推荐）

当用户说"打开技能面板"时：

1. **如果本地服务器已运行**：
   > 技能面板已就绪：http://localhost:18080/skill-dashboard.html
   > 在 OpenCove 网页窗口中填入即可查看。

2. **如果本地服务器未运行**：
   > 请运行以下命令启动面板服务器：
   > ```bash
   > cd ~/DailyWork2/skills && python3 -m http.server 18080
   > ```
   > 然后在浏览器或 OpenCove 中访问：http://localhost:18080/skill-dashboard.html

## 异常处理 / 边界条件

面板和列表都依赖外部文件与本地服务，下列情况必须按"条件 → 处理"应对，**不允许凭记忆编造 skill**：

**条件**：`skill-index.json` 不存在、为空或解析失败（JSON 错误）
**处理**：不要凭记忆列 skill。明确告诉用户索引缺失，提示先运行 `cd ~/DailyWork2/skills && python3 scan-skills.py` 重建；若重建仍失败，则报具体报错行，绝不硬编造。

**条件**：启动面板时 18080 端口被占用（`Address already in use`）
**处理**：先判断是否已有面板在跑——能访问 `http://localhost:18080/skill-dashboard.html` 就直接复用，不重复起服务；确属别的进程占用，则换端口（如 18081）启动并把新地址告诉用户，不强杀未知进程。

**条件**：扫描结果为 0 个 skill 或明显偏少
**处理**：不要假装"没有 skill"。提示可能扫描路径不对或软链断了，建议跑 `python3 scan-skills.py --tree` 复核层级，并如实报告实际扫到的数量。

**条件**：`/autolink fix`（scan-skills.py 全量扫描）执行失败或超时
**处理**：保留原始报错输出给用户，标明哪个工作区失败；不谎报"已修复"。失败时回退到只读列出已有 skill，等用户决定是否重试。

**条件**：用户问的功能在索引里查不到
**处理**：如实说"索引里没有匹配项"，再用 triggers/description 做模糊检索给出最接近的候选，绝不杜撰一个不存在的 skill 名。

## Action 速查

把本 skill 会用到的命令收在一处,照抄即可,不用翻正文:

| 你要做什么 | Action（命令） |
|-----------|---------------|
| 刷新 skill 索引快照 | `cd ~/DailyWork2/skills && python3 scan-skills.py` |
| 查看完整层级树 | `cd ~/DailyWork2/skills && python3 scan-skills.py --tree` |
| 启动可视化面板 | `~/DailyWork2/skills/start-dashboard.sh`（或 `python3 -m http.server 18080`） |
| 看使用统计 | `cd ~/DailyWork2/skills && python3 skill-trace.py` |
| 回归校验推荐链路 | `cd ~/DailyWork2 && python3 skills/skill-recommend-regression.py` |

面板地址固定为 `http://localhost:18080/skill-dashboard.html`。

## 数据更新

- 索引文件：`~/DailyWork2/skills/skill-index.json`
- 扫描命令：`cd ~/DailyWork2/skills && python3 scan-skills.py`
- 使用统计：`cd ~/DailyWork2/skills && python3 skill-trace.py`
- 双击打开前刷新快照：`cd ~/DailyWork2/skills && python3 scan-skills.py`
- 一键启动服务器：`~/DailyWork2/skills/start-dashboard.sh`

## 快速验收

如果你想一眼确认“推荐链路有没有歪”，先跑：

```bash
cd /Users/sure/DailyWork2
python3 skills/skill-recommend-regression.py
```

通过标准：
- 输出最后一行是 `OK`
- `先对齐一下工作方式` 命中 `skill-optimizer`
- `你有什么 skill` 命中 `skill-dashboard`
- `帮我规划一个复杂任务` 命中 `task-crafter`

## 自动链接管理（Autolink）

skill-dashboard 负责管理跨工作区的 skills 自动链接系统。

### 职责
- **扫描时自动修复**：`scan-skills.py` 每次运行都会检查所有工作区的 `skills/`，自动为缺少 `CLAUDE.md` 的 skill 创建软链接
- **launchd 常驻守护**：后台 `fswatch` 监听三个工作区，实时响应文件变化
- **状态汇报**：索引中 `summary.autolink` 字段记录每个工作区的链接状态

### 用户指令

| 指令 | 响应 |
|------|------|
| `/autolink status` | 显示三个工作区的 autolink 状态（已修复/已就绪/缺少 SKILL.md） |
| `/autolink fix` | 手动触发 scan-skills.py 全量扫描+修复 |
| `/autolink log` | 显示 launchd 服务的最近日志 |

> ⚠️ `/autolink fix` 会跨三个工作区批量创建/修复软链接,属于会改文件系统的写操作。执行前**先确认**:向用户说明将扫描哪几个工作区、预计动哪些 skill,等用户确认后再跑,不要默默全量执行。

### 索引中的 autolink 数据

```json
"summary": {
  "autolink": {
    "total_fixed": 0,
    "total_ok": 25,
    "total_missing": 0,
    "by_workspace": {
      "study-research": {"fixed": 0, "already_ok": 11, "missing": 0},
      "content work": {"fixed": 0, "already_ok": 2, "missing": 0},
      "DailyWork2": {"fixed": 0, "already_ok": 33, "missing": 0}
    }
  }
}
```

### launchd 服务信息
- **Label**: `com.user.skills-autolink`
- **日志**: `~/.claude/skills-autolink.log`
- **脚本**: `~/.claude/skills-autolink.sh`

## 使用场景示例

```
用户：你有什么 skill？
→ 读取 skill-index.json → 优先按主链 / 治理 / 专项场景列出

用户：打开技能面板
→ 检查服务器是否在运行 → 给出访问地址或启动命令

用户：我之前写的那个论文阅读工具叫什么？
→ 搜索索引中的 triggers 和 description → 回答 "paper-reader"

用户：帮我分析一下竞品
→ 💡 检测到你有 'research-competitive' skill 可以做竞品分析，要用吗？

用户：读篇论文
→ 💡 检测到你有 'paper-reader' skill（三遍阅读法），要用吗？

用户：我想先对齐一下你现在的工作方式，再改 skill
→ 💡 优先走 `skill-optimizer`，它现在负责“先对齐工作方式，再评分/锐评/优化”

用户：我有哪些公共工具
→ 💡 先看 `~/shared-skills/_tools/README.md`，那里列着公共工具层的入口和验收命令
```

## 规则

1. **不要编造 skill**。必须从 `skill-index.json` 读取，不能凭记忆回答。
2. **优先推荐面板**。对话列出是备选，可视化面板是首选查看方式。
3. **状态要准确**。stable/draft/built-in 状态从索引中读取，不能猜测。
4. **子包要提及**。research 主 skill 下有 4 个子包，不要只提主 skill。
5. **主入口要说清**。涉及 skill 治理或工作方式对齐时，默认先提 `skill-optimizer`，不要再把 `setup-daily-work-skills` 说成并列主入口。
