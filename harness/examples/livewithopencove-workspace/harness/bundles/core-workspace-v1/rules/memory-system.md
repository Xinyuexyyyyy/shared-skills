---
component_id: memory-system
version: 1.0.0
status: draft
---

# 工作区记忆制度

工作区记忆用于跨会话接续当前工作区，不用于保存聊天全文，也不承担跨设备公共状态。真实内容始终留在工作区私有目录，bundle 只携带制度和空模板。

## 标准结构

```text
.claude/memory/
├── MEMORY.md
├── workspace-brief.md
├── workspace-map.md
├── current-position.md
├── timeline.md
├── decisions.md
├── lessons.md
└── tasks/
    └── INDEX.md
```

## 读取规则

- 会话开局不预读记忆。
- 接续具体任务：`tasks/INDEX.md` 定位，再读取该任务的状态。
- 接上次进度：读取 `current-position.md`，再读取 `timeline.md` 最近三到五条。
- 查询历史决策或经验：按主题检索 `decisions.md` 或 `lessons.md`。
- 一次性问答和纯新任务：不读记忆。
- 读到能执行当前一步所需的最小信息后停止。

## 写入规则

1. 执行和 closeout 只能提出记忆候选。
2. 用户确认候选后，才写入对应文件。
3. `current-position.md` 保存当前焦点、阻塞和下一步，不保存流水。
4. `timeline.md` 保存重要变化，旧记录按阈值归档。
5. `decisions.md` 只保存已确认的长期决策及原因。
6. `lessons.md` 只保存换个会话仍有价值、且已有证据的经验。
7. 任务索引只保存定位信息，不复制任务全文。

## 禁止内容

- 聊天全文、原始工具日志和烟测噪声。
- 凭证、账号、网络地址和设备专属配置。
- 未经确认的推断、灵感或未来任务。
- 跨设备公共任务状态和协作进度。
- 真实记忆内容进入 bundle、发布物或存储镜像。

## 维护

- 时间线超过工作区约定阈值时，只移旧条目到归档，不删除。
- 索引目标不存在、当前位置过期或决策互相冲突时，只报告，不自动改写语义。
- 模板初始化必须发生在私有目录，且不得把示例文字当作真实状态。
