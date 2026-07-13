# DEVICES — 设备与连接权威清单

> 日期：2026-06-19（实测）
> 这是所有跨设备连接信息的唯一权威。任务的 artifacts.md 要写跨设备产物时，引用这里的设备名，不复制连接细节。
> 全部经 Tailscale 组网。下面的"状态"是实测结果，不是记忆。

---

## 一、设备一览（Tailscale）

| 设备名(Tailscale) | IP | 系统 | SSH 登录 | 实测状态 |
|---|---|---|---|---|
| xinyuemacbook | 100.120.195.99 | macOS | 本机 | 本机 |
| userysys | 100.113.27.115 | linux | `ssh userysys@100.113.27.115` | ✅ 免密通 |
| iZ2zeh...（ECS） | 100.117.194.114 | linux | `ssh root@100.117.194.114` | ✅ 免密通 |
| sure（Win） | 100.118.92.53 | windows | `ssh sure-win` | ✅ 已重新接入；Codex/Claude 入口均已验证（2026-07-13） |
| xyy | 100.74.95.81 | linux | — | ⛔ 离线（86 天前） |

> 注：Tailscale 账户下所有设备 owner 显示 `shuoy1230@`。Win 设备 Tailscale 主机名 `sure`，SSH 登录用户 `sure`（2026-07-13 重装后用户名与机器名一致，不再区分）。在本机一律使用 `ssh sure-win`；该别名在 `~/.ssh/config` 中指向 `sure@100.118.92.53`。

---

## 二、OpenCove 服务链路（userysys + ECS）

```
opencove.xihongshichaojidan.top
  → ECS(100.117.194.114) Nginx 公网入口  /etc/nginx/sites-enabled/opencove
  → ECS FRP Server (vhostHTTPPort=8089)   /etc/frp/frps.toml
  → userysys(100.113.27.115) FRP Client   /etc/frp/frpc.toml
  → userysys opencove-worker.service       OpenCove 实际运行宿主
```
运维用 `opencove-remote-deploy` skill：`status` / `verify` / `build-live`。详见该 skill 的 `references/topology.md`。

---

## 三、Win 设备（sure@100.118.92.53）

**当前状态：✅ 2026-07-13 已重新接入**。登录用户 `sure`（whoami=`desktop-f24ajub\sure`），主机名 `DESKTOP-F24AJUB`，路径 `C:\Users\Sure\...`。本机一律使用 `ssh sure-win`；Tailscale 地址 `100.118.92.53` 只在本文件维护。已实测可 SSH、可 ping ECS、可从 Windows SSH 到 ECS；hub 工作副本、Claude Code 和 Codex 已按新路径恢复。Codex 使用 `gpt-5.6-terra`，启动级 hub 读取测试已通过。

原 F 盘（files）变为 H 盘。链路：`Mac → SSH → Win → PowerShell/cmd`；同步链路：`Win → Tailscale → ECS Git hub`。

历史用途：
- Arduino：`Mac → SSH → Win → Arduino CLI → COM6 → Uno R3`；ESP32-S3 用 COM8
- GT-Power：`Win → GT-POWER 2016` 跑发动机仿真
- 汽车课设：Win 桌面曾有 `vehicle control` 文件夹（产物已在 Mac 本地有副本，见 tasks/vehicle-control/artifacts.md，日常不需连 Win）

---

## 四、用法约定

- 任务要登记跨设备产物 → 在 artifacts.md 写"设备名（见 DEVICES.md）+ 该设备上的路径"，不重复抄 IP/连接方式。
- 连接信息变了 → 只改本文件，实测后更新"状态"列。
- 不确定能不能连 → 先 `tailscale status` 看在线，再 `ssh ... whoami` 实测，不靠记忆。
