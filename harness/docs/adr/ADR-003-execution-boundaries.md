# ADR-003：脚本、配置、文本的执行边界

状态：accepted for draft

配置声明事实、阈值、状态和能力分类；`harnessctl` 执行路径、Schema、SHA-256、预算、发布门和 health；短 Markdown 只解释运行时如何发现同一份语义资产。任何 hard-enforced 能力都必须同时具有脚本、注册点和测试证据，否则校验失败。

本阶段不引入常驻 Runner，不持久化真实 Turn Envelope，不把复杂行为规则重新复制成大型入口文件。
