---
name: project-sop
description: 项目全流程管理skill。创建项目、头脑风暴、拆任务、写蓝图、开发、测试、收尾。当用户说新项目、brainstorm、拆任务、写蓝图、开始开发、测试、项目结束时使用。
status: stable
agents: research
---



# Project SOP Skill — 项目全流程管理

## 定位

包装 project-sop Blueprint 的 CLI，封装为 Skill 层。DailyWork2 版本只用于轻量项目 SOP 草稿和外部项目过程记录，不接管 DailyWork2 根目录 `tasks/` 的正式任务系统。

## 触发词（自动路由）

| 用户说（示例） | 路由到 | 节点 |
|--------------|--------|------|
| `新项目 <名字>` / `建个项目` | `new` | ① 建立 |
| `brainstorm` / `聊聊想法` / `头脑风暴` | `brainstorm` | ② 头脑风暴 |
| `quality <分数>` / `质量确认` | `quality` | ②→③ 质量门控 |
| `拆任务` / `落实` / `写计划` | `plan` | ③ 落实任务 |
| `写蓝图` / `定方案` / `blueprint` | `blueprint` | ④ 写蓝图 |
| `开始开发` / `develop` / `开始干活` | `develop` | ⑤ 开发 |
| `测试` / `debug` / `调试` | `test` | ⑥ 测试debug |
| `close` / `项目结束了` / `收尾` | `close` | ⑦ 收尾 |
| `项目状态` / `进度` | `status` | 查询当前节点 |

## 项目反馈关联

在任意节点，当用户描述问题时：
1. 自动识别当前项目（从 state.yaml 读取 current_project）
2. 调用 `feedback` skill，`source` 填项目名
3. 向用户确认：「检测到反馈，已关联到项目 {name}，要记下来吗？」

DailyWork2 边界：
- 正式跨会话任务仍建在 `~/DailyWork2/tasks/<task>/`。
- `project-sop` 只写 `~/DailyWork2/task_draft/project-sop/`，用于项目想法、蓝图和开发日志草稿。
- 不写 `~/.openclaw/`，不调用旧 registry，除非用户明确要求兼容旧 OpenClaw。

## 数据结构

```
~/DailyWork2/task_draft/project-sop/{project}/
├── blueprint/
│   ├── overview.md      # 项目方向
│   └── progress.md      # 任务清单 + 验收标准
├── logs/
│   ├── brainstorm-*.md  # 头脑风暴
│   ├── round-*.md       # 开发日志
│   ├── test-*.md        # 测试记录
│   └── debug-*.md        # 调试记录
└── state/
    └── state.yaml       # 当前节点状态
```

## 操作（Actions）

### `new` — 节点①：建立项目

输入：`name`（项目名），`description`（一句话描述）

输出：创建目录结构，初始化 overview + state.yaml + `~/.claude/memory/project-sop-index.md` 索引

---

### `brainstorm` — 节点②：头脑风暴

输入：`project`（项目名），`content`（用户想法，可选）

**核心原则**：输入 ≠ 结论。必须经过独立分析才能落地。

**输入类型适配流程**：

```
brainstorm 触发
    ↓
识别输入类型
    ├── Harvest 共识输出
    │       → 扒源码验证可行性（架构/算法部分）
    │       → 结论：保留 / 砍掉 / 改写
    │
    ├── 自然语言讨论
    │       → 提炼用户意图
    │       → 识别潜在风险和未明确定义
    │       → 提出反共识或独特见解
    │
    ├── 外部参考资料（URL/文档/代码）
    │       → 抓取关键段落
    │       → 与现有系统对照
    │
    └── 混合输入（上述多种）
            → 分别处理各部分
            → 整合冲突和矛盾

    **两段式流程**：
1. 🔥 **轮1 — 高温暖场（发散）**：列出3个以上不同方向，每条含方案名称+核心思路+潜在风险/分歧点。AI 只扩边，不评估。
2. ❄️ **轮2 — 低温收缩（整合）**：AI 整合分歧，给出推荐方向并说明理由。
3. 📋 **质量自评**：AI 自我评价，格式如下：

```
## 质量自评
- 总分：X/10
- 风险点：（2-3条）
- 能不能过：（>=6分写"能过，进入 plan"，<6分写"不过，需重跑"）
```
4. ✅ **用户确认**：告知用户推荐方向，用户决定是否接受、换方向、或要求重跑。
5. 🚫 **质量门控**：评分 < 6 → 必须重跑 brainstorm，不推进节点；评分 >= 6 → 可进入 plan。
```

**评估维度**（对每个方案都要回答）：
- **可行性**：源码/文档是否支持这个方案？
- **成本**：XYY 机器 8GB 内存是否能承受？
- **维护**：会不会变成空坟场（建了没人填）？
- **核心价值**：砍掉某层之后系统是否仍然成立？

输出：`logs/brainstorm-YYYYMMDD-HHMMSS.md`（节点暂不推进，等 `quality` 确认后推进）

**流程**：brainstorm → 填写质量自评 → `quality <分数>` → 节点推进到② → `plan`

---

### `quality` — 质量门控

输入：`project`（项目名），`score`（质量评分 0-10）

- score < 6 → 拒绝推进节点，要求重跑 brainstorm
- score >= 6 → 推进 state → ②，进入 plan 节点

---

### `plan` — 节点③：落实任务

输入：`project`（项目名），`content`（任务描述，可选）

输出：创建/更新 `progress.md` 任务清单，推进 state → ③

---

### `blueprint` — 节点④：写蓝图

输入：`project`（项目名），`content`（方案描述，可选）

输出：补充 `progress.md` 验收标准，推进 state → ④

---

### `develop` — 节点⑤：开始开发

输入：`project`（项目名），`note`（开发说明，可选）

输出：创建 `logs/round-YYYYMMDD-HHMMSS.md`，推进 state → ⑤

---

### `test` — 节点⑥：测试debug

输入：`project`（项目名），`content`（测试/调试内容）

输出：创建 `logs/test-*.md` 或 `logs/debug-*.md`，推进 state → ⑥

---

### `close` — 节点⑦：收尾

输入：`project`（项目名）

输出：
1. 调用 `project-archiver` skill 归档 logs → progress
2. 更新 `~/.claude/memory/project-sop-index.md` 项目状态
3. 锁定蓝图（progress.md 标记 `## 🔒 已锁定`）

---

### `status` — 查询状态

输入：`project`（项目名，可选，默认当前项目）

输出：当前节点 + 各节点状态 + 待归档日志数

## 边界条件

### 错误场景

### 文件读取失败
**条件**：访问本地文件或远程资源时返回 404 或 IO 异常。
**处理**：如果读取失败，则记录详细日志并 fallback 至默认配置文件继续运行。

### 网络请求超时
**条件**：外部 API 响应时间超过 30 秒设定阈值。
**处理**：如果连接超时，则触发指数退避重试，最多 3 次后切换备用源。

### 参数校验缺失
**条件**：输入数据缺少必填字段或类型不匹配。
**处理**：如果校验失败，则抛出明确错误码，阻断流程并提示用户修正。

**限制与超时说明**：
系统并发数 limit 严格限制为 10。单次任务最大执行时间 limit 为 60 秒。若连续 error 计数达 5 次，系统将自动熔断并通知运维人员介入。
