# github-harvest-to-consensus examples

## 样例 1：明确仓库

### 用户输入

```text
github项目 juliusbrussee/caveman
```

### 触发判断

用户已经给出 `owner/repo`，直接补成 GitHub URL，不需要 discover。

### 应执行

```bash
gh auth status
python3 skills/harvest-tool/skill.py harvest https://github.com/juliusbrussee/caveman
python3 skills/harvest-tool/skill.py analyze juliusbrussee/caveman
```

然后分析：

- 仓库解决什么问题
- 项目成熟度
- 可直接借什么
- 改造后借什么
- 只参考什么
- 不抄什么

### 应产出

```text
task_draft/consensus/caveman-harvest-consensus-<timestamp>/
├── README.md
├── consensus.md
├── consensus.json
├── final-report.md
└── research_plan.md
```

如果用户继续问“怎么抄，拆任务”，补：

```text
copy_task_breakdown.md
```

### 不该做

- 不先搜索其他候选仓库
- 不照搬 caveman 口吻
- 不做全平台安装器

## 样例 2：模糊方向

### 用户输入

```text
找几个能借鉴的 agent skill 项目
```

### 触发判断

没有指定仓库，需要先 discover/evaluate，不直接 harvest。

### 应执行

```bash
python3 skills/harvest-tool/skill.py discover "agent skill" 10
python3 skills/harvest-tool/skill.py evaluate
```

向用户展示 shortlist，等用户确认抓哪 1 到 3 个。

### 应产出

先产出候选评估，不急着写共识目录。等用户确认仓库后再进入 harvest。

### 不该做

- 不一次抓 10 个仓库
- 不在 shortlist 未确认前写最终共识

## 样例 3：多仓库对比

### 用户输入

```text
比较 caveman / mattpocock/skills / nexu-io/html-anything，沉成共识
```

### 触发判断

用户给了多个仓库，需要逐个 harvest/analyze，再 compare-consensus。

### 应执行

```bash
python3 skills/harvest-tool/skill.py harvest https://github.com/juliusbrussee/caveman
python3 skills/harvest-tool/skill.py harvest https://github.com/mattpocock/skills
python3 skills/harvest-tool/skill.py harvest https://github.com/nexu-io/html-anything
python3 skills/harvest-tool/skill.py analyze juliusbrussee/caveman
python3 skills/harvest-tool/skill.py analyze mattpocock/skills
python3 skills/harvest-tool/skill.py analyze nexu-io/html-anything
python3 skills/harvest-tool/skill.py compare-consensus juliusbrussee/caveman mattpocock/skills nexu-io/html-anything --goal skill-system
```

### 应产出

对比型共识目录，必须说明每个仓库分别贡献什么：

- caveman：规则包产品化
- mattpocock/skills：skill 编写和组织方式
- html-anything：输出 surface 和可视化交付物

### 不该做

- 不把三者合成一个大平台目标
- 不省略“哪些不抄”

## 样例 4：用户问“怎么抄”

### 用户输入

```text
这个项目怎么抄，你分析一下，把任务点拆开
```

### 触发判断

用户要的是任务拆解，不是再次抓取。读取已有共识目录和 harvest JSON，补 `copy_task_breakdown.md`。

### 应产出

最多 5 个任务点，每个任务点都有：

- 目标
- 输入
- 输出
- 验收
- 依赖
- 需要用户确认的地方

### 不该做

- 不直接开始实现
- 不拆超过 5 步
- 不绕开用户确认去新增 skill 或改脚本
