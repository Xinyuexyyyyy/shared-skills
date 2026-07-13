# EXPORTS — 权威源与单向导出登记

> 日期：2026-06-18（建立）
> 配套：[ARCHITECTURE.md](ARCHITECTURE.md)、[CONSENSUS-workspace-reorg-20260618.md](CONSENSUS-workspace-reorg-20260618.md)
> 本文件是"哪个 skill 的权威在哪、导出到哪个开源仓库"的唯一登记表。

---

## 一、核心规则

1. **按领域分两个权威源**：
   - **通用层权威** = `~/shared-skills/`（task / output / research 底座 / harvest / idea-to-research 等）
   - **学术线权威** = `~/study-research/skills/`（paper 流水线 / academic-* / survey / supervisor-scout / topic-framing / method-design 等）
2. **导出是单向的**：开源仓库（LiveWithOpenCove、research-skills-pack）是权威源的**裁剪发布快照**。
   - 改 skill 只在权威源改。
   - 导出方向：权威源 → 开源仓库。**禁止反向手改**开源仓库里的 skill 再指望同步回来。
   - 如果在开源仓库里发现改动需求，回到权威源改，再重新导出。
3. **工作区消费**：三个工作区（DailyWork / ContentWork / study-research）通过 `skills/` 下软链消费权威源；全局 `~/.claude/skills/` 是去重后的统一入口（一个 skill 一个入口，详见 ARCHITECTURE.md）。

---

## 二、LiveWithOpenCove（教学骨架，5 skill）

> GitHub: Xinyuexyyyyy/LiveWithOpenCove · 受众：想抄这套 setup 的开源用户 · 定位：最小骨架，精简删减版

| 导出的 skill | 权威源 | 备注 |
|---|---|---|
| closeout | shared-skills | 骨架版可能比权威版精简（实测 302 行 vs 权威 498 行） |
| idea-to-research | shared-skills | |
| output-polisher | shared-skills | |
| task-analyze | shared-skills | |
| task-decompose | shared-skills | |

导出位置：`LiveWithOpenCove/shared-skills-skeleton/`
裁剪原则：只导出"通用、与具体业务无关、教学价值高"的基础 skill。教学版允许精简，但不得包含权威版没有的新逻辑。

---

## 三、research-skills-pack（学术发行包，24 skill）

> GitHub: Xinyuexyyyyy/research-skills-pack · 受众：要做学术科研的人 · 定位：学术线完整发行 + Windows 安装

### 来自 shared-skills（通用层，7 个）
closeout · idea-to-research · output-layer · output-polisher · output-style-checker · research · task-analyze · task-decompose

### 来自 study-research（学术线，15 个）
academic-deep-research · academic-plotting · knowledge-compiler · method-design · paper-composer · paper-discovery · paper-reading · paper-screening · research-academic · research-ideation · rigor-reviewer · supervisor-scout · survey-writer · topic-framing

### pack 独有（权威即在 pack 自身，2 个）
workspace-init · workspace-tidy
> 这两个是安装/维护脚手架，不在另外两个权威源里。它们的权威就是 research-skills-pack 自己。

导出位置：`research-skills-pack/skills/`
裁剪原则：导出学术线全套 + 通用层中学术流程依赖的部分。

---

## 四、导出操作约定（暂为人工，未自动化）

当前没有自动导出脚本。导出 = 人工把权威源对应 skill 复制/精简到开源仓库。

每次导出后应：
1. 在对应开源仓库 commit，说明本次从哪个权威源、哪个版本导出。
2. 若导出时做了裁剪（如教学版精简），在该仓库的 README/MANIFEST 注明"本版为精简版，完整版见权威源"。

> TODO（按需，不急）：写一个 `_tools/export.sh`，按本表把权威源 skill 同步到两个开源仓库，避免手工漏同步。真有维护频率了再做。

---

## 五、与"光盘层"约定的关系

光盘层（见 ARCHITECTURE.md 第 8 节）解决的是"同一逻辑、不同工作区要不同配置"；
本文件解决的是"同一逻辑、要发布给不同受众"。
两者都遵循同一个内核：**逻辑只有一份权威，其余都是它的投影**（工作区投影 = 软链 + 可选配置；开源投影 = 单向导出快照）。
