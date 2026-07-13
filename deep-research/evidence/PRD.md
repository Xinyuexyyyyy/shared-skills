# AI 多平台余额统一监控仪表盘 PRD — v0.2

## 1. 产品概述

基于 **CodexBar**（macOS 原生菜单栏 App）构建统一余额监控。DeepSeek 和 Kimi 原生支持即开即用，为 packyapi 和 xcode 两个 one-api 中转站编写自定义 Swift Provider，实现菜单栏一看就知道所有渠道余额——类"桌宠"体验，点开弹出概览，无需开浏览器。

## 2. 目标用户

- **主要用户：** 你（个人使用）
- **用户痛点：** 多个中转站和官方 API 散布各处，提醒邮件不常看，经常用到一半发现余额不足才被迫停下
- **不做会怎样：** 继续靠记忆和猜测判断余额，随时可能被某个渠道"抛锚"，打断工作流

## 3. 价值假设

我们相信 [菜单栏统一余额监控] 能帮助 [你] 解决 [多渠道余额分散无法实时感知] 的痛点，从而 [避免因余额不足导致的意外中断，提升 AI 工具使用体验]。

## 4. MVP 范围

第一版必须包含的能力：

1. **CodexBar 基础安装**
   - `brew install --cask codexbar` 安装
   - 配置 **DeepSeek**（API Key，调用 `/user/balance`）
   - 配置 **Kimi**（API Key，原生支持）
   - DeepSeek 和 Kimi 的余额即时可用

2. **自定义 One-API Provider（Swift）**
   - 为 CodexBar 编写一个 one-api 通用 provider
   - 调用 `GET /api/user/self`（Authorization: Bearer access_token）
   - 解析 `quota` 字段，换算为可读金额
   - 适配 **packyapi** 和 **xcode** 两个中转站（各有独立配置）

3. **菜单栏体验**
   - 菜单栏图标显示精选余额或汇总状态
   - 点击弹出各渠道余额卡片（DeepSeek / Kimi / packyapi / xcode）
   - 每 5 分钟自动刷新（可配置）
   - 渠道异常时状态标记（错误/过时）

## 5. Out of Scope（不做，第一版不碰）

1. **right_code 接入** —— 缺少 access token，暂不接入，等找到方案再补
2. **告警通知**（低余额推送/Bark/Server酱/Telegram）—— 先让你能看见，再考虑推给你
3. **模型级用量拆分**（按模型看消耗明细）
4. **Web 仪表盘** —— 菜单栏才是主入口，不额外搭 Web 服务
5. **历史曲线/趋势图** —— CodexBar 原生不支持，后续看需求
6. **多用户/团队管理**
7. **自动充值**

## 6. Future（未来做）

1. **right_code 接入** —— 找到 access token 或替代方案后补上
2. **低余额标记/告警** —— 余额低于阈值时菜单栏图标变色或弹通知
3. **多个 one-api 自动发现** —— 类似 Metapi 的自动发现机制
4. **用量趋势** —— 本地存历史快照，画简单曲线
5. **iPhone Widget** —— CodexBar 已支持 WidgetKit

## 7. 验收标准

| # | 标准 | 验证方式 |
|---|------|----------|
| 1 | 菜单栏出现 CodexBar 图标 | 肉眼确认 |
| 2 | DeepSeek 和 Kimi 余额正确显示 | 与官网后台对照 |
| 3 | packyapi 和 xcode 余额正确显示 | 与中转站后台对照 |
| 4 | 点击图标弹出 4 张余额卡片 | 点击确认 |
| 5 | 刷新后数据实时更新 | 等 5 分钟后再看 |
| 6 | 某个渠道掉线时显示错误状态 | 故意填错一个 token 观察 |
| 7 | 应用随 macOS 开机自启 | 重启确认菜单栏自动出现 |

## 8. 关键风险

| 风险 | 状态 | 说明 |
|------|------|------|
| One-API `/api/user/self` 返回值格式 | **待验证** | 不同 one-api 版本/实例返回值可能不同，packyapi 和 xcode 需逐一实测 |
| Access Token 有效期 | **已知** | token 有有效期，到期需手动更新 |
| 本地构建 CodexBar 门槛 | **已确认** | 需要 Xcode 16+，macOS 原生 Swift 开发环境 |
| DeepSeek/Kimi 原生支持稳定性 | **已确认** | CodexBar v0.37+ 已稳定支持 |
| CodexBar 更新是否冲掉自定义 provider | **待评估** | 需要评估 provider 的集成方式（fork vs 补丁） |

## 9. 推荐方案

**推荐：CodexBar + 自定义 One-API Swift Provider**

| 方案 | 体验 | 官方 API 支持 | 中转站支持 | 开发量 |
|------|------|:------------:|:----------:|:------:|
| **CodexBar** ⭐ | 菜单栏原生桌宠 | ✅ DeepSeek、Kimi 即有 | 写 1 个 provider | **最小** |
| Token Balance Monitor | Web + 菜单栏 + iPhone | ✅ DeepSeek、Kimi 即有 | 写 TS 适配器 | 中等 |
| AIMeter | Web 看板 | 需写适配器 | 需写适配器 | 最大 |
| Metapi | Web 看板 | ❌ 不适配官方 | ✅ 原生 | 需补官方 |

选择 **CodexBar** 的理由：
- **零成本覆盖 DeepSeek + Kimi**——装上就能用，不需要做任何开发
- **你要的就是桌宠体验**——菜单栏图标、点击弹出、一目了然
- **写一个 provider 覆盖两个站**—— packyapi 和 xcode 都是 one-api 接口，一个 provider 搞定
- macOS 原生，保活、自刷新、开机自启全有
- 活跃维护（v0.37+），社区大，遇到问题容易找到答案

不选其他方案的理由：
- **Token Balance Monitor** 虽然也有桌宠，但它是 Webview 套壳，体验和 Swift 原生有差距，社区也小
- **AIMeter** 是 Web 面板，你要的是桌宠，方向不对
- **Metapi** 把中转站管得很好，但不支持 DeepSeek / Kimi，分两套看更麻烦

## 10. 下一步

### 实施步骤

```
Phase A：环境准备
  ├─ brew install --cask codexbar
  ├─ 配 DeepSeek API Key → 确认余额显示正常
  └─ 配 Kimi API Key → 确认余额显示正常

Phase B：接口实测
  ├─ 拿 packyapi 的 access token 调 curl /api/user/self
  ├─ 拿 xcode 的 access token 调 curl /api/user/self
  └─ 确认返回格式（特别是 quota 字段和金额换算关系）

Phase C：编写 Provider
  ├─ fork CodexBar 仓库
  ├─ 参照 DeepSeek Provider 的模式，写 OneAPIProvider.swift
  └─ 本地 Xcode 构建验证

Phase D：验证上线
  ├─ 确认菜单栏显示 4 个渠道
  ├─ 观察 24 小时自动刷新稳定性
  └─ 把改动提交到自己的仓库（备用）
```

### 需要你提供的凭证

| 渠道 | 需要 | 状态 |
|------|------|:----:|
| DeepSeek | API Key（sk-...） | ✅ 已有 |
| Kimi | API Key（或 Cookie） | ✅ 需确认 |
| packyapi | access token（one-api 后台生成） | ❓ 需找到 |
| xcode | access token（one-api 后台生成） | ❓ 需找到 |

### 预估工作量

| 阶段 | 耗时 |
|------|:----:|
| Phase A：装 CodexBar + 配置 DeepSeek/Kimi | ~10 分钟 |
| Phase B：实测接口格式 | ~15 分钟 |
| Phase C：写 One-API Provider | ~1.5 小时 |
| Phase D：验证 + 微调 | ~30 分钟 |
| **总计** | **~2.5 小时** |
