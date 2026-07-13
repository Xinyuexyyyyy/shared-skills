# Skill 产出物存储 + 命名规范

> 日期：2026-06-18
> 配套：[ARCHITECTURE.md](ARCHITECTURE.md)、任务级记忆 `<工作区>/.claude/memory/tasks/`
> 目的：终结"skill 乱存、不知道放哪、事后找不到"。本文件是所有 skill 产出落盘的唯一规矩，新 skill 也照此。

---

## 一、一条铁律（先记这条，其余都是展开）

**产出物的物理位置可以在任何地方，但每件正式产出必须在所属任务的 `tasks/<任务>/artifacts.md` 里登记一条坐标。**

存哪不重要，登记了就找得回。"乱存"之所以变成"丢失"，是因为没登记，不是因为位置不对。

---

## 二、产出落哪（按类型）

| 产出类型 | 落盘位置 | 命名 |
|---|---|---|
| **过程产物**（草稿、中间件、调试样本） | `<工作区>/output/<skill>/runs/<slug>/` | `<slug>` = 任务短名，不用纯时间戳 |
| **正式成品**（文章、报告、PPT、综述） | `<工作区>/output/<任务名>/` | 用任务名建目录，成品放里面 |
| **调研共识** | `<工作区>/task_draft/consensus/<任务>-<日期>/` | 沿用现状 |
| **跨设备 / 云端产物**（Win 文件、飞书、远端服务器） | **物理留在原处**，不强行搬到 Mac | 只在 artifacts.md 登记坐标 + 取回方式 |
| **skill 自身运行态**（如 interview 的 state） | `<工作区>/.claude/skills/<skill>/state/` 或任务的家 | — |
| **证据包**（调研层/任务层出口的机读证据，非给人报告） | `<工作区>/.claude/memory/tasks/<任务>/evidence/<步骤-slug>/` | `manifest.json + data.jsonl + 可选 sources.json` |

工作区根：DailyWork / ContentWork / study-research（不带空格）。

### 证据包(Evidence Pack)——规定步骤产数据不产报告

调研层、任务层的**出口**不再产"给人看的 .md 长报告",改产**给 agent 看的证据包**;人话结论只在对话里给。详见 `task_draft/consensus/evidence-pack/design.md`。

- 位置：`tasks/<任务>/evidence/<步骤-slug>/`，含 `manifest.json`(做了什么/为什么/输入输出/验收结论/human_conclusion)+ `data.jsonl`(结构化数据)+ 可选 `sources.json`(溯源)。
- 与验证层咬合：`manifest.verdict` = 出口断言的硬/软结论。证据包是出口断言留下的痕迹。
- 目的：易管理、易其他 agent 介入、易复盘逻辑链。纯 JSON/JSONL，可 grep 可手改，不引数据库。
- 输出层的"稿子"不算证据(它是给人的成品原料),照常产。

---

## 三、命名约定

1. **用语义名，不用纯时间戳**。`output/output-layer/汽车课设-报告/` 好过 `output/output-layer/20260618-153022/`。
   - 真要防重名再加日期后缀：`<语义名>-YYYYMMDD`。
2. **同一主题反复生成，覆盖或归档旧的**，不要堆几十个时间戳文件夹（output-layer 已踩过这坑）。最新成品保持唯一可识别；旧版进 `_archive/`。
3. **任务名跨文件保持一致**：tasks/ 里的任务名、output/ 里的成品目录名、artifacts.md 登记名，用同一个 slug，方便串起来。

---

## 四、每个 SKILL.md 必须声明产出去向

每个会产出文件的 skill，在 SKILL.md 里写一行（或一节）`## 产出去向`，明确：

```
## 产出去向
- 过程产物：output/<本skill>/runs/<slug>/
- 正式成品：output/<任务名>/  （并登记进 tasks/<任务>/artifacts.md）
- 跨设备产物：留原处，登记坐标
```

新建 skill 时这是必填项。已有 skill 逐步补（不强制一次改完）。

---

## 五、与任务记忆的咬合

- skill 产出后 → closeout 收尾时提议在 `tasks/<任务>/artifacts.md` 加一条坐标 + 在 `unit-log.md` 加一行历史。
- 用户确认才写（沿用"提议-确认"写入模型）。
- 这样：做完的成果有日志（不被覆盖）、有坐标（找得回）、有索引（INDEX 能定位）。三层兜住，不再"记得住进度记不住成果"。

---

## 六、不做什么

- 不强制立刻迁移所有历史产物到新位置（成本高、收益低）。规范从"新产出"开始生效，旧的按需归位。
- 不引入数据库 / 索引服务。纯 markdown + 目录约定，可 `ls`、可 `grep`、可手改。
