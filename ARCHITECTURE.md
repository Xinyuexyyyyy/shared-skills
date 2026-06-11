# 跨工作区 Skill 共享架构

> 本文件是 `~/shared-skills/` 的权威文档。任何工作区的 AI 进入后都应能读懂当前结构。

---

## 一、核心原则

**每个 skill 只维护一份权威版本，其他工作区通过软链接引用。改一处，全局生效。**

---

## 二、目录结构

```
~/shared-skills/
├── task-analyze/          # 基础：意图分析
├── task-decompose/        # 基础：任务拆解
├── closeout/              # 基础：任务收尾
├── research/              # 调研层：总入口 + 4 个子包
│   ├── base/
│   └── packages/
│       ├── academic/
│       ├── competitive/
│       ├── comprehensive/
│       └── discovery/
├── idea-to-research/      # 调研层：模糊想法路由
├── output-layer/          # 输出层：公共输出（markdown/Obsidian/docx）
├── output-polisher/       # 输出层：排版与导出
├── output-style-checker/  # 输出层：规则检查
├── ui-design/             # 输出层：UI/页面/组件设计与截图验收
├── source-intake/          # 前置层：URL/PDF/网页/资料包到 Markdown + evidence
├── harvest-tool/          # 工具：GitHub 项目收割
├── _tools/                # 本机公共工具层（下划线前缀，不被扫描为 skill）
│   ├── scan-skills.py     # 跨工作区 skill 扫描 + 索引生成
│   ├── skill-governance.py
│   ├── skill-recommend.py
│   ├── skill-trace.py
│   ├── auto-link.sh       # 自动创建 CLAUDE.md -> SKILL.md 软链接
│   └── start-dashboard.sh
├── README.md              # 公共层入口说明
└── ARCHITECTURE.md        # 本文件
```

---

## 三、工作区接入关系

| 工作区 | 路径 | 接入方式 | 共用 skill 数 | 本地 skill |
|--------|------|---------|--------------|-----------|
| **Daily Work** | `~/Daily Work/` | skills/ 下软链接指向 shared-skills | 11 | bilibili-video-analyzer, better-option, info-head, ppt-master, ppt-master-bridge, skill-optimizer, skill-dashboard, opencove-remote-deploy, fast-onboard 等 |
| **Content Work** | `~/Content Work/` | skills/ 下软链接指向 shared-skills | 9 | interview-writer（权威版）, sure-content-studio |
| **Study Research** | `~/study-research/` | skills/ 下软链接指向 shared-skills | 9 | paper-discovery, paper-reading, paper-screening, research-academic, research-base, academic-deep-research, supervisor-scout, survey-writer |
| **harvester-ai-research** | `~/study-research/harvester-ai-research/` | skills/ 下软链接指向 shared-skills | 7 | 无（纯消费者） |

### 跨区链接（非 shared-skills）

| Skill | 权威位置 | 链接到 |
|-------|---------|-------|
| `interview-writer` | Content Work | Daily Work 软链过去 |

---

## 四、Skill 分层

```
┌─────────────────────────────────────┐
│         共用层 (~/shared-skills/)    │
│  base: task-analyze, task-decompose, │
│        closeout                      │
│  调研: research, idea-to-research    │
│  前置: source-intake                 │
│  输出: output-layer, output-polisher,│
│        output-style-checker,         │
│        ui-design                     │
│  工具: harvest-tool                  │
└─────────────┬───────────────────────┘
              │ 软链接
    ┌─────────┼─────────┬──────────────┐
    │         │         │              │
 Daily Work  Content  Study       harvester
 (本地 skill) Work    Research    -ai-research
              (本地)   (本地)      (纯消费)
```

---

## 五、约定

### 5.1 新增共用 skill

1. 在 `~/shared-skills/` 下创建目录，写 `SKILL.md`
2. 运行 `~/shared-skills/_tools/auto-link.sh` 自动建 `CLAUDE.md -> SKILL.md`
3. 在需要的工作区 skills/ 下建软链接：`ln -sf ~/shared-skills/<name> <name>`
4. 更新对应工作区的 AGENTS.md 和 .claude/CLAUDE.md 的 skill 列表

### 5.2 新建工作区接入

1. 在新工作区下创建 `skills/` 目录
2. 按需建软链接到 `~/shared-skills/` 下的 skill
3. 建 `.claude/skills -> skills/` 软链接
4. 创建 `.claude/memory/` 目录 + 6 个标准模板文件
5. 创建 `AGENTS.md`，列出共用 skill 和本地 skill
6. 创建 `.claude/CLAUDE.md`，写 Skills 边界表

### 5.3 Skill 命名冲突

- 共用 skill 改名时，需要同时更新所有工作区的软链接
- 如果某个工作区需要对共用 skill 做个性化，应把它移回本地，不要在 shared-skills 里加条件分支

### 5.4 管理工具使用

`_tools/` 是本机公共工具层，只负责扫描、追踪、推荐、治理和 dashboard 数据，不放业务 skill。

```bash
# 在任意工作区下运行，生成该工作区的 skill-index.json
python3 ~/shared-skills/_tools/scan-skills.py

# 指定输出位置
python3 ~/shared-skills/_tools/scan-skills.py --output ./skill-index.json

# 只看层级结构
python3 ~/shared-skills/_tools/scan-skills.py --tree

# 搜索 skill
python3 ~/shared-skills/_tools/scan-skills.py --query "调研"
```

默认验收链：

```bash
python3 skills/scan-skills.py
python3 skills/skill-trace.py
python3 skills/skill-governance.py --query "先对齐一下工作方式"
python3 skills/skill-recommend-regression.py
```

通过标准：

- `skills/skill-index.json` 和根目录 `skill-index.json` 内容一致
- `skills/skill-dashboard.data.js` 和根目录 `skill-dashboard.data.js` 内容一致
- `skill-governance.snapshot.json` 写在当前工作区的 `skills/` 下
- `skill-recommend-regression.py` 输出 `OK`

---

## 六、验证方法

```bash
# 确认软链接完整性（在任意工作区 skills/ 下）
ls -la skills/ | grep "^l"

# 确认同一 skill 跨区指向同一文件（inode 一致）
stat -f "%i" ~/shared-skills/task-analyze/SKILL.md ~/Daily\ Work/skills/task-analyze/SKILL.md

# 重新生成索引并检查
python3 ~/shared-skills/_tools/scan-skills.py --tree
```

---

## 七、历史

- **2026-05-27**：新增 `source-intake` 到公共池，先接入 Daily Work，用于 URL/PDF/网页/资料包到 Markdown + evidence 的资料摄取前置层。
- **2026-05-27**：新增 `ui-design` 到公共池，先接入 Daily Work，用于 UI/页面/组件设计与截图验收。
- **2026-05-21**：初始建立。从 Daily Work 迁出 9 个 skill 到公共池，对齐 DW/CW/SR + harvester-ai-research 四个工作区。
