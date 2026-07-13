# github-harvest-to-consensus acceptance

## 命令验收

### 1. GitHub CLI 可用

```bash
gh auth status
```

通过标准：

- 返回已登录账号
- 没有 auth error

### 2. 仓库可抓取

```bash
python3 skills/harvest-tool/skill.py harvest https://github.com/<owner>/<repo>
```

通过标准：

- 输出“抓取完成”
- `skills/harvest-tool/data/harvest_<owner>_<repo>.json` 存在
- 至少抓到 README 或目录结构

### 3. 分析材料可生成

```bash
python3 skills/harvest-tool/skill.py analyze <owner>/<repo>
```

通过标准：

- 输出仓库画像
- 输出材料置信度
- 输出 README/目录/核心文件摘要

### 4. 共识可落盘

```bash
python3 skills/harvest-tool/skill.py consensus '<json>'
```

通过标准：

- `task_draft/consensus/<slug-timestamp>/` 存在
- `consensus.md` 存在
- `consensus.json` 存在
- `README.md` 存在

### 5. JSON 可解析

```bash
python3 -m json.tool task_draft/consensus/<slug-timestamp>/consensus.json >/tmp/consensus-check.txt
```

通过标准：

- 命令退出码为 0

## 内容验收

共识报告必须包含：

- 仓库解决什么问题
- 直接用
- 改造用
- 只参考
- 不抄
- 风险
- 不确定性
- 下一步最小行动
- 用户可验证路径

## MVP 边界验收

本任务不应出现：

- 未经确认的新 skill 目录
- installer
- hook
- statusline
- 默认改变用户沟通风格
- 跨 30+ agent 的平台化设计

## 用户回复验收

最终回复必须说清：

- 产物在哪里
- 用户现在能看什么
- 如何验证成功
- 没做什么
- 下一步需要用户拍板什么
