# Formal Expansion Layer PRD v1

## 目标

`formal-expansion-layer` 解决的问题不是“能不能生成 docx”，而是：当输入内容太短、太口语、太依赖用户给的几句前置条件、反复重复同一判断时，如何先扩成一份结构完整、语气正式、边界清楚的中文正式稿，再交给质量门检查。

它是 `output-layer` 里位于质量门之前的一层：

```text
source.md
  -> formal expansion
  -> deterministic docx quality check
  -> assisted methodology review
  -> docx render
```

第一版只做正式扩写和结构补全，不做事实编造，不自动补引用，不替用户下合规结论。

## 用户问题

当前 AI 输出常见问题：

1. **太简单：** 只有一句结论或几条点，没有对象、背景、依据、边界和下一步。
2. **太口语：** 使用“这个东西”“大概就是”“挺烦的”“弄一下”等表达，不适合 docx 正式交付。
3. **太重复：** 反复说“提升质量、优化体验、形成闭环”，信息密度低。
4. **太依赖前置条件：** 只复述用户给的几句话，没有把隐含目标转成正式文档结构。
5. **看起来完整但不可靠：** 为了显得正式，容易编造事实、政策、数据、依据或结论。

## MVP 范围

### 做

- 将短输入扩成正式文档骨架。
- 将口语表达改成书面、正式、克制表达。
- 合并重复观点，保留一次核心判断。
- 按 `doc_type` 选择扩写结构：
  - `formal_report`：对象/目的 -> 背景/问题 -> 核心内容/方法 -> 依据/边界 -> 结论/行动。
  - `proposal`：为什么做 -> 做什么 -> 凭什么能做。
  - `technical_disclosure`：技术问题 -> 技术方案 -> 技术效果 -> 边界条件。
  - `abstract`：对象/问题 -> 方法/材料 -> 结果/发现 -> 意义/边界。
  - `manual`：适用对象 -> 前置条件 -> 操作步骤 -> 注意事项 -> 异常处理。
- 对缺事实的位置标注 `待补充`。
- 输出扩写报告，说明扩写了什么、没扩什么、哪些内容需要人工补充。

### 不做

- 不新增事实、数据、政策、标准、文献、项目基础、研究结果。
- 不自动补引用或参考资料。
- 不判断事实真假、政策现行性、项目合规性、论文创新性、专利权利边界。
- 不把所有文本改成政府公文口吻。
- 不直接自动覆盖原稿。

## 模式

### `off`

默认关闭，不影响现有 `render_markdown_output.py` 行为。

### `conservative`

保守扩写。适用于用户已经有内容，只是表达太口语、太散、重复太多。

行为：

- 保持原始事实和判断。
- 重排结构。
- 改正式表达。
- 合并重复内容。
- 对缺项只提示，不主动补段落。

输出适合作为“修订稿”。

### `structured`

结构化扩写。适用于用户只给了几句话，希望形成正式文档初稿。

行为：

- 按 `doc_type` 补齐章节骨架。
- 用已给信息填入对应章节。
- 缺少事实的位置写 `待补充：...`。
- 明确边界和下一步。

输出适合作为“正式初稿”，但必须继续过质量门。

## 输入

Markdown 文件，允许 frontmatter：

```yaml
---
doc_type: formal_report
expansion_mode: structured
audience: 内部评审
purpose: 形成正式 docx 初稿
---
```

正文可以是：

- 几句想法。
- 会议纪要。
- 草稿段落。
- 条目列表。
- 已生成但质量不高的 output-layer 输出。

## 输出

扩写层单独运行时输出：

- `output.expanded.md`
- `formal_expansion_report.json`
- `formal_expansion_report.md`

接入渲染主链后，run 目录新增：

- `output.expanded.md`
- `formal_expansion_report.json`
- `formal_expansion_report.md`
- 后续质量门报告：`docx_quality_report.*`、`assisted_quality_report.*`

## 报告状态

| status | 含义 | 下一步 |
|---|---|---|
| `expanded` | 已完成扩写，可进入质量门 | `quality_check` |
| `needs_user_input` | 关键信息不足，只能生成骨架或待补充标记 | `fill_missing_facts` |
| `skipped` | 模式为 off 或输入不适合扩写 | `render_or_review` |

## 扩写报告字段

```json
{
  "status": "expanded",
  "doc_type": "formal_report",
  "mode": "structured",
  "summary": "已将短输入扩展为正式报告初稿，缺失事实以待补充标记保留。",
  "actions": [
    {
      "code": "build_formal_skeleton",
      "description": "补齐正式报告五段骨架",
      "evidence": "原文缺少标题和章节结构"
    }
  ],
  "blocked_expansions": [
    {
      "reason": "缺少事实依据",
      "placeholder": "待补充：本方案已有验证结果或实际案例"
    }
  ],
  "next_action": "quality_check"
}
```

## 用户可见效果

### 输入

```markdown
这个输出层现在太薄了，AI 总是反复说提升质量，写得很口语。我要一个正式点的质量关，别乱编事实。
```

### `structured` 期望输出方向

```markdown
# 输出层正式写作质量关建设说明

# 一、建设目的

本说明面向 output-layer 的 docx 输出场景，目标是解决输出内容过短、表达口语化、观点重复和事实边界不清等问题。

# 二、现有问题

当前输出链路能够生成文档文件，但在内容层面仍存在以下问题：一是部分输出仅复述用户前置条件，缺少正式文档所需的对象、目的、依据和结论；二是部分表达偏口语化，不适合作为正式 docx 交付；三是部分段落反复使用“提升质量、优化体验”等低信息表达。

# 三、处理原则

扩写层只补结构、过渡、边界和表达，不新增未经提供的事实、数据、政策或结论。涉及事实依据、项目基础和合规口径的内容，应以“待补充”标记保留，并交由人工确认。

# 四、下一步

建议先实现保守扩写和结构化扩写两个模式，再将扩写结果交由 deterministic quality check 和 assisted review 复核。
```

## 验收标准

MVP 完成时必须满足：

1. 给一段短输入，能生成 `output.expanded.md`。
2. 扩写稿比原稿结构更清楚、表达更正式、重复更少。
3. 不新增原文没有的事实、数据、政策、引用或结论。
4. 缺事实的位置出现 `待补充`，并进入 expansion report。
5. 扩写后能继续跑现有质量门。
6. 至少覆盖 3 类样例：太短、太口语、重复空泛。

## 风险

| 风险 | 处理 |
|---|---|
| 扩写变成编造 | 所有事实型缺口必须写 `待补充` |
| 扩写变成长而空 | 每段必须承担对象、背景、方法、依据、边界或行动之一 |
| 扩写过度公文腔 | 使用正式但克制的说明文，不默认模仿政府文件 |
| 报告太多用户看不懂 | run index 只给最终建议：可渲染 / 需修订 / 需补事实 |

## 后续非 MVP

- LLM 辅助深度扩写。
- 按用户个人风格做正式表达适配。
- 自动生成多版本：简版、正式版、申报版。
- 与真实 source library 做 retrieval-grounded expansion。
