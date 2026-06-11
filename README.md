# Shared Skills

本目录是本机公共 skill 和公共工具层。

它只服务本机多个工作区共享，不是对外发布包。

## 分层

### 公共 skill 层

这些目录会被各工作区通过软链接引用：

- `task-analyze`
- `task-decompose`
- `closeout`
- `research`
- `idea-to-research`
- `output-layer`
- `output-polisher`
- `output-style-checker`
- `ui-design`
- `source-intake`
- `harvest-tool`

规则：

- 一个 skill 只维护一份权威版本
- 工作区需要个性化时，复制回本地，不在共享版里堆条件分支
- 业务专用 skill 不放进这里

### 公共工具层

`_tools/` 只放管理工具，不作为 skill 扫描：

- `scan-skills.py`：扫描多工作区 skill，生成索引和 dashboard 数据
- `skill-trace.py`：从历史记录反推使用统计
- `skill-recommend.py`：根据用户输入推荐 skill
- `skill-governance.py`：生成治理快照
- `auto-link.sh`：补 `CLAUDE.md -> SKILL.md` 软链接
- `start-dashboard.sh`：启动本地 dashboard 静态服务

## 标准工作流

在任意工作区根目录运行：

```bash
python3 skills/scan-skills.py
python3 skills/skill-trace.py
python3 skills/skill-governance.py --query "先对齐一下工作方式"
python3 skills/skill-recommend-regression.py
```

通过标准：

- `scan-skills.py` 能生成 `skills/skill-index.json`
- 根目录 `skill-index.json` 与 `skills/skill-index.json` 内容一致
- `skill-trace.py` 能生成 `skills/skill-usage.json`
- `skill-governance.py` 能生成 `skills/skill-governance.snapshot.json`
- `skill-recommend-regression.py` 最后一行输出 `OK`

## 什么时候放进 shared-skills

满足这些条件再放：

- 至少两个工作区会用
- 不依赖某个具体项目路径
- 有 `SKILL.md`
- 有最小 README 或验收命令
- 能被 `scan-skills.py` 正常索引

不满足时留在具体工作区。

## 权威说明

- 架构：`ARCHITECTURE.md`
- 工具命令：`_tools/README.md`
