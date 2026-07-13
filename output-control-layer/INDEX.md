# 输出控制层 · 总索引

> 本文件的定位:这是"输出控制层"这一整套机制的**显式目录**——把分散在 6 个目录里的成果(规则正文、hook 脚本、注册配置、引用文件、设计稿、记忆)集中列出,标清每份文件的作用、关联和验收方式。当你或新会话不知道"这套东西到底由哪些文件组成、动哪个会影响哪个"时,先看这份索引,再去动文件。

> 名词速查:
> - **hook**(钩子):Claude Code / Codex 在特定时机(用户提交、调用工具前、会话开始等)自动触发的脚本,等于给 AI 加"自动反应"。
> - **信源**:规则的唯一权威正文。所有其他地方只允许"引用"它,不允许"复制"它,改一处全员生效。
> - **注入**:每轮对话开始前,hook 自动把信源内容塞进 AI 的上下文,确保 AI 这一轮"看得见"规则。
> - **拦截器**:在 AI 准备执行某个动作(改文件、跑危险命令)前,hook 先检查一遍,不合规就拦下来。
> - **context**(上下文):AI 这一轮能"看见"的全部文字,包含系统提示、规则、用户输入、工具结果。
> - **GC**:此处指文件归档/清理(garbage collection)。

---

## 一、整体结构(一张图先看清)

```
信源(1 份规则正文)
  └─► 注入器 hook(2 个,每轮/每会话塞进 context)
  └─► 触发稳定性短闸(Codex/DailyWork2 入口 + final gate)
  └─► 引用文件(8 个,只指向信源,不复制正文)
  └─► 拦截器 hook(6 个,执行前把关)
       └─► 注册在 2 份 hook 配置里(Claude Code + Codex)
  └─► 设计稿 + 历史(5 份,给人看,不参与运行)
  └─► 记忆痕迹(6 处,给新会话续上)
```

**一句话**:信源是唯一权威,注入器让 AI 每轮看得见,拦截器在动手前把关,引用文件让各工作区指过来,设计稿和记忆只是给人看的留痕。

---

## 二、信源(规则正文)

主 SKILL.md(被 hook 每轮注入)+ TWO-STAGE.md(按需 Read 的拆出文件):

| 文件 | 作用 | 备注 |
|---|---|---|
| `/Users/sure/shared-skills/output-control-layer/SKILL.md` | 主规则正文,含 0-7 节(二审/规则段/限制段/执行步长/铁律/四段交付/文档渲染门/两段制摘要/触发稳定性),约 9000 字符 | **改规则只改这里**。被 hook 注入。距 10000 字符上限仍需持续关注 |
| `/Users/sure/shared-skills/output-control-layer/TWO-STAGE.md` | 两段制完整规范(SKILL.md 第 6 节拆出版),含路径硬触发清单、触发稳定性相关修改、prompt 模板、二审判据、反馈重派格式、边界成本 | **派 sub-agent 前先 Read 这份**。不被 hook 注入,主 agent 按需自己读 |

### 2.1 触发稳定性补强(2026-06-29)

新增触发稳定性层,目的不是复制新规则,而是规定什么时候必须重新唤醒输出控制层:

- Codex 短版输出闸:见 `SKILL.md` 第 7.1 节和 `/Users/sure/.codex/AGENTS.md`
- 工具前二审:见 `SKILL.md` 第 7.2 节
- 长流程阶段闸:见 `SKILL.md` 第 7.3 节
- 正式输出 final gate:见 `SKILL.md` 第 7.4 节
- DailyWork2 本地输出短闸:见 `/Users/sure/DailyWork2/AGENTS.md`
- 验收脚本:`/Users/sure/shared-skills/output-control-layer/verify-trigger-stability.sh`

---

## 三、注入器 + 拦截器(8 个 hook 脚本,全部在 `/Users/sure/.claude/hooks/`)

### 3.1 注入器(2 个,负责"让 AI 每轮看得见规则")

| 文件 | 触发时机 | 作用 |
|---|---|---|
| `/Users/sure/.claude/hooks/inject_output_control.py` | Claude Code 每次 UserPromptSubmit(用户回车后) | 把 SKILL.md 正文塞进这一轮 context |
| `/Users/sure/.claude/hooks/inject_output_control_codex.py` | Codex SessionStart(新会话开始) | Codex 不支持每轮注入,只能会话开始注入一次 |

### 3.2 拦截器(6 个,负责"AI 动手前把关")

| 文件 | 触发时机 | 作用 |
|---|---|---|
| `/Users/sure/.claude/hooks/guard_dangerous_bash.py` | PreToolUse Bash | 拦危险命令(rm -rf / git reset --hard / DROP TABLE 等) |
| `/Users/sure/.claude/hooks/guard_edit_needs_read.py` | PreToolUse Edit/Write/MultiEdit | 改已存在文件前没 Read 过就拦 |
| `/Users/sure/.claude/hooks/guard_overexecute.py` | PreToolUse Edit/Write/MultiEdit | 用户最后一句是问句且无执行词时拦(防过度执行) |
| `/Users/sure/.claude/hooks/record_read_files.py` | PostToolUse Read | 记录读过哪些文件,供 guard_edit_needs_read 查 |
| `/Users/sure/.claude/hooks/record_user_prompt.py` | UserPromptSubmit | 记录最近 prompt,供 guard_overexecute 查 |
| `/Users/sure/.claude/hooks/nudge_subagent_dispatch.py` | Stop | 改了关键配置但没派 sub-agent 时,stderr 软提醒(不拦) |

**关联**:`record_*` 两个是"记录员",其他拦截器从它们记录的状态里查依据。删任何一个 record 都会让对应 guard 失效。

---

## 四、hook 注册位置(2 份配置)

| 文件 | 平台 | 作用 |
|---|---|---|
| `/Users/sure/.claude/settings.local.json` | Claude Code | 注册全部 Claude Code hook;**故意放 local 而非 settings.json**,避免 `cc switch` 切换 profile 时被覆盖(已验证:本轮设计就是为了规避 cc switch 覆盖) |
| `/Users/sure/.codex/hooks.json` | Codex | 注册 Codex 的 SessionStart hook |

**注意**:hook 脚本本身在 `.claude/hooks/` 里,但 Claude Code / Codex 不会自动发现,必须在这两份配置里**显式声明**才会触发。新增 hook 必须改这两份之一。

---

## 五、引用文件(8 份,指向 SKILL.md,不复制正文)

每个工作区都有一对 `AGENTS.md`(给 Codex 看) + `.claude/CLAUDE.md`(给 Claude Code 看),都是"只引用不复制"。

### 5.1 全局层(2 份)

| 文件 | 作用 |
|---|---|
| `/Users/sure/.claude/CLAUDE.md` | Claude Code 全局规则,输出控制层节已缩成 4 行引用 |
| `/Users/sure/.codex/AGENTS.md` | Codex 全局规则,引用 SKILL.md |

### 5.2 三个工作区(各 2 份,共 6 份)

| 工作区 | Codex 入口 | Claude Code 入口 |
|---|---|---|
| Daily Work | `/Users/sure/Daily Work/AGENTS.md` | `/Users/sure/Daily Work/.claude/CLAUDE.md` |
| content work | `/Users/sure/content work/AGENTS.md` | `/Users/sure/content work/.claude/CLAUDE.md` |
| study-research | `/Users/sure/study-research/AGENTS.md` | `/Users/sure/study-research/.claude/CLAUDE.md` |

**铁律**:这 8 份**只能含指向 SKILL.md 的引用 + 工作区专属内容**,不能复制 SKILL.md 正文。复制会导致改一处不同步,失去单一信源的意义。

---

## 六、设计稿与历史(5 份,给人看,不影响运行)

全部在 `/Users/sure/task_draft/consensus/output-control-layer/`:

| 文件 | 类型 | 作用 |
|---|---|---|
| `consensus.md` | v0 共识 | 最初对齐"要做什么"的快照 |
| `design.md` | v0 设计稿 | 最初的方案设计 |
| `PRD-v2-codex-parity.md` | PRD | Codex 对等化(让 Codex 也能用上这套)的需求,已闭环 |
| `Phase1-codex-feasibility-report.md` | 调研 | Codex hook 能力盘点 |
| `two-pass-pattern-trial-2026-06-24.md` | 实测记录 | 两段制(规则段/限制段)的实测记录 |
| `output-control-layer-trigger-stability-prd-v0.1.md` | PRD | 触发稳定性 vNext:解决长会话、连续执行、正式输出前闸门衰减问题 |

**特性**:删这 5 份**不影响**机制运行(已验证:运行只依赖 SKILL.md + hook + 配置),但删了之后新会话/外人看不懂"为什么这么设计"。建议保留。

---

## 七、记忆痕迹(6 处,给新会话续上下文)

| 文件/位置 | 作用 |
|---|---|
| `/Users/sure/.claude/memory/output-control-layer.md` | v0 项目记忆 |
| `/Users/sure/.claude/memory/output-control-layer-codex-parity.md` | Codex 对等化项目记忆 |
| `/Users/sure/.claude/memory/verification-and-evidence-layer.md` | 验证层体系记忆(相关项目,不属于本机制但有交集) |
| `/Users/sure/.claude/memory/current-position.md` | 含一段 output-quality-system 总指针(推断:指向本机制) |
| `/Users/sure/.claude/memory/timeline.md` | 2026-06-24 有 2 条相关时间线 |
| `/Users/sure/.claude/memory/lessons.md` | 2026-06-24 加了 hook-status-probe(hook 健康探针)教训 |

**关联**:新会话开局**不会**自动读这些(按全局规则,记忆是 lazy load),只有用户说"接上次/续 output 控制层"时才需要读。

---

## 八、验收命令(让你确认体系还活着)

复制下面命令到终端跑(zsh / bash 都行),逐条核对输出:

```bash
# 1. 信源还在,字符数大致正确(已验证基线:约 8085 字符)
wc -c /Users/sure/shared-skills/output-control-layer/SKILL.md

# 2. 8 个 hook 脚本都在
ls -1 /Users/sure/.claude/hooks/inject_output_control.py \
      /Users/sure/.claude/hooks/inject_output_control_codex.py \
      /Users/sure/.claude/hooks/guard_dangerous_bash.py \
      /Users/sure/.claude/hooks/guard_edit_needs_read.py \
      /Users/sure/.claude/hooks/guard_overexecute.py \
      /Users/sure/.claude/hooks/record_read_files.py \
      /Users/sure/.claude/hooks/record_user_prompt.py \
      /Users/sure/.claude/hooks/nudge_subagent_dispatch.py

# 3. 注册位置:Claude Code 的 hook 段在 settings.local.json 里(出现 inject_output_control 字样即可)
grep -l "inject_output_control" /Users/sure/.claude/settings.local.json

# 4. 注册位置:Codex hook 已注册
grep -l "inject_output_control_codex" /Users/sure/.codex/hooks.json

# 5. 8 份引用文件都指向 SKILL.md
grep -l "output-control-layer/SKILL.md" \
  /Users/sure/.claude/CLAUDE.md \
  /Users/sure/.codex/AGENTS.md \
  "/Users/sure/Daily Work/AGENTS.md" \
  "/Users/sure/Daily Work/.claude/CLAUDE.md" \
  "/Users/sure/content work/AGENTS.md" \
  "/Users/sure/content work/.claude/CLAUDE.md" \
  /Users/sure/study-research/AGENTS.md \
  /Users/sure/study-research/.claude/CLAUDE.md

# 6. 活体检查:在 Claude Code 里开一轮新对话,问一句"你这一轮 context 里有没有看见输出控制层的规则?"
#    应该:能复述 0-6 节大致结构。如果说没看到 → 注入器挂了,查 1 和 3。
```

**预期**:1 返回 ~8085;2 全部存在;3、4 各返回一个文件路径;5 返回 8 个路径;6 AI 能复述规则。任何一条不符,按"九、维护说明"对应章节排查。

---

## 九、维护说明(动东西前先看)

### 9.1 改规则正文 → 只改 SKILL.md
- 改 `/Users/sure/shared-skills/output-control-layer/SKILL.md` 一份就够。
- **不要**去 8 份引用文件里改规则——它们只是指针。
- 改完起一轮新对话验证(验收命令第 6 条),确认新规则确实进了 context。

### 9.2 加/删 hook → 改脚本 + 改配置,两步都要
- 加 hook:在 `/Users/sure/.claude/hooks/` 放脚本,然后去 `settings.local.json` 或 `hooks.json` 注册;只放脚本不注册等于没加(已验证:未在配置里声明的脚本不会触发)。
- 删 hook:反过来,先从配置摘掉,再删脚本;否则可能残留报错。
- 改 hook 行为:改完后**自己开一轮新对话实测**,不要只看代码——hook 不报错不等于生效(推断:基于一般 hook 调试经验,未验证)。

### 9.3 新增工作区 → 加 2 份引用文件,不要复制 SKILL.md
- 新工作区根目录加 `AGENTS.md` + `.claude/CLAUDE.md`,内容是"指向 `/Users/sure/shared-skills/output-control-layer/SKILL.md` + 工作区专属内容",**不要**把 SKILL.md 正文复制过去。
- 复制了规则正文 = 破坏单一信源 = 改规则时这个工作区不会同步。

### 9.4 cc switch / 切换 profile
- Claude Code hook 故意注册在 `settings.local.json` 而不是 `settings.json`,就是为了规避 `cc switch` 覆盖(已验证:本轮设计动机)。
- 如果哪天发现 hook 不触发了,先查 `settings.local.json` 还在不在,是否被某个工具误改成 `settings.json`。

### 9.5 设计稿和记忆能不能删
- 设计稿(`task_draft/consensus/output-control-layer/` 5 份)和记忆(`.claude/memory/` 6 处)**不影响运行**,但删了之后新会话/外人看不懂设计动机。建议保留,不主动 GC(文件清理)。
- 真要清理,走出新归旧规则(改 v1 → 旧的进 `_archive/`),不要硬删。

### 9.6 这份 INDEX 自己怎么维护
- 加新 hook / 新引用文件 / 新设计稿 → 顺手在对应章节加一行。
- 改了文件路径 → INDEX 这里也要改,否则下次找不到。
- 这份 INDEX **不是信源**,只是地图;改规则永远去 SKILL.md。
