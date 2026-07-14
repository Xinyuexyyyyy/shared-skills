---
name: example-status
description: 当用户询问当前 harness、规则包、入口或私有状态边界时，报告示例工作区的 harness 状态。
status: stable
---

# Example Status

读取 `../../manifest.yaml`，并用简短中文回答：

- 当前 workspace ID 和版本。
- 已启用 bundle 的 ID 和版本。
- 当前可用 skills。
- 私有状态排除目录。

只报告 manifest 中存在的内容。不要修改文件，不要读取私有 memory，不要推断未声明能力。
