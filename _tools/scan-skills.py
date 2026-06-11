#!/usr/bin/env python3
"""
Skill 目录扫描器
扫描本地 skills 目录，读取 SKILL.md / skill.md / *.md / *.yaml frontmatter，生成 skill-index.json
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_SKILLS_DIR = SCRIPT_DIR.parent
CWD = Path.cwd()
WORKSPACE_ROOT = CWD.parent if CWD.name == "skills" else CWD
WORKSPACE_SKILLS_DIR = WORKSPACE_ROOT / "skills"
DEFAULT_INDEX_PATH = WORKSPACE_SKILLS_DIR / "skill-index.json"
ROOT_INDEX_PATH = CWD / "skill-index.json"

# === 配置 ===
DEFAULT_SCAN_PATHS = [
    os.path.expanduser("~/.claude/skills/"),
    str(WORKSPACE_ROOT / "skills"),
    str(WORKSPACE_ROOT / ".claude" / "skills"),
]

# Claude Code 内置 skills（无 SKILL.md 文件，从系统提示中提取）
# 注意：如果文件级目录中存在同名 skill，文件级优先覆盖
BUILTIN_SKILLS = {
    "task-analyze": {
        "name": "task-analyze",
        "description": "分析用户输入的意图，提取核心目标、约束条件和缺失信息。触发词：'帮我分析下'、'看看这个需求'、'我想做X'、'有个想法'、'分析一下'。类型：轻型分析器，任何新需求的第一步。",
        "status": "built-in",
        "triggers": ["分析", "需求", "想法", "看看"],
        "source": "built-in",
    },
    "bilibili-video-analyzer": {
        "name": "bilibili-video-analyzer",
        "description": "B站视频分析器 - ASR转录→Qwen结构化分析→Claude深度解读",
        "status": "built-in",
        "triggers": ["B站", "视频分析", "bilibili"],
        "source": "built-in",
    },
    "closeout": {
        "name": "closeout",
        "description": "任务结束时输出 6 段总结，建议更新记忆文件，等待用户明确确认后写入。",
        "status": "built-in",
        "triggers": ["结束", "总结", "收尾"],
        "source": "built-in",
    },
    "task-decompose": {
        "name": "task-decompose",
        "description": "将已分析的任务拆解为可执行子任务。最多 5 个子任务，一步能做完不拆。",
        "status": "built-in",
        "triggers": ["拆解", "分解", "子任务"],
        "source": "built-in",
    },
    "interview-writer": {
        "name": "interview-writer",
        "description": "顶级商业访谈记者风格的 AI 思维深化 Skill。核心流程：通过多轮自适应对话挖掘用户的故事素材 → 输出结构化访谈稿。",
        "status": "built-in",
        "triggers": ["访谈", "采访", "聊清楚", "想法"],
        "source": "built-in",
    },
    "update-config": {
        "name": "update-config",
        "description": "配置 Claude Code harness 的 settings.json。用于权限、环境变量、hooks 等。",
        "status": "built-in",
        "triggers": ["配置", "权限", "设置", "hook"],
        "source": "built-in",
    },
    "keybindings-help": {
        "name": "keybindings-help",
        "description": "自定义键盘快捷键，修改 ~/.claude/keybindings.json。",
        "status": "built-in",
        "triggers": ["快捷键", "键位", "绑定"],
        "source": "built-in",
    },
    "simplify": {
        "name": "simplify",
        "description": "Review changed code for reuse, quality, and efficiency, then fix any issues found.",
        "status": "built-in",
        "triggers": ["简化", "优化", "重构"],
        "source": "built-in",
    },
    "fewer-permission-prompts": {
        "name": "fewer-permission-prompts",
        "description": "Scan transcripts for common read-only Bash and MCP tool calls, then add a prioritized allowlist to project settings.",
        "status": "built-in",
        "triggers": ["权限提示", "allowlist", "减少提示"],
        "source": "built-in",
    },
    "loop": {
        "name": "loop",
        "description": "Run a prompt or slash command on a recurring interval.",
        "status": "built-in",
        "triggers": ["循环", "定时", "重复", "loop"],
        "source": "built-in",
    },
    "schedule": {
        "name": "schedule",
        "description": "Create, update, list, or run scheduled remote agents (routines) that execute on a cron schedule.",
        "status": "built-in",
        "triggers": ["定时任务", "cron", "计划", "schedule"],
        "source": "built-in",
    },
    "claude-api": {
        "name": "claude-api",
        "description": "Build, debug, and optimize Claude API / Anthropic SDK apps. Handles prompt caching, model migration.",
        "status": "built-in",
        "triggers": ["Claude API", "Anthropic SDK", "API", "缓存"],
        "source": "built-in",
    },
    "init": {
        "name": "init",
        "description": "Initialize a new CLAUDE.md file with codebase documentation.",
        "status": "built-in",
        "triggers": ["初始化", "CLAUDE.md", "文档"],
        "source": "built-in",
    },
    "review": {
        "name": "review",
        "description": "Review a pull request.",
        "status": "built-in",
        "triggers": ["PR", "review", "审查", "代码审查"],
        "source": "built-in",
    },
    "security-review": {
        "name": "security-review",
        "description": "Complete a security review of the pending changes on the current branch.",
        "status": "built-in",
        "triggers": ["安全", "security", "审查", "安全审查"],
        "source": "built-in",
    },
    "paper-reader": {
        "name": "paper-reader",
        "description": "基于 S. Keshav「三遍阅读法」的论文阅读 Skill。用户提供论文链接、本地 PDF 路径或 arXiv ID，AI 按「速读→精读→深读」三阶段逐步引导。触发词：/paper-reader、帮我读这篇论文、按三遍法读、读一下这篇。",
        "status": "built-in",
        "triggers": ["论文", "paper", "读论文", "三遍法", "arxiv"],
        "source": "built-in",
    },
}

EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "draft", "snapshots", "output"}

# === 多工作区扫描配置 ===
# 自动发现 ~/ 下含 .claude/ 的工作区目录（排除 ~/.claude/ 全局配置本身）
# 每个工作区会扫描下面这些相对子路径
WORKSPACE_SCAN_SUBPATHS = [
    "skills",
    ".claude/skills",
    "prompt/skills",     # legacy 兼容
    "prompts",           # 兜底（递归找 SKILL.md）
]


def parse_frontmatter_md(content: str) -> dict:
    """解析 Markdown 文件的 YAML frontmatter"""
    fm = {}
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            front = content[3:end].strip()
            # 简单解析 key: value，处理多行 description
            current_key = None
            current_val = None
            for line in front.split("\n"):
                if not line.strip() or line.strip().startswith("#"):
                    continue
                # 新 key
                m = re.match(r"^(\w+):\s*(.*)$", line)
                if m:
                    if current_key:
                        fm[current_key] = current_val.strip() if current_val else ""
                    current_key = m.group(1)
                    current_val = m.group(2)
                elif current_key and line.startswith(" "):
                    # 续行
                    current_val += " " + line.strip()
            if current_key:
                fm[current_key] = current_val.strip() if current_val else ""
    return fm


def parse_frontmatter_yaml(content: str) -> dict:
    """解析 YAML 文件的 frontmatter（简单 key: value）"""
    fm = {}
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            fm[key] = val
    return fm


def extract_triggers(description: str) -> list:
    """从 description 中提取触发词"""
    triggers = []
    m = re.search(r"触发词[：:]\s*(.+?)(?:。|$)", description)
    if m:
        text = m.group(1)
        for t in re.split(r"[、,，]", text):
            t = t.strip().strip("'\"").strip()
            if t and len(t) > 1:
                triggers.append(t)
    return triggers


def infer_domain(name: str, description: str) -> str:
    """根据名称和描述推断领域"""
    name_lower = name.lower()
    desc_lower = description.lower()

    if "github" in name_lower or "调研" in desc_lower or "research" in name_lower:
        return "research"
    if "skill" in name_lower and ("优化" in desc_lower or "评测" in desc_lower or "score" in desc_lower):
        return "quality"
    if "分析" in desc_lower or "analyzer" in name_lower:
        return "analysis"
    if "访谈" in desc_lower or "interview" in name_lower:
        return "content"
    if "api" in name_lower or "sdk" in name_lower:
        return "coding"
    if "配置" in desc_lower or "config" in name_lower or "设置" in desc_lower:
        return "tooling"
    if "安全" in desc_lower or "security" in name_lower:
        return "security"
    if "review" in name_lower or "审查" in desc_lower:
        return "quality"
    if "loop" in name_lower or "schedule" in name_lower or "定时" in desc_lower:
        return "automation"
    if "task" in name_lower:
        return "planning"
    if "openclaw" in name_lower or "远程" in desc_lower or "ssh" in desc_lower:
        return "infrastructure"
    if "harvest" in name_lower:
        return "research"
    return "general"


def find_skill_entry(dir_path: Path) -> tuple:
    """
    在目录中查找 skill 入口文件。
    返回 (文件路径, 是相对路径还是目录内)
    """
    # 优先找 SKILL.md，其次 skill.md
    for name in ["SKILL.md", "skill.md"]:
        f = dir_path / name
        if f.exists():
            return f, True
    return None, False


def scan_skill_file(file_path: Path, skill_id: str = None) -> dict:
    """扫描单个 skill 文件（.md 或 .yaml），返回结构化信息"""
    content = file_path.read_text(encoding="utf-8")

    if file_path.suffix == ".yaml":
        fm = parse_frontmatter_yaml(content)
    else:
        fm = parse_frontmatter_md(content)

    name = fm.get("name", skill_id or file_path.stem)
    description = fm.get("description", "")
    status = fm.get("status", "unknown")

    # 提取触发词
    triggers = extract_triggers(description)
    if "triggers" in fm:
        val = fm["triggers"]
        if isinstance(val, list):
            triggers = val
        elif isinstance(val, str):
            triggers = [t.strip().strip("'\"") for t in val.split(",") if t.strip()]

    # 用目录名作为默认触发词（用户说会直接用目录名调用）
    if not triggers and skill_id:
        triggers = [skill_id]

    return {
        "id": skill_id or file_path.stem,
        "name": name,
        "description": description,
        "domain": infer_domain(name, description),
        "status": status,
        "triggers": triggers,
        "path": str(file_path.resolve()),
        "format": file_path.suffix.lstrip("."),
    }


def scan_skill_directory(dir_path: Path) -> tuple:
    """扫描 skill 目录，返回 (skill_dict_or_None, [子skill...])

    即使当前目录没有 SKILL.md，也会递归扫描子目录。
    这样 packages/ 等中间目录的子 skill 也能被找到。
    """
    # 先递归扫描子目录（无论自身是否有 SKILL.md）
    children = []
    for sub in dir_path.iterdir():
        if not sub.is_dir() or sub.name.startswith(".") or sub.name in EXCLUDE_DIRS:
            continue
        child_skill, grand_children = scan_skill_directory(sub)
        if child_skill:
            children.append(child_skill)
        children.extend(grand_children)

    # 再检查自身是否有 SKILL.md
    skill_file, _ = find_skill_entry(dir_path)
    if not skill_file:
        return None, children

    skill = scan_skill_file(skill_file, dir_path.name)

    # 计算文件统计（只算当前目录下，不算子 skill 的）
    all_files = list(dir_path.rglob("*"))
    md_files = [f for f in all_files if f.suffix == ".md"]
    py_files = [f for f in all_files if f.suffix == ".py"]

    # 查找入口文件
    entry_points = []
    for f in all_files:
        if f.name in ("skill.py", "main.py", "analyze.sh"):
            entry_points.append(str(f.relative_to(dir_path)))

    skill.update({
        "has_cli": len(entry_points) > 0,
        "entry_points": entry_points,
        "file_count": {
            "total": len([f for f in all_files if f.is_file()]),
            "markdown": len(md_files),
            "python": len(py_files),
        },
        "last_modified": datetime.fromtimestamp(dir_path.stat().st_mtime).isoformat(),
    })

    return skill, children


def scan_directory(path: str) -> list:
    """扫描目录，返回扁平化的 skill 列表（含子 skill）"""
    skills = []
    p = Path(path)
    if not p.exists():
        return skills

    for item in p.iterdir():
        # 跳过隐藏目录和排除目录
        if not item.is_dir() or item.name.startswith(".") or item.name in EXCLUDE_DIRS:
            continue

        skill, children = scan_skill_directory(item)
        if skill:
            skills.append(skill)
        skills.extend(children)

    return skills


def scan_files(path: str) -> list:
    """扫描目录下的直接 .md / .yaml skill 文件（非目录形式）

    规则：
    - .md 文件只认 SKILL.md / skill.md（排除 report.md 等）
    - 用父目录名作为 skill_id
    - .yaml/.yml 文件直接用父目录名
    """
    skills = []
    p = Path(path)
    if not p.exists():
        return skills

    for f in p.iterdir():
        if not f.is_file():
            continue
        if f.suffix in (".md", ".yaml", ".yml"):
            # 排除备份文件
            if f.name.endswith(".bak") or ".bak." in f.name or f.name.endswith(".final"):
                continue
            # .md 文件只认 SKILL.md / skill.md
            if f.suffix == ".md" and f.name.lower() not in ("skill.md",):
                continue
            # 确定 skill_id：
            # - SKILL.md / skill.md → 用父目录名（如 skill-reforge/SKILL.md → skill-reforge）
            # - .yaml/.yml → 用文件名（如 remote-openclaw.yaml → remote-openclaw）
            if f.suffix == ".md":
                skill_id = f.parent.name
            else:
                skill_id = f.stem
            skill = scan_skill_file(f, skill_id)
            skill.update({
                "has_cli": False,
                "entry_points": [],
                "file_count": {"total": 1, "markdown": 1 if f.suffix == ".md" else 0, "python": 0},
                "last_modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
            skills.append(skill)

    return skills


def scan_root_skill_files(path: str) -> list:
    """扫描根目录级单文件 skill，例如 skills/task-crafter.md。"""
    skills = []
    p = Path(path)
    if not p.exists():
        return skills

    skip_names = {
        "README.md",
        "CLAUDE.md",
        "AGENTS.md",
        "MEMORY.md",
    }

    for f in p.iterdir():
        if not f.is_file():
            continue
        if f.name in skip_names:
            continue
        if f.suffix not in (".md", ".yaml", ".yml"):
            continue
        if f.name.endswith(".bak") or ".bak." in f.name or f.name.endswith(".final"):
            continue
        # 只收带 frontmatter 的单文件 skill，避免把普通文档吸进来
        content = f.read_text(encoding="utf-8", errors="ignore")
        if not content.lstrip().startswith("---"):
            continue
        skill_id = f.stem
        skill = scan_skill_file(f, skill_id)
        skill.update({
            "has_cli": False,
            "entry_points": [],
            "file_count": {"total": 1, "markdown": 1 if f.suffix == ".md" else 0, "python": 0},
            "last_modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })
        skills.append(skill)

    return skills


def discover_workspaces(home=None):
    """自动发现 ~/ 下含 .claude/ 目录的工作区。

    排除 ~/.claude/ 自身（那是全局配置，不是工作区）。
    软链接按真实路径去重（避免同一工作区被算两次）。
    返回 [{"name": str, "path": absolute_str}]。
    """
    home = Path(home or os.path.expanduser("~"))
    workspaces = []
    seen_paths = set()
    for entry in sorted(home.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if not (entry / ".claude").is_dir():
            continue
        # 按真实路径去重（处理软链接）
        real_path = entry.resolve()
        if real_path in seen_paths:
            continue
        seen_paths.add(real_path)
        workspaces.append({
            "name": entry.name,
            "path": str(real_path),
        })
    return workspaces


def slugify_workspace(name: str) -> str:
    """工作区名规范化为 id 安全前缀"""
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")


def make_skill_key(workspace_name: str, skill_id: str) -> str:
    """生成 workspace::skill_id 完整键"""
    return f"{slugify_workspace(workspace_name)}::{skill_id}"


def scan_workspace(workspace: dict) -> list:
    """扫描单个工作区下的所有 skills，返回短 id 形式的列表（未加 workspace 前缀）"""
    seen = {}
    base = Path(workspace["path"])

    for sub in WORKSPACE_SCAN_SUBPATHS:
        target = base / sub
        if not target.exists() or not target.is_dir():
            continue

        for skill in scan_directory(str(target)):
            seen[skill["id"]] = skill
        for skill in scan_files(str(target)):
            seen[skill["id"]] = skill
        for skill in scan_root_skill_files(str(target)):
            seen[skill["id"]] = skill

    return list(seen.values())


def autolink_workspace(workspace: dict) -> dict:
    """检查并修复工作区 skills/ 下的 CLAUDE.md -> SKILL.md 软链接。

    返回 {"fixed": int, "already_ok": int, "missing_skill_md": int, "log": [str]}
    """
    base = Path(workspace["path"])
    skills_dir = base / "skills"
    if not skills_dir.exists() or not skills_dir.is_dir():
        return {"fixed": 0, "already_ok": 0, "missing_skill_md": 0, "log": [], "active": False}

    fixed = 0
    already_ok = 0
    missing = 0
    log = []

    for item in skills_dir.iterdir():
        if not item.is_dir() or item.name.startswith(".") or item.name in EXCLUDE_DIRS:
            continue
        skill_file, _ = find_skill_entry(item)
        if not skill_file:
            missing += 1
            continue
        claude = item / "CLAUDE.md"
        if claude.exists() or claude.is_symlink():
            already_ok += 1
            continue
        # 创建软链接
        try:
            claude.symlink_to("SKILL.md")
            fixed += 1
            log.append(f"  ✓ {item.name}: CLAUDE.md -> SKILL.md")
        except OSError as e:
            log.append(f"  ✗ {item.name}: 链接失败 ({e})")

    return {
        "fixed": fixed,
        "already_ok": already_ok,
        "missing_skill_md": missing,
        "log": log,
        "active": True,
    }


def build_index(workspaces=None, scan_paths=None, output_path=None):
    """构建跨工作区 skill 索引。

    两种调用模式：
    - workspaces=None & scan_paths=None: 自动发现工作区（默认）
    - workspaces=[{name, path}, ...]: 指定工作区列表
    - scan_paths=[...]: 旧模式（兼容），扫描指定路径，归到 "default" 工作区
    """
    all_skills = {}            # full_key -> skill dict
    workspace_records = []     # 输出索引的 workspaces 字段

    if workspaces is None and scan_paths is None:
        workspaces = discover_workspaces()

    autolink_results = {}
    if workspaces:
        for ws in workspaces:
            ws_name = ws["name"]
            ws_skills = scan_workspace(ws)

            # autolink: 自动修复 CLAUDE.md
            al = autolink_workspace(ws)
            autolink_results[ws_name] = al

            # 建立 短id → 完整key 的映射，子包 children 也要改成完整 key
            id_map = {s["id"]: make_skill_key(ws_name, s["id"]) for s in ws_skills}

            full_keys = []
            for skill in ws_skills:
                short_id = skill["id"]
                full_key = id_map[short_id]
                skill["id"] = full_key
                skill["short_id"] = short_id
                skill["workspace"] = ws_name
                skill["workspace_path"] = ws["path"]
                if "children" in skill:
                    skill["children"] = [id_map.get(c, c) for c in skill["children"]]
                all_skills[full_key] = skill
                full_keys.append(full_key)

            workspace_records.append({
                "name": ws_name,
                "path": ws["path"],
                "skill_count": len(ws_skills),
                "skill_keys": full_keys,
                "autolink": {
                    "fixed": al["fixed"],
                    "already_ok": al["already_ok"],
                    "missing_skill_md": al["missing_skill_md"],
                },
            })
    elif scan_paths:
        # 兼容旧调用：把 scan_paths 当作 "default" 工作区
        full_keys = []
        legacy_skills = []
        for path in scan_paths:
            legacy_skills.extend(scan_directory(path))
            legacy_skills.extend(scan_files(path))
        seen = {s["id"]: s for s in legacy_skills}
        id_map = {sid: make_skill_key("default", sid) for sid in seen}
        for short_id, skill in seen.items():
            full_key = id_map[short_id]
            skill["id"] = full_key
            skill["short_id"] = short_id
            skill["workspace"] = "default"
            skill["workspace_path"] = None
            if "children" in skill:
                skill["children"] = [id_map.get(c, c) for c in skill["children"]]
            all_skills[full_key] = skill
            full_keys.append(full_key)
        workspace_records.append({
            "name": "default",
            "path": None,
            "skill_count": len(seen),
            "skill_keys": full_keys,
        })

    # 补充内置 skills（不属于任何工作区，无前缀）
    for skill_id, skill_info in BUILTIN_SKILLS.items():
        # 内置 skill key 直接用原 id；如果同名已存在（一般不会，因为文件级带 workspace 前缀），跳过
        if skill_id in all_skills:
            continue
        all_skills[skill_id] = {
            "id": skill_id,
            "short_id": skill_id,
            "workspace": None,
            "workspace_path": None,
            "name": skill_info["name"],
            "description": skill_info["description"],
            "domain": infer_domain(skill_info["name"], skill_info["description"]),
            "status": skill_info["status"],
            "triggers": skill_info["triggers"],
            "path": None,
            "format": "built-in",
            "has_cli": False,
            "entry_points": [],
            "file_count": {"total": 0, "markdown": 0, "python": 0},
            "last_modified": None,
            "source": "built-in",
        }

    # 构建层级结构：从路径里的 /packages/ 模式识别父子（父子必在同一工作区）
    for full_key, skill in list(all_skills.items()):
        path = skill.get("path") or ""
        if "/packages/" not in path or not skill.get("workspace"):
            continue
        parts = path.split("/")
        for i, part in enumerate(parts):
            if part == "packages" and i > 0:
                parent_short = parts[i - 1]
                parent_full = make_skill_key(skill["workspace"], parent_short)
                if parent_full in all_skills:
                    parent = all_skills[parent_full]
                    parent.setdefault("children", [])
                    if full_key not in parent["children"]:
                        parent["children"].append(full_key)
                break

    # 构建索引结构
    file_based = [s for s in all_skills.values() if s.get("source") != "built-in" and s.get("format") != "built-in"]
    built_in_count = len([s for s in all_skills.values() if s.get("format") == "built-in" or s.get("source") == "built-in"])
    with_children = len([s for s in all_skills.values() if s.get("children")])

    # autolink 汇总
    total_fixed = sum(r["fixed"] for r in autolink_results.values())
    total_ok = sum(r["already_ok"] for r in autolink_results.values())
    total_missing = sum(r["missing_skill_md"] for r in autolink_results.values())

    index = {
        "meta": {
            "version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "mode": "multi-workspace" if workspaces else "legacy",
        },
        "workspaces": workspace_records,
        "summary": {
            "total": len(all_skills),
            "by_status": {},
            "by_domain": {},
            "by_workspace": {ws["name"]: ws["skill_count"] for ws in workspace_records},
            "with_cli": len([s for s in all_skills.values() if s.get("has_cli")]),
            "built_in": built_in_count,
            "file_based": len(file_based),
            "with_children": with_children,
            "autolink": {
                "total_fixed": total_fixed,
                "total_ok": total_ok,
                "total_missing": total_missing,
                "by_workspace": {name: {
                    "fixed": r["fixed"],
                    "already_ok": r["already_ok"],
                    "missing": r["missing_skill_md"],
                } for name, r in autolink_results.items()},
            },
        },
        "skills": all_skills,
    }

    for skill in all_skills.values():
        status = skill.get("status", "unknown")
        domain = skill.get("domain", "general")
        index["summary"]["by_status"][status] = index["summary"]["by_status"].get(status, 0) + 1
        index["summary"]["by_domain"][domain] = index["summary"]["by_domain"].get(domain, 0) + 1

    output_file = Path(output_path) if output_path else DEFAULT_INDEX_PATH
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    root_mirror = WORKSPACE_ROOT / "skill-index.json"
    if output_file.resolve() != root_mirror.resolve():
        with open(root_mirror, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    return index


def write_dashboard_data(index: dict, usage_path=None, output_path=None):
    """写入 dashboard 本地快照，供 file:// 直开时回退使用。"""
    usage = {}
    usage_file = Path(usage_path) if usage_path else WORKSPACE_SKILLS_DIR / "skill-usage.json"
    if usage_file.exists():
        with open(usage_file, "r", encoding="utf-8") as f:
            usage = json.load(f)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "index": index,
        "usage": usage,
    }

    output_file = Path(output_path) if output_path else WORKSPACE_SKILLS_DIR / "skill-dashboard.data.js"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("window.SKILL_DASHBOARD_DATA = ")
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    root_mirror = WORKSPACE_ROOT / "skill-dashboard.data.js"
    if output_file.resolve() != root_mirror.resolve():
        with open(root_mirror, "w", encoding="utf-8") as f:
            f.write("window.SKILL_DASHBOARD_DATA = ")
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write(";\n")


def print_summary(index: dict):
    """打印索引摘要"""
    print("=" * 50)
    print(f"Skill 索引生成完成")
    print("=" * 50)
    print(f"总计: {index['summary']['total']} 个 skill")
    print(f"  - 文件级: {index['summary']['file_based']} 个")
    print(f"  - 内置: {index['summary']['built_in']} 个")
    print(f"  - 含 CLI 入口: {index['summary']['with_cli']} 个")
    print(f"  - 含子包: {index['summary']['with_children']} 个")
    print()
    workspaces = index.get("workspaces", [])
    if workspaces:
        print(f"工作区 ({len(workspaces)} 个):")
        for ws in workspaces:
            print(f"  📂 {ws['name']}: {ws['skill_count']} 个 skill  ({ws['path'] or '内置'})")
        print()
    # autolink 状态
    al = index['summary'].get('autolink', {})
    if al:
        print(f"🔗 Autolink 状态: {al['total_ok']} 就绪 / {al['total_fixed']} 修复 / {al['total_missing']} 缺 SKILL.md")
        for ws_name, ws_al in al.get('by_workspace', {}).items():
            print(f"   {ws_name}: {ws_al['already_ok']} 就绪, {ws_al['fixed']} 修复, {ws_al['missing']} 缺入口")
        print()
    print("按状态分布:")
    for status, count in sorted(index['summary']['by_status'].items()):
        print(f"  {status}: {count}")
    print()
    print("按领域分布:")
    for domain, count in sorted(index['summary']['by_domain'].items(), key=lambda x: -x[1]):
        print(f"  {domain}: {count}")
    print()
    print(f"索引文件: {DEFAULT_INDEX_PATH}")
    print("=" * 50)


def print_hierarchy(index: dict):
    """打印层级结构"""
    print("\n层级结构（含子包）:")
    print("=" * 50)

    # 找出有子包的
    for sid, skill in index["skills"].items():
        if "children" in skill:
            print(f"\n📁 {sid} [{skill['status']}]")
            print(f"   描述: {skill['description'][:60]}...")
            print(f"   子包:")
            for child_id in skill["children"]:
                child = index["skills"].get(child_id)
                if child:
                    print(f"      └─ {child_id} [{child['status']}] {child['description'][:50]}...")

    # 独立 skill（无父无子）
    child_ids = set()
    for s in index["skills"].values():
        child_ids.update(s.get("children", []))

    standalone = [sid for sid, s in index["skills"].items()
                  if "children" not in s and sid not in child_ids and s.get("format") != "built-in"]
    if standalone:
        print("\n📄 独立文件级 Skills:")
        for sid in standalone:
            s = index["skills"][sid]
            print(f"   {sid} [{s['status']}] {s['description'][:50]}...")

    print("=" * 50)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="跨工作区扫描 skill 目录，生成统一索引")
    parser.add_argument("--paths", nargs="+", help="[legacy] 直接指定要扫的路径，不用工作区发现")
    parser.add_argument("--workspaces", nargs="+", help="手动指定工作区路径列表（绕过自动发现）")
    parser.add_argument("--home", help="工作区发现的家目录（默认 ~/）")
    parser.add_argument("--output", default=str(DEFAULT_INDEX_PATH), help="输出文件路径")
    parser.add_argument("--list", action="store_true", help="列出所有 skill 名称")
    parser.add_argument("--query", help="按关键词搜索 skill")
    parser.add_argument("--tree", action="store_true", help="显示层级结构")
    args = parser.parse_args()

    if args.paths:
        # 旧模式：直接扫指定路径
        index = build_index(scan_paths=args.paths, output_path=args.output)
    elif args.workspaces:
        # 手动工作区列表
        ws_list = [{"name": Path(p).name, "path": str(Path(p).resolve())} for p in args.workspaces]
        index = build_index(workspaces=ws_list, output_path=args.output)
    else:
        # 默认：自动发现工作区
        ws_list = discover_workspaces(home=args.home)
        index = build_index(workspaces=ws_list, output_path=args.output)

    write_dashboard_data(index)

    if args.tree:
        print_hierarchy(index)
    elif args.list:
        print("\n所有技能列表:")
        for sid in sorted(index["skills"].keys()):
            s = index["skills"][sid]
            marker = "📁" if "children" in s else "  "
            ws_tag = f"[{s.get('workspace')}] " if s.get("workspace") else "[built-in] "
            print(f"  {marker} {ws_tag}[{s['status']}] {sid}: {s['description'][:60]}...")
    elif args.query:
        query = args.query.lower()
        print(f"\n搜索 '{args.query}':")
        matches = []
        for sid, s in index["skills"].items():
            text = f"{sid} {s['name']} {s['description']} {' '.join(s.get('triggers', []))}"
            if query in text.lower():
                matches.append(s)
        if matches:
            for s in matches:
                ws_tag = f"[{s.get('workspace')}] " if s.get("workspace") else "[built-in] "
                print(f"  - {ws_tag}{s['id']} ({s['domain']}): {s['description'][:80]}...")
        else:
            print("  无匹配")
    else:
        print_summary(index)
        print_hierarchy(index)
