#!/usr/bin/env python3
"""PreToolUse hook: 拦截危险 Bash 命令。

职责单一:只拦明确高危、不可逆的命令,其余放行。
遵循 HOOKS-RESPONSIBILITY.md 铁律:出错静默 exit 0,绝不阻断会话。

拦截方式:输出 JSON permissionDecision=deny,Claude 收到后据此调整。
退出码 0 + deny JSON = 软拦截(Claude 看到原因,可改策略),不是硬杀。
"""
import json
import re
import sys

# 高危模式:不可逆 / 大范围破坏。宁可少拦,不误伤日常命令。
DANGER_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r", "rm -rf(递归强制删除)"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard(丢弃未提交改动)"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean -f(删未跟踪文件)"),
    (r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b", "git push --force"),
    (r":\s*\(\)\s*\{.*\}\s*;\s*:", "fork bomb"),
    (r"\bmkfs\b", "格式化文件系统"),
    (r"\bdd\s+.*of=" + "/" + "dev/", "dd 写入块设备"),
    (r">\s*" + "/" + r"dev/sd[a-z]", "直接写磁盘设备"),
    (r"\bDROP\s+(TABLE|DATABASE)\b", "SQL DROP TABLE/DATABASE"),
    (r"\bTRUNCATE\s+TABLE\b", "SQL TRUNCATE"),
]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # 读不到输入,放行

    tool = data.get("tool_name", "")
    if tool != "Bash":
        sys.exit(0)

    cmd = (data.get("tool_input", {}) or {}).get("command", "")
    if not cmd:
        sys.exit(0)

    for pat, desc in DANGER_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            reason = (
                f"⚠️ 危险命令拦截:{desc}。"
                f"这条命令不可逆或破坏范围大。如果确实需要,请向用户说明风险并取得确认,"
                f"或改用更安全的等价做法(如指定具体路径、先备份、用 git stash 代替 reset --hard)。"
            )
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }))
            sys.exit(0)

    sys.exit(0)  # 没命中,放行


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)  # 任何意外都不阻断会话
