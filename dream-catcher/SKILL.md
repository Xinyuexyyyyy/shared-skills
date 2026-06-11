---
name: dream-catcher
description: 想法对撞机。接住 sure 冒出来的半成品想法,跟"已发布作品/锚点池/想法池"三池立刻对撞,挑出"好玩感"最强的几条火花,不下结论让 sure 拍板。用于"我有个想法但不知道行不行"那种状态。
status: stable
---

# Dream Catcher

## 定位

想法接收 + 立刻对撞 + 好玩感识别。

不是想法管理库,是**想法撞墙池**——sure 不是囤货型创作者,他要的是想法被接住后立刻挨打,从打架的火花里看哪条值得做。

## 它在防什么坑

- **想法仓库化**:把想法记下来归档分类,然后再没人看(违反 [[feedback-anti-warehouse]] 第 2 条)
- **过度分析**:对一个想法做"可行性 / 用户画像 / 商业逻辑"五段式分析,把好玩感分析掉
- **平铺所有可能**:对撞结果穷举,sure 看完更不知道选啥
- **代 sure 拍板**:给"我建议你做 X"的强结论(违反 `feedback_motivation_model` 的"给信号不下决定")
- **凭空启发**:池子里没相关素材时硬编理由(违反 anchor-spark 的"灵感来自摩擦")

## 什么时候用

- sure 说"我有个想法..." / "我想做..." / "我在想能不能..."
- sure 说"这事儿好玩" / "这个有意思"
- sure 抛出一个模糊的题目/概念/感受,没明确说要写文章
- sure 处于"做事中场休息"状态,冒出来一个非当前任务的念头

## 不什么时候用

- sure 已经有完整骨架要写正文 → 走 `sure-content-studio`
- sure 知道写什么但不知道怎么切角 → 走 `anchor-spark`(它是写文章前的骨架阶段)
- sure 说"帮我审稿/改稿" → 走 `review-gate`
- sure 在做事过程中提了个**和当前任务相关**的子想法 → 直接讨论,不要切到 dream-catcher 增加摩擦

## 必读资源(按优先级)

1. `~/anchor-pool/published-articles.md` — sure 已发布的作品(最关键的对撞池,避免重复造轮子)
2. `~/anchor-pool/INDEX.md` — 锚点池索引(做过的事)
3. `~/anchor-pool/ideas.md` — 想法池(想做的事)
4. `~/anchor-pool/seeds/wechat_writing_anchors-2026-05-25.md` — 实证基线
5. `~/.claude/projects/-Users-sure-Daily-Work/memory/feedback_anti_warehouse.md` — 协作三原则
6. `~/.claude/projects/-Users-sure-Daily-Work/memory/feedback_motivation_model.md` — 灵感来自摩擦机制
7. `~/content work/skills/sure-content-studio/references/style-profile.md` — 6 视角 + 真护城河

## 工作方式

### Step 1: 接住,不评判

sure 给的输入可能是:
- 一个名词("想做个 agent 名动词的合集")
- 一个动词短语("想骂下产品经理")
- 一个情绪("最近觉得 0 代码用户被高估了")
- 一个具体经历("刚跟 X 聊完发现一件事")

**不要先问"你想写文章吗" / "你想做什么形式"**——sure 还没想清楚,逼他想清楚是反作用。

直接进 Step 1.5。

### Step 1.5: 跨工作区回响(前置,不可跳过)

在三池对撞之前,先扫一遍全部工作区的历史,看这个想法是不是"你已经做过/想过的"。

```bash
bash ~/anchor-pool/cross-workspace-recall.sh <从 sure 输入里提取的 2-4 个关键词>
```

**看什么**:
- 🎯 栏有命中 → 告诉 sure:"这个方向你之前做过 [项目名],已经产出了 [final-report/consensus/...]。要在那个基础上继续,还是当全新方向?"
- 🎯 栏为空但 📝/🧠 有零散命中 → 作为对撞素材带进 Step 2,不单独打断
- 全部为空 → 直接进 Step 2,这是真新方向

**关键词提取规则**:
- 从 sure 的输入里取 2-4 个核心名词/动词
- 中英文都要(如"录音"同时搜"recorder/audio")
- 忽略虚词、语气词

### Step 2: 三池对撞(并行,不要顺序问)

并行扫三个池子:

```bash
# 已发布池(最关键 — 避免重复)
cat ~/anchor-pool/published-articles.md

# 锚点池(做过的事)
cat ~/anchor-pool/INDEX.md
# 然后挑相关的 anchors-*.md cat 进来

# 想法池(想做的事)
cat ~/anchor-pool/ideas.md
```

匹配规则:
- **关键词命中**:sure 给的输入里的核心名词在池子哪些条目里出现过
- **kind 共振**:如果输入带情绪("被动""无聊""被吹爆了"),优先找对应 kind(`contrast` / `inversion` / `debunk`)
- **face 跨面**:如果输入横跨多个面(比如 engineering + humanist),优先标记
- **新鲜度**:最近 30 天的优先

### Step 3: 三种对撞结果(不要超过 3 类各 2 条)

把对撞结果按"火花类型"分成三类,**每类最多 2 条**(总共 ≤ 6 条):

#### 🔥 能合体的(有现成材料拼)
sure 池子里已有 N 条素材能直接组装这个想法。
- 给具体哪几条素材 + 怎么拼
- 评估"好玩度":拼起来比单独看更有 sparkle 吗?

#### ⚡ 能拆穿的(池子里有矛盾点)
池子里有跟当前想法冲突的锚点/已发文章。
- 这是 sure 的"逆向/拆穿"叙事力的强项触发点(参见 [[feedback_narrative_style]])
- 矛盾本身是创作素材

#### 🌱 完全新的(池子里没相关锚点)
- **不是好事也不是坏事**——可能是真新方向,也可能是无根想法
- 提示 sure:"池子里没相关素材意味着你最近没在这件事上做过摩擦"(参见 [[feedback_motivation_model]] 灵感来自摩擦)
- 给两个选项:回去做小落地 / 先放进 ideas.md 发酵 3 天

### Step 4: 好玩感识别(关键能力)

从对撞结果里挑**最有 sparkle 的 1~3 条**,标 ⭐ 强度。

好玩感判断标准(从 `style-profile.md` 提炼):
- ⭐⭐⭐⭐⭐ = 跨学科类比 + 跟用户护城河(metaphor)直接连接
- ⭐⭐⭐⭐ = 对比/拆穿/逆向能直接出火花,不需要展开背景
- ⭐⭐⭐ = 有素材能挂上,但需要展开
- ⭐⭐ = 能说但平淡
- ⭐ = 这个对撞没产生新东西

**不要给所有结果打分**——只标火花最强的几个,弱的不出现。

### Step 5: 拍板权交还

最后给两个具体动作选项,让 sure 拍板:

```markdown
**接下来怎么走?**

A. 进 ideas.md 发酵 3 天(不立刻动,看 3 天后还认不认)
B. 直接进 anchor-spark 切角写文章(此刻就有 sparkle)
C. 都不,回去做点具体的事(池子薄,先摩擦)

我看 [N] 这条最有 sparkle,理由 [一句]。但你拍板。
```

**不要替 sure 决定**——给信号,他选。

### Step 6: 进 ideas.md(如果 sure 选 A)

帮 sure 把想法写进 `~/anchor-pool/ideas.md`,格式:

```markdown
## YYYY-MM-DD HH:MM — <一句话标题>

- **想法**: <展开 1~3 句>
- **为什么有意思**: <他为什么觉得值得记>
- **下一步小动作**: <填得出来就填,填不出来就承认"暂无">
- **关联**: <对撞匹配到的 anchor id / article slug>
- **状态**: 🌱 新
- **入库**: YYYY-MM-DD
- **最近动作**: YYYY-MM-DD
- **提醒次数**: 0
```

写完告诉 sure: "已进 ideas.md,3 天后我会主动问你这个想法还在不在脑子里。"

发酵期机制:
- 进 ideas.md 后第 3 天起,closeout / dream-catcher / anchor-spark 启动时会检查并提醒
- sure 回应"再放着" → 把 `提醒次数` +1,`最近动作` 更新为今天
- sure 回应"开干了" → 状态改 🔥,提醒停止
- sure 回应"弃了" → 状态改 🪦
- 提醒 3 次仍无决策 → review-ideas.sh 自动列入"候选标灰",closeout 时建议改 🩶

(机制由 `~/anchor-pool/review-ideas.sh` 检测,不依赖 cron,sure 不打开 Claude 时不会被打扰)

## 输出格式

```markdown
## Dream Catcher 接到一个想法

### 你的想法
> [sure 原话]

### 三池对撞结果

#### 🔥 能合体的
- **[标题]**(关联: [anchor:20260525-DW-01] + [article:便宜不是目的])
  > 拼法: ...
  > sparkle: ⭐⭐⭐⭐⭐ (跟你的扳手原型类比能直接接)

#### ⚡ 能拆穿的
- **[标题]**(关联: [anchor:20260520-CW-02])
  > 矛盾点: ...
  > sparkle: ⭐⭐⭐⭐

#### 🌱 完全新的
- 池子里没相关素材。说明你最近没在这件事上做过摩擦。

### 我看到的最强 sparkle

[最值得做的 1 条 + 一句话理由]

### 接下来

A. 进 ideas.md 发酵 3 天
B. 直接 anchor-spark 切角写
C. 不,回去做点具体的事

你拍。
```

## 关键检查点

### 1. 必须真扫三池

不能跳过 published-articles.md。重复造轮子是 dream-catcher 防的最大坑——sure 已经写过的别让他再写一遍。

### 2. 必须有"完全新的"分类(即使为空)

如果池子里啥也没匹配,要明说"完全新的方向 → 这意味着你没做过摩擦",而不是装作有得说。诚实优先。

### 3. 不超过 6 条对撞结果

3 类 × 2 条 = 6 条上限。多了就是平铺,sure 看了更迷糊。

### 4. sparkle 评级只标火花最强的

不是给每条打分。**只挑出 1~3 条标 ⭐**,其他不带评级。这是好玩感识别,不是评估表。

### 5. 不替 sure 拍板

给"我看 N 这条最有 sparkle",不给"我建议你做 N"。一个字之差,差很多。

### 6. 池子薄要诚实喊停

如果三池加起来连 1 条相关都没有,直接说"这个方向你没素材,要么换主题,要么回去做点具体的"——不要硬启发。

## 边界条件

### 情况 1: sure 给的想法是"我没想法"

- 翻 published-articles.md 看最近 3 篇主题
- 翻 INDEX 看最近 7 天锚点
- 给 2~3 个"基于你最近做过的事的备选主题",不强推

### 情况 2: 想法跟 sure 已发文章高度重合

- 直接说:"这个跟 [article:xxx] 题目重合度高,你已经写过了"
- 然后给"差异化角度"建议(用 contrast / inversion 视角让旧主题翻出新意)

### 情况 3: 想法横跨多个 face

- 标记出来:"这个题横跨 engineering + humanist,你很少这么搭——这是新组合"
- 多面组合本身可能就是 sparkle 来源

### 情况 4: sure 在疲惫状态

- 信号:连续短回复 / "嗯""好""可以"型回应 / 5 轮以上无新决策
- 处理:**不要给对撞结果**,直接调出 observations.md 的 ✅ 已确认 区,问"现在你最有感觉的是什么"
- 这是协作三原则第 3 条(对话切片本身有清醒作用)

## 与其他 skill 的关系

```
dream-catcher (接想法+对撞+发酵) → ideas.md
                                    ↓ 3 天后
                                  确认 → anchor-spark (写文章前的 6 视角骨架)
                                    ↓
                                  sure-content-studio (写正文)
                                    ↓
                                  review-gate (审稿)
```

dream-catcher 是引擎的**入口**——想法在这里被接住、对撞、发酵。anchor-spark 是后续——已经决定要写时,从想法/锚点池里挑切角。

## 最小验收

这轮至少要做到:

1. 真扫了 published-articles.md / INDEX.md / ideas.md 三个池子
2. 给的对撞结果 ≤ 6 条,分 🔥/⚡/🌱 三类
3. 只标了 1~3 条 sparkle,不平铺评分
4. 给了 A/B/C 三个具体动作,sure 拍板
5. 如果 sure 选 A,正确进了 ideas.md(状态 🌱)
6. 如果池子薄,诚实说"没素材"——不硬编
