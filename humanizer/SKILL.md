---
name: humanizer
description: 检测并去除文本中的 AI 写作痕迹。基于 Wikipedia "Signs of AI writing" 的 30 条具体模式，系统化审计+改写。与 output-layer 的 rewrite-polisher 分工：rewrite-polisher 做通用表达优化（润色/收紧/改语气），humanizer 做 AI 模式审计（检测具体 AI tell → 定向去除）。触发词：去 AI 味、太像 AI 了、humanize、审一下 AI 痕迹、检查 AI 味。
status: stable
commands:
  - humanizer
  - humanize
---

# Humanizer — AI 写作痕迹检测与去除

## 定位

检测并去除文本中的 AI 生成痕迹，让文字读起来像人写的。

**不是通用润色器**。它只做一件事：找到具体的 AI tell，定向替换。
如果用户要的是"收紧表达/改语气/重写开头"，走 `output-layer` 的 rewrite-polish 模式。

## 与 rewrite-polisher 的边界

| 用户说 | 走哪里 | 理由 |
|---|---|---|
| "润一下 / 收紧 / 改得像我" | output-layer rewrite-polish | 通用表达优化 |
| "去 AI 味 / 太像 AI 了 / humanize" | **本 skill** | AI 模式审计 |
| "帮我看看哪里像 AI" | **本 skill**（诊断模式） | 只标注不改 |
| "改得更像人话" | 视上下文 | 如果有具体 AI 痕迹 → 本 skill；如果只是语气问题 → rewrite-polish |

## 核心流程

```
输入文本 → 模式扫描（30 条规则）→ 标注命中 → 改写初稿 → 自审（"哪里还像 AI？"）→ 终稿
```

### 步骤

1. **扫描**：逐条检查下方 30 个模式，标记命中项
2. **改写初稿**：替换所有命中项，保持原文含义和段落结构
3. **自审**：问自己"这段哪里还明显像 AI？"，列出残留 tell
4. **终稿**：修掉残留，确认无 em dash（硬约束）
5. **交付**：返回终稿 + 改动摘要（改了哪几类模式）

## Voice Calibration（可选）

如果用户提供了自己的写作样本：

1. 分析样本：句长模式、用词层级、段落开头习惯、标点偏好、口头禅
2. 改写时匹配样本风格，不是匹配"通用人味"
3. 没有样本时，回退到默认行为：自然、有节奏变化、有观点

## 30 条 AI 写作模式

### 内容层

| # | 模式 | 关键词/信号 | 改法 |
|---|---|---|---|
| 1 | 意义膨胀 | stands as, testament, pivotal, underscores, broader | 删掉意义声明，只留事实 |
| 2 | 知名度堆砌 | independent coverage, active social media presence | 用一个具体例子替代罗列 |
| 3 | -ing 假深度 | highlighting, ensuring, reflecting, showcasing | 删掉 -ing 尾巴，或改成独立句 |
| 4 | 促销腔 | vibrant, profound, nestled, breathtaking, renowned | 换成具体描述 |
| 5 | 模糊归因 | Experts argue, Industry reports, Some critics | 给出具体来源或删除 |
| 6 | 套路"挑战与展望" | Despite challenges, Future Outlook | 用具体事实替代 |

### 语言层

| # | 模式 | 关键词/信号 | 改法 |
|---|---|---|---|
| 7 | AI 高频词 | delve, landscape, tapestry, vibrant, crucial, foster, underscore, interplay, intricate | 换成普通词或删除 |
| 8 | copula 回避 | serves as, stands as, boasts, features | 直接用 is/are/has |
| 9 | 否定平行 | Not only...but..., It's not just...it's... | 改成直接陈述 |
| 10 | 三点式堆砌 | A, B, and C（强行凑三个） | 只保留真正需要的项 |
| 11 | 同义词轮换 | protagonist→main character→central figure→hero | 用同一个词，不怕重复 |
| 12 | 假范围 | from X to Y（X 和 Y 不在同一尺度） | 直接列举 |
| 13 | 被动语态/无主语 | No configuration needed. Results are preserved. | 加主语，用主动语态 |

### 风格层

| # | 模式 | 信号 | 改法 |
|---|---|---|---|
| 14 | 破折号（硬约束） | — / – / ` -- ` | 终稿中不允许出现。改为句号/逗号/冒号/括号 |
| 15 | 加粗滥用 | 机械性加粗关键词 | 删除多余加粗 |
| 16 | 列表头格式 | `- **Header:** content` | 改成连贯段落 |
| 17 | 标题 Title Case | Strategic Negotiations And Global Partnerships | 改为 sentence case |
| 18 | Emoji 装饰 | 🚀💡✅ 开头 | 删除 |
| 19 | 卷引号 | "..." (curly) | 改为 "..." (straight) |

### 沟通层

| # | 模式 | 信号 | 改法 |
|---|---|---|---|
| 20 | 协作痕迹 | I hope this helps, Let me know, Here is a... | 删除，直接进入正文 |
| 21 | 知识截止/猜测填充 | as of [date], While specific details are limited | 说不知道或删除，不伪装 |
| 22 | 谄媚语气 | Great question! You're absolutely right! | 删除，直接回应内容 |

### 填充层

| # | 模式 | 信号 | 改法 |
|---|---|---|---|
| 23 | 废话短语 | In order to, Due to the fact that, At this point in time | 缩短：To, Because, Now |
| 24 | 过度 hedge | could potentially possibly be argued that might | 去掉多余限定词 |
| 25 | 通用正面结尾 | The future looks bright, Exciting times lie ahead | 换成具体下一步 |
| 26 | 连字符过度统一 | 谓语位置也加连字符（the report is high-quality） | 谓语位置去掉连字符 |
| 27 | 权威修辞 | The real question is, At its core, What really matters | 删掉前缀，直接说 |
| 28 | 预告式开头 | Let's dive in, Here's what you need to know | 删掉，直接进入内容 |
| 29 | 碎片化标题 | 标题后跟一句重复标题的话 | 删掉重复句 |
| 30 | Diff 锚定写作 | This was added to replace the previous... | 描述当前状态，不叙述变更历史 |

---

## 误报指南（什么不该改）

以下情况**不是** AI 信号，不要过度矫正：

- 完美语法和一致风格 → 可能是专业写手或经过编辑
- 混合正式/口语语域 → 可能是技术领域的人或年轻写手
- 正式/学术词汇 → AI 过度使用的是**特定**花哨词（见 #7），不是所有花哨词
- 单个 em dash → 很多记者和编辑常用；只有跟其他 tell 聚集时才算
- 单个过渡词（Additionally, However） → 只有堆砌时才算
- 无来源声明 → 大部分网络内容都没来源

**判断原则**：看**聚集**，不看孤立。一个 em dash 什么都不说明；em dash + 三点式 + vibrant tapestry + "Conclusion" 段 = 确认。

## 人味信号（保留这些）

看到以下特征时，倾向于不改：

- 具体、不寻常、难以编造的细节
- 混合感受和未解决的张力（"我觉得大体上好，但有什么地方不对"）
- 有时代感的引用/梗/圈内笑话
- 句长变化（短长交替）
- 真正的插入语、自我修正（"我一直想说'几乎'，但其实是确定的"）

---

## 与 output-layer rewrite-polisher 的协作

当 output-layer 收到"去 AI 味"请求时，可以调用本 skill 的模式清单做检测。
本 skill 产出改写后的文本，output-layer 负责最终交付格式（chat / file / export）。

流程：
```
用户说"去 AI 味" → output-layer 识别触发词 → 调用 humanizer 模式扫描+改写 → 返回终稿
```

## 参考来源

本 skill 的模式清单基于 [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)（WikiProject AI Cleanup 维护）和 [blader/humanizer](https://github.com/blader/humanizer)（21.5k⭐, MIT）。
