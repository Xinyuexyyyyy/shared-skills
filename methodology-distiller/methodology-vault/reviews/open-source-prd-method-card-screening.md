# 开源 PRD 方法卡方案筛选记录

## 筛选目标

筛选对象不是“好看的 PRD 模板”，而是能贡献到中文 PRD 方法卡库的开源方案。判断问题：

- 能不能转成方法卡？
- 能不能服务轻代码用户？
- 能不能提升 Boundary / Detail / Evidence / Acceptance？
- 能不能接入 `deep-research -> grillme -> methodology-distiller -> PRD Quality Gate`？

## 筛选结果

| 方案 | 类型 | 采纳方式 | 贡献位置 | 注意事项 |
|---|---|---|---|---|
| Open Practice Library | 实践库 | 借库结构、索引、审核、废弃机制 | `INDEX.md`、`reviews/`、`deprecated/` | 不照搬内容，只借组织形态 |
| Open Practice Library card decks | 方法卡/卡组 | 借卡片化、可评审、可版本化思路 | `cards/`、`candidates/` | 适合卡片治理，不直接变 PRD |
| Open Design Kit | 设计方法库 | 借非专业用户友好的方法表达 | `prd-detail`、`prd-ui-state` | 需要转成 PRD 可执行字段 |
| Product Manager Skills | PM skill 库 | 借 agent skill 化、PRD/discovery/prioritization workflow | `prd-type-selector`、`prd-boundary` | 许可证不适合复制正文，只借思路 |
| PM toolkit / product manager toolkit | PRD/PM 工作流 | 借 PRD / one-page PRD / feature brief / epic 的类型判断 | `prd-type-selector` | 作为启发，不当唯一标准 |
| PRD / SRS templates | 规格模板 | 借字段：目标、范围、验收、限制、风险、依赖 | `prd-executable-spec`、`prd-acceptance-path` | 模板容易变厚，必须做减法 |
| ADR / MADR | 决策记录 | 借 context/options/decision/consequences | `prd-subtraction`、后续 ADR 卡 | 技术争论放 ADR，不塞主 PRD |

## 采纳结论

第一版不做大型方法论数据库，也不做 RAG。先做中文 Markdown 方法卡：

- `cards/`：已经通过筛选、可以直接调用的正式卡。
- `candidates/`：有启发但没评审的方法。
- `reviews/`：来源筛选和评审记录。
- `deprecated/`：废弃方法卡，保留原因。

## 不采纳项

- 只提供漂亮排版、没有方法判断的 PRD 模板。
- 过重的企业级产品管理流程。
- 需要用户掌握大量专业术语才能使用的方法。
- 许可证不清晰或不可复用的正文内容。

