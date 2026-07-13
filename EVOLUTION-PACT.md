# 进化公约 — 能力怎么开分支、怎么收回主线

> 日期：2026-06-18
> 配套：[ARCHITECTURE.md](ARCHITECTURE.md)、[EXPORTS.md](EXPORTS.md)、[STORAGE-SPEC.md](STORAGE-SPEC.md)
> 解决的问题：新能力（skill / 规则 / hook）想试，但又怕污染主线、怕一改全局到处崩。
> 核心思想：**任何新能力先在"分支"上试，验证好了才"收回"主线；不好就丢弃，主线全程零污染。** 借 git 版本控制思想，落成纯 markdown + 目录约定，不上任何系统。

---

## 一、三个状态（一个能力的一生）

每个 skill 在 frontmatter 标 `status`：

| status | 含义 | 是否进全局入口 | 是否进开源导出 |
|---|---|---|---|
| `draft` | 分支态：正在试，未验证 | 否 | 否 |
| `stable` | 主线态：验证过，可用 | 是 | 是（按 EXPORTS） |
| `deprecated` | 退役态：不再维护 | 否（撤入口，实体留档） | 否 |

**铁律**：只有 `stable` 进全局 `~/.claude/skills/` 入口、只有 `stable` 被 EXPORTS 导出到开源仓库。draft 永远关在分支里。

---

## 二、开分支（试）

新能力不直接建在权威源 + 挂全局入口。两种隔离档位，按改动大小选：

**轻量档：`status: draft` + 单工作区试用**
1. 在某个工作区的 `skills/<新skill>/` 下建，frontmatter 写 `status: draft`。
2. 只在这个工作区用，不挂全局入口 `~/.claude/skills/`。
3. 适合：新 skill、对已有 skill 加实验性段落。

**重量档：git worktree 隔离**
1. 对 shared-skills / 开源仓库这类 git 仓库，用 `git worktree` 开一个副本分支改。
2. 主线工作目录完全不受影响。
3. 适合：要动多个文件、改架构、怕中途反悔的大改。

---

## 三、验证（在分支内）

收回主线前，draft 必须过这三关（按能力类型取适用的）：

1. **真实任务跑一遍**：拿一个真实需求在分支里走通，不是空想。
2. **评分**：能力类 skill 用 `skill-optimizer` 评分（够线才升 stable）。
3. **产出登记**：验证产生的产物按 STORAGE-SPEC 登记到 `tasks/<任务>/artifacts.md`，留下"它确实work过"的证据。

验证不过 → 回到第二步继续改，或直接丢弃。

---

## 四、收回主线（收）

验证通过后，把能力从分支收回主线：

**轻量档收回**：
1. 改 frontmatter `status: draft → stable`。
2. 若是通用能力，移到对应权威源（通用→shared-skills，学术→study-research）。
3. 挂全局入口：`ln -sfn <权威路径> ~/.claude/skills/<name>`（一个 skill 一个入口，不加前缀）。
4. 若需开源，更新 EXPORTS.md 加一条，再导出。
5. `scan-skills.py` 重建索引，确认零断链。

**重量档收回（worktree）**：
1. 在副本里验证通过。
2. `git merge` 回主分支。
3. 同上挂入口、更新 EXPORTS。

---

## 五、丢弃（不好就扔，主线零污染）

验证不通过、或决定不要了：

**轻量档**：删掉 `skills/<新skill>/` 草稿目录。因为它从没挂全局入口、从没进 EXPORTS，**主线没有任何指针指向它，删了零残留**。

**重量档**：删掉 worktree 副本（`git worktree remove`）。主分支从头到尾没动过。

这就是"分支"的意义：**试错的成本被关在分支里，主线永远是验证过的状态。**

---

## 六、退役（stable 用旧了）

一个 stable 能力不再需要：
1. 改 `status: stable → deprecated`。
2. 撤全局入口软链（`rm ~/.claude/skills/<name>`），实体目录留档（不删，供历史指针/回溯）。
3. 从 EXPORTS.md 移除，下次导出不再带它。

参考本次重整：`setup-daily-work-skills`、`research-academic` 就是这样退役的（撤入口、留实体）。

---

## 七、和其他公约的关系

- **谁是主线**：由 EXPORTS.md 定义的两个权威源（shared-skills 通用层 / study-research 学术线）。
- **产出去哪**：验证产物按 STORAGE-SPEC 登记。
- **记忆怎么留**：进化过程中的决策写进对应工作区的 `tasks/<任务>/`，收回/丢弃的结论写一行进 timeline。

一句话总括：**主线只装验证过的（stable），分支承担所有试错，收回靠改 status + 挂入口，丢弃靠删分支——主线永远干净。**
