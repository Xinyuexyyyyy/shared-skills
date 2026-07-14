# Context Rules

1. 先读取工作区入口，再读取 `harness/HARNESS.md` 和 manifest。
2. 只加载当前任务需要的 bundle 和 skill。
3. 私有 memory 默认不读；仅在用户要求接续已有任务时按需读取。
4. 不把对话历史、任务记录或 memory 复制进 harness bundle。
5. 路径和引用必须相对工作区，不能依赖某台机器的目录结构。
6. 找不到声明文件时停止使用对应能力，并明确报告缺口。
