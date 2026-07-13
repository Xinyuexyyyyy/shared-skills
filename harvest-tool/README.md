# Harvest Tool

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 一句话

`harvest-tool` 用来做 GitHub 借鉴型调研：先找仓库，再筛 shortlist，再抓资料，最后沉成共识文档。

## 常用任务书

- `docs/github-harvest-to-consensus.md`：用户给 GitHub 仓库和主题任务时，按“抓取 -> 分析 -> 借鉴分层 -> 共识落盘 -> 验收说明”生成结构化共识草稿。
- `docs/github-harvest-examples.md`：典型输入的 Before/After 和执行判断。
- `docs/github-harvest-acceptance.md`：最小验收清单。

## 安装

```bash
# 1. 克隆仓库
git clone https://github.com/Xinyuexyyyyy/harvest-tool.git
cd harvest-tool

# 2. 确保 GitHub CLI 已安装并登录
gh auth status
# 如果未登录，先运行：gh auth login

# 3. 直接运行（无需额外 Python 依赖）
python3 skill.py discover "deep research" 5
```

或使用 pip 安装：

```bash
pip install -e .
harvest discover "deep research" 5
```

## 先看效果

你给一句目标，比如：

- “帮我找几个能借鉴的 deep research 项目”
- “我想做一个微信工作台，先帮我看现成开源方案”
- “这几个 GitHub 仓库里，哪个最值得抄第一版”

系统内部会按这条顺序跑：

1. discover 候选仓库
2. evaluate 做第一轮筛选
3. 等你确认要继续看的仓库
4. harvest 抓重点资料
5. analyze 提炼借鉴点
6. consensus 正式落盘

## 主入口

普通使用时，不要让用户手敲命令。用户讲目标，系统内部调用即可。

调试或验收时可直接运行：

```bash
python3 skill.py discover "deep research" 5
python3 skill.py evaluate
python3 skill.py harvest https://github.com/langchain-ai/open_deep_research
python3 skill.py analyze open_deep_research
python3 skill.py compare open_deep_research obra/superpowers
python3 skill.py compare obra/superpowers langchain-ai/open_deep_research --goal application
python3 skill.py compare-consensus obra/superpowers langchain-ai/open_deep_research --goal workflow
```

## 什么时候该停

- `gh auth status` 失败时先停
- 仓库链接不是标准 GitHub 地址时先停
- 搜索结果明显跑偏时先停，先换关键词
- 抓取资料不够时先停，不强行下“可直接抄”的结论

## 关键目录

- `data/`
  保存 discover / evaluate / harvest / analyze 的中间产物（自动创建，默认在 .gitignore 中排除）
- `task_draft/consensus/`（或自定义目录）
  保存最终共识文档；Stage 6 会为每轮结果创建独立子目录，并同步写一份 `latest_consensus.json`
- `data/compare_results.json`
  保存最近一轮批量比较结果，便于做 shortlist

## 最小验收

先确认 GitHub CLI 已登录：

```bash
gh auth status
```

再跑一轮最小烟雾：

```bash
python3 skill.py discover "deep research" 3
python3 skill.py evaluate
```

看到候选项目列表，并能输出评估输入材料，就说明这条高频主链还是通的。
