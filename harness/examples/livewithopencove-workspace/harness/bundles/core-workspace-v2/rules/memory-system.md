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
├── timeline-archive.md
├── decisions.md
├── lessons.md
├── lessons-archive.md
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

### 写入 Schema

- `timeline.md`：时间倒序，记录做了什么、产物位置、下一步和阻塞。
- `current-position.md`：覆盖式保存当前焦点、优先级、最近待办、阻塞和更新时间。
- `decisions.md`：追加已确认决策、背景、影响和状态。
- `lessons.md`：追加条件式经验，并带 `scope/applied/helpful/harmful/last` 机读 meta。
- `tasks/INDEX.md`：只保存任务名、状态文件位置、状态和更新时间。

## 禁止内容

- 聊天全文、原始工具日志和烟测噪声。
- 凭证、账号、网络地址和设备专属配置。
- 未经确认的推断、灵感或未来任务。
- 跨设备公共任务状态和协作进度。
- 真实记忆内容进入 bundle、发布物或存储镜像。

## 维护

- `memory_gc.py`：默认保留最近 30 条时间线；溢出内容只移入归档，写前备份。
- `lessons_gc.py`：默认只报告重复、冲突和退役候选；只有 `--apply` 才归档退役项。
- `check_map.py`：只读检查未登记目录和地图新鲜度，不自动改写地图。
- `organize.py`：默认 dry-run；只在显式 `--apply` 后整理工作区约定的产物目录。
- 自动 checkpoint 是运行恢复状态，不是正式长期记忆；不得替代用户确认后的记忆写入。
- 模板初始化必须发生在私有目录，且不得把示例文字当作真实状态。
