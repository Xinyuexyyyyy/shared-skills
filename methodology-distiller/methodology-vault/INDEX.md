# PRD 方法卡库索引

这个库不是 PRD 模板合集，而是 PRD 缺口修补系统。使用顺序是：

```text
发现缺口 -> 选择方法卡 -> 补齐信息或默认方案 -> 回到 PRD Quality Gate
```

## 总原则

- 正文全部使用中文。
- 文件名使用英文，方便路径稳定和检索。
- 方法卡只解决一个清晰缺口，不写成百科。
- 用户只回答事实、偏好、优先级、限制和真实场景。
- 技术、PRD、UX、数据、验收等专业方法由 agent 蒸馏，不逼用户学术语。
- 候选来源先进入 `candidates/` 或 `reviews/`，通过筛选后再沉进 `cards/`。

## 卡片路由

| PRD 缺口 | 使用卡片 | 输出位置 |
|---|---|---|
| 不知道该写完整 PRD 还是 brief | `cards/prd-type-selector.md` | 交付物类型、降级说明 |
| PRD 看起来完整但不能开工 | `cards/prd-executable-spec.md` | PRD Quality Gate / 下一步 |
| MVP / Future / Out of Scope 不清 | `cards/prd-boundary.md` | MVP 范围、不做、未来、假设 |
| 页面、按钮、状态、输入输出不清 | `cards/prd-detail.md` | 体验与 UI 行为、实现与数据决策 |
| UI 状态和草图缺失 | `cards/prd-ui-state.md` | 页面/区域/控件/状态表 |
| 数据放哪里、字段是什么不清 | `cards/prd-data-storage.md` | 数据字段、存储位置、目录布局 |
| 不知道怎么验收 | `cards/prd-acceptance-path.md` | 验收标准、最短测试路径 |
| PRD 太长、太散、像资料堆 | `cards/prd-subtraction.md` | 正文保留项、附录/ADR/evidence brief |
| 不知道缺口该回哪一层 | `cards/prd-loopback-routing.md` | loopback target |
| Gate 发现缺口后需要回滚成追问链 | `cards/prd-grok-loop.md` | Grok 追问链、回填字段 |

## 来源分层

| 等级 | 含义 | 可进入 |
|---|---|---|
| L1 | 官方 / 标准 / 经典方法 | `cards/` |
| L2 | 成熟开源实践 / 大厂公开指南 | `cards/` 或 `reviews/` |
| L3 | 专家实践 / 社区经验 / 案例 | `candidates/` 后评审 |
| L4 | 博客、社媒、小红书等启发 | 只能进 `candidates/` |

## 第一批借鉴

- Open Practice Library：借实践库、贡献、审核、卡片组织方式。
- Open Design Kit：借面向非专业用户的方法写法。
- Product Manager Skills / PM toolkit：借 agent skill 化和 PRD 类型选择。
- PRD / SRS 模板：借稳定字段，不直接套模板。
- ADR / MADR：借决策记录和主 PRD 减法方式。
