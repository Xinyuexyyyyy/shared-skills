# Shared Tools

这里放的是本机公共 skill 工具，不是 skill 本体。

## 命令

- `scan-skills.py`
  - 扫描多个工作区的 skills
  - 生成 `skill-index.json`
  - 同步 `skill-dashboard.data.js`
- `skill-trace.py`
  - 从历史日志反推使用记录
  - 生成 `skill-usage.json`
- `skill-recommend.py`
  - 根据用户输入推荐 skill
  - 供对话路由和治理快照复用
- `skill-governance.py`
  - 汇总索引、使用记录、评分和当前焦点
  - 生成治理快照
- `auto-link.sh`
  - 检查并补 `CLAUDE.md -> SKILL.md` 软链接
- `start-dashboard.sh`
  - 启动本地静态 dashboard 服务

## 默认验收

```bash
cd /Users/sure/Daily\ Work
python3 skills/scan-skills.py
python3 skills/skill-trace.py
python3 skills/skill-governance.py --query "先对齐一下工作方式"
python3 skills/skill-recommend-regression.py
```

## 路径规则

- 优先站在当前工作区根目录
- 共享软链接环境下，优先找当前工作区的 `skills/`
- 根目录镜像只保留兼容

## 不做什么

- 不放业务 skill
- 不做对外发布包
- 不在这里塞工作区个性化分支
