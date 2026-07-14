# Harness 管理方法

## 1. 目标

Harness 管理需要同时满足六个约束：

- **集中**：规则、清单和 skills 不再散落。
- **可复用**：复制到新工作区即可接入。
- **可追踪**：每个 bundle 有稳定 ID 和版本。
- **可验证**：发布前能机械检查结构和引用。
- **运行时中立**：核心规则不绑定具体 agent。
- **状态隔离**：私有记忆和任务状态不进入 bundle。

## 2. 七层结构

### 权威源

维护中的原始 harness。规则正文只在 `components/` 修改。

### Assembly

`assemblies/` 声明一个 bundle 由哪些组件、策略和适配器组成。Assembly 是组装配方，不直接给运行时消费。

### Bundle

从 assembly 物化出的可复用规则包。每个文件都进入 manifest 并带校验值；生成后的 bundle 不手工编辑。

### Workspace Harness

工作区内的 `harness/`，声明当前启用哪些 bundles 和 skills。这里是该工作区的 harness 内容中心。

### Runtime Adapter

根 `AGENTS.md`、`.claude/CLAUDE.md`、`.agents/skills/` 和 `.claude/skills/` 是必要的发现入口。它们只做薄适配，不复制规则正文。

### Private State

`.claude/memory/`、任务记录和用户数据属于工作区私有状态。Harness 可以声明何时按需读取，但不能把内容打进 bundle。

### Storage Mirror

存储镜像保存已验证版本，只负责备份、留存和取回。存储端不修改发布内容，也不承担运行时验收。

## 3. 标准加载顺序

1. 读取当前运行时的薄入口。
2. 读取 `harness/HARNESS.md`。
3. 读取 `harness/manifest.yaml`。
4. 按 manifest 顺序加载 bundle rules。
5. 只在任务命中时加载对应 skill。
6. 只有任务需要接续时，才按需读取私有 memory。

## 4. 标准维护顺序

1. 修改 `components/` 中的源规则或模板。
2. 需要改变组合或默认行为时，更新 `assemblies/` 和版本。
3. 使用物化脚本生成 canonical bundle。
4. 使用同一 assembly 生成示例工作区副本。
5. 运行 bundle 一致性检查、manifest 校验和负向测试。
6. 运行完整能力映射、hook 行为和 memory fixture 测试。
7. 执行目标运行时新会话烟测。
8. 提交版本后，才生成存储镜像。

## 5. 版本规则

Bundle 使用语义版本：

- `PATCH`：措辞澄清，不改变行为。
- `MINOR`：增加兼容规则或可选能力。
- `MAJOR`：改变默认行为、边界或加载契约。

已发布版本不得原地修改。工作目录可保持当前 bundle 名称，但发布身份必须由 `bundle-id + version + Git commit` 唯一确定；发生变化时更新版本并重新物化。存储镜像使用 `releases/<bundle-id>/<version>/` 保存不可变副本。

## 6. 生命周期

1. 在源组件和 assembly 中修改。
2. 重新物化 canonical bundle 和示例副本。
3. 执行结构验证、校验值检查和负向测试。
4. 人工确认入口足够薄、规则自包含、私有状态已排除。
5. 在目标运行时执行新会话烟测。
6. 提交 Git 版本。
7. 用同一 Git commit 生成存储镜像的不可变版本目录。

## 7. 发布边界

发布内容只能包含：

- manifest。
- rules。
- 被明确列入清单的 skills。
- 示例入口与说明。
- 校验脚本和测试。
- 明确列入 manifest 的 hook、维护工具和默认关闭的可选组件。

发布内容不得包含：

- 私有 memory 内容。
- 日志和对话记录。
- token、密码或私钥。
- 主机绝对路径和设备专属配置。
- 未列入 manifest 的隐式依赖。

示例工作区可以保留无真实数据的 memory 骨架，用于说明目录边界；从真实工作区生成发布副本时，必须排除整个私有 memory 目录。

## 8. LiveWithOpenCove 适配

工作区仍保留 LiveWithOpenCove 的职责分离：

- `AGENTS.md`：Codex 发现入口。
- `.claude/CLAUDE.md`：Claude 发现入口。
- `.claude/memory/`：工作区私有状态。
- `harness/`：共享工作方式、清单和规范化 skills。

v2 直接参考并迁入其 workspace skeleton 中的 `MEMORY.md`、workspace brief/map、current position、timeline、decisions、lessons、两个 archive 模板，以及 `memory_gc`、`lessons_gc`、`check_map`、`organize`。迁入后只做路径参数化和 Harness 边界适配，不携带任何真实工作区内容。

与原始骨架相比，harness 内容从多个入口文件中抽离，集中进入 `harness/`。入口文件只保留机器可发现的最小指针。

跨设备任务、设备清单和公共协作状态由外部协调系统负责；Harness 不重复维护，只规定工作区私有记忆的边界。
