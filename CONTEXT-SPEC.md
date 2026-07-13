# CONTEXT-SPEC — 上下文调用规范

> 日期：2026-06-19
> 解决：开局读太多 / 费 token / 聊久了规则漂移。把"什么时机读什么、读多深、何时停"成文。
> 借鉴：memoir 的 "token 房租"（flat 大文件每改一点就失效整段缓存）、Continuous-Claude 的 "compound not compact"（按需召回而非全灌）。
> 配套：全局 `~/.claude/CLAUDE.md` 的开局协议是本规范的执行锚点。

---

## 一、核心原则

1. **规则先行，记忆按需**（lazy load）：开局只读规则，记忆等明确意图后再读。
2. **够用即停**：读到能干活就停，不把整个 memory 灌进来。
3. **按 scope 取，不整篇塞**：大文件（timeline、lessons）按需截取，不全读。
4. **token 是房租**：大 flat 文件少读、少全读；经常变的（任务状态）和很少变的（长期记忆）分开读。

---

## 二、什么时机读什么（分层）

### 开局（每次会话开始）—— 只读规则层
- `~/.claude/CLAUDE.md`（全局规则）
- 当前工作区 `.claude/CLAUDE.md` + `AGENTS.md`
- **不读**任何 memory 文件。

### 第一句之后（知道要干什么了）—— 按意图读
| 用户意图 | 读什么 | 读多深 |
|---|---|---|
| 接续某个已有任务 | `.claude/memory/tasks/INDEX.md` 定位 → 进该任务 `state.md` | 先 INDEX 一屏，再单个任务 |
| 接上次进度 | `current-position.md` + `timeline.md` | timeline 只读最近 3-5 条，不全读 |
| 涉及历史决策 | `decisions.md` | 按主题 grep，不全读 |
| 要避坑 | `lessons.md` | 按 scope 标签 grep 相关条，不整篇 |
| 要连远程设备 | `~/shared-skills/DEVICES.md` | 查对应设备行 |
| 纯新任务 / 一次性问答 | 不读记忆 | — |

### 执行中 —— 产出物按坐标取
- 要找以前的产出 → 查任务的 `artifacts.md`，按坐标取，不翻整个 output/。

---

## 三、何时停（防贪读）

- 读到"能开始干这一步"所需的最小信息 → 停。
- 不为"可能用得上"提前读 decisions/lessons 全文。
- 一个任务的家（tasks/<任务>/）四件套里，开局先读 state.md 一个；artifacts/context/log 用到再读。

---

## 四、防 token 膨胀的具体动作

1. **timeline 不全读**：43KB 的 timeline 全读是浪费，只取最近几条或按关键词 grep。
2. **lessons 按 scope grep**：`grep -B1 -A6 "scope=.*<当前场景>" lessons.md`，不整篇加载。
3. **大文件该瘦身就提醒**：单个记忆文件过大（如 timeline 超 30KB）时，提议归档旧条目到 `-archive`。
4. **长会话定期重锚**：聊很久后，规则会在上下文里稀释；关键决策点重述一句"当前任务/必守规矩"，对抗漂移。

---

## 五、自检（每次要读记忆前问一句）

1. 这一轮真用得上这个文件吗？用不上就不读。
2. 要全读还是截取？默认截取。
3. 是不是开局就在灌记忆？是 → 停，等用户说意图。
4. 读完够开始干了吗？够了就停，别继续翻。
