from __future__ import annotations

"""
Harvest Tool - Stage 4: 抓取
输入: 用户确认的 GitHub URL
输出: README + 目录结构 + 核心代码文件
依赖: gh CLI 已登录
"""

import sys
import os
import time
import subprocess
import json
from pathlib import PurePosixPath

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.utils import (
    fetch_readme,
    fetch_file_content,
    save_json,
    normalize_github_repo_url,
    check_gh_cli_ready,
)
from configs.settings import OUTPUT_DIR, REQUEST_DELAY, MAX_FILES_TO_FETCH

PREFERRED_SOURCE_FILENAMES = {
    "main.py",
    "main.ts",
    "main.tsx",
    "main.js",
    "main.rs",
    "main.go",
    "index.py",
    "index.ts",
    "index.tsx",
    "index.js",
    "app.py",
    "app.ts",
    "app.tsx",
    "app.js",
    "server.py",
    "server.ts",
    "server.js",
    "cli.py",
    "cli.ts",
    "cli.js",
    "__init__.py",
}
PREFERRED_DOC_FILENAMES = {
    "README.md",
    "ARCHITECTURE.md",
    "INSTALLATION.md",
    "QUICKSTART.md",
    "TROUBLESHOOTING.md",
    "WORKFLOW.md",
}
PREFERRED_TEST_PREFIXES = ("test_", "test.", "spec.", "spec_")
CODE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".rs",
    ".go",
    ".java",
    ".kt",
    ".swift",
    ".rb",
    ".php",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".sh",
}
MAX_SKILL_SAMPLES_TO_FETCH = 5
SKILL_BUCKET_PRIORITY = {
    "engineering": 0,
    "productivity": 1,
    "misc": 2,
    "shared": 3,
    "stable": 4,
    "personal": 20,
    "in-progress": 30,
    "deprecated": 40,
}


def _run_gh_directory_listing(owner: str, repo: str, path: str, timeout: int = 10) -> tuple[list[dict], str | None]:
    api_path = f"repos/{owner}/{repo}/contents/{path}".rstrip("/")
    try:
        result = subprocess.run(
            ["gh", "api", api_path, "--jq", ".[] | {name, path, type, download_url}"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return [], "gh CLI 不可用"
    except Exception as exc:
        return [], str(exc)

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip() or "未知错误"
        return [], detail

    items = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        items.append(json.loads(line))
    return items, None


def _is_not_found_error(message: str | None) -> bool:
    text = (message or "").lower()
    return "not found" in text or "404" in text


def _fetch_repo_file(owner: str, repo: str, path: str) -> dict | None:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
    content = fetch_file_content(url)
    if not content:
        return None
    return {
        "name": path,
        "path": path,
        "url": url,
        "content": content[:3000],
        "size": len(content),
    }


def _append_unique_file(fetched: dict, bucket: str, file_data: dict | None, seen_paths: set[str]) -> None:
    if not file_data:
        return
    path = file_data.get("path") or file_data.get("name")
    if not path or path in seen_paths:
        return
    fetched[bucket].append(file_data)
    seen_paths.add(path)


def _score_source_item(item: dict, parent_dir: str) -> tuple[int, str]:
    path = item.get("path", "")
    name = item.get("name", "")
    suffix = PurePosixPath(name).suffix.lower()
    score = 0

    if name in PREFERRED_SOURCE_FILENAMES:
        score += 100
    if parent_dir == "tests":
        if name.startswith(PREFERRED_TEST_PREFIXES) or ".test." in name or ".spec." in name:
            score += 90
    if suffix in CODE_EXTENSIONS:
        score += 40
    if name.lower().startswith(("main", "index", "app", "server", "cli")):
        score += 20
    if "example" in path.lower() or "demo" in path.lower():
        score -= 10
    return (-score, path)


def _score_doc_item(item: dict) -> tuple[int, str]:
    path = item.get("path", "")
    name = item.get("name", "")
    score = 0
    if name in PREFERRED_DOC_FILENAMES:
        score += 100
    if name.lower().endswith(".md"):
        score += 40
    if "spec" in path.lower() or "architecture" in path.lower():
        score += 20
    return (-score, path)


def _select_representative_files(
    owner: str,
    repo: str,
    directory: str,
    *,
    limit: int,
    mode: str = "source",
    descend_one_level: bool = True,
) -> tuple[list[dict], list[str]]:
    items, error = _run_gh_directory_listing(owner, repo, directory)
    if error:
        return [], [f"目录 {directory} 抓取失败: {error}"]

    files = [item for item in items if item.get("type") == "file"]
    subdirs = [item for item in items if item.get("type") == "dir"]
    errors: list[str] = []
    selected_paths: list[str] = []

    if mode == "docs":
        files.sort(key=_score_doc_item)
    else:
        files.sort(key=lambda item: _score_source_item(item, directory))

    for item in files[:limit]:
        path = item.get("path", "")
        if path:
            selected_paths.append(path)

    if len(selected_paths) >= limit or not descend_one_level:
        return [_fetch_repo_file(owner, repo, path) for path in selected_paths if path], errors

    for subdir in subdirs:
        if len(selected_paths) >= limit:
            break
        nested_path = subdir.get("path", "")
        nested_items, nested_error = _run_gh_directory_listing(owner, repo, nested_path)
        if nested_error:
            errors.append(f"目录 {nested_path} 抓取失败: {nested_error}")
            continue

        nested_files = [item for item in nested_items if item.get("type") == "file"]
        if mode == "docs":
            nested_files.sort(key=_score_doc_item)
        else:
            nested_files.sort(key=lambda item: _score_source_item(item, directory))

        for nested_item in nested_files:
            nested_file_path = nested_item.get("path", "")
            if not nested_file_path or nested_file_path in selected_paths:
                continue
            selected_paths.append(nested_file_path)
            break

    return [_fetch_repo_file(owner, repo, path) for path in selected_paths if path], errors


def _select_skill_samples(owner: str, repo: str, *, limit: int = MAX_SKILL_SAMPLES_TO_FETCH) -> tuple[list[dict], list[str]]:
    """Fetch representative SKILL.md files from one-level or bucketed skills directories."""
    items, error = _run_gh_directory_listing(owner, repo, "skills")
    if error:
        return [], [f"目录 skills 抓取失败: {error}"]

    samples: list[dict] = []
    errors: list[str] = []
    seen_paths: set[str] = set()
    items = sorted(
        items,
        key=lambda item: (
            SKILL_BUCKET_PRIORITY.get(item.get("name", ""), 10),
            item.get("name", ""),
        ),
    )

    for item in items:
        if len(samples) >= limit:
            break
        if item.get("type") != "dir":
            continue

        base_path = item.get("path", "")
        direct_path = f"{base_path}/SKILL.md"
        direct_sample = _fetch_repo_file(owner, repo, direct_path)
        if direct_sample:
            _append_unique_file({"skill_samples": samples}, "skill_samples", direct_sample, seen_paths)
            continue

        nested_items, nested_error = _run_gh_directory_listing(owner, repo, base_path)
        if nested_error:
            if not _is_not_found_error(nested_error):
                errors.append(f"目录 {base_path} 抓取失败: {nested_error}")
            continue

        for nested_item in nested_items:
            if len(samples) >= limit:
                break
            if nested_item.get("type") != "dir":
                continue
            nested_path = f"{nested_item.get('path', '')}/SKILL.md"
            nested_sample = _fetch_repo_file(owner, repo, nested_path)
            if nested_sample:
                _append_unique_file({"skill_samples": samples}, "skill_samples", nested_sample, seen_paths)
                break

    return samples, errors


def _build_harvest_payload(
    *,
    project: str = "",
    repo_name: str = "",
    url: str = "",
    readme: dict | None = None,
    structure: dict | None = None,
    code_files: dict | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    issues: list[dict] | None = None,
    status: str = "ok",
) -> dict:
    return {
        "status": status,
        "errors": errors or [],
        "warnings": warnings or [],
        "issues": issues or [],
        "meta": {
            "project": project,
            "repo_name": repo_name,
            "url": url,
        },
        "project": project,
        "repo_name": repo_name,
        "url": url,
        "readme": readme or {},
        "structure": structure or {},
        "code_files": code_files or {},
    }


def _make_issue(
    *,
    stage: str,
    code: str,
    message: str,
    target: str = "",
    level: str = "warning",
) -> dict:
    return {
        "stage": stage,
        "code": code,
        "target": target,
        "level": level,
        "message": message,
    }


def _collect_top_level_issues(readme: dict, structure: dict, code_files: dict) -> list[dict]:
    issues: list[dict] = []
    if not readme.get("raw"):
        issues.append(
            _make_issue(
                stage="readme",
                code="readme_missing",
                message="README 未抓到，背景信息不足。",
                target=readme.get("url", ""),
            )
        )

    issues.extend(structure.get("issues", []))
    issues.extend(code_files.get("issues", []))
    return issues


def harvest_repo(repo_url: str, repo_name: str = "") -> dict:
    """
    抓取仓库内容

    Args:
        repo_url: GitHub 仓库 URL
        repo_name: 仓库名称（可选）

    Returns:
        {
            "project": "owner/repo",
            "readme": {...},
            "structure": {...},
            "code_files": {...}
        }
    """
    print(f"[Stage 4] 抓取: {repo_url}")

    normalized_url = normalize_github_repo_url(repo_url)
    if not normalized_url:
        return _build_harvest_payload(
            url=repo_url,
            status="invalid-input",
            errors=["Invalid repo URL. Expected https://github.com/<owner>/<repo>"],
        )

    ready, message = check_gh_cli_ready()
    if not ready:
        return _build_harvest_payload(
            url=normalized_url,
            status="blocked",
            errors=[message],
        )

    from urllib.parse import urlparse
    parts = urlparse(normalized_url).path.strip("/").split("/")
    if len(parts) < 2:
        return _build_harvest_payload(
            url=normalized_url,
            status="invalid-input",
            errors=["Invalid repo URL"],
        )

    owner, repo = parts[0], parts[1]
    repo = repo.replace(".git", "")
    project = f"{owner}/{repo}"

    if not repo_name:
        repo_name = project

    warnings: list[str] = []

    # 1. 抓取 README
    print(f"[Stage 4] 抓取 README...")
    readme_data = fetch_readme(normalized_url)
    readme = {
        "raw": readme_data.get("raw", ""),
        "filename": readme_data.get("filename", ""),
        "url": readme_data.get("url", ""),
    }
    if not readme["raw"]:
        warnings.append("README 未抓到，后续评估只能更多依赖目录和代码文件。")

    # 2. 抓取目录结构
    print(f"[Stage 4] 抓取目录结构...")
    time.sleep(REQUEST_DELAY)
    structure = fetch_repo_structure(owner, repo)
    if structure.get("error"):
        warnings.append(f"目录结构抓取失败：{structure['error']}")

    # 3. 抓取核心代码文件
    print(f"[Stage 4] 抓取核心代码文件...")
    code_files = fetch_key_files(owner, repo, structure)
    if code_files.get("error"):
        warnings.append(f"核心代码抓取失败：{code_files['error']}")
    elif not code_files.get("files"):
        warnings.append("未抓到核心代码文件，分析时需降低确定性。")

    issues = _collect_top_level_issues(readme, structure, code_files)

    status = "ok"
    if structure.get("error") or code_files.get("error"):
        status = "partial"
    elif not readme["raw"] and not code_files.get("files"):
        status = "partial"

    result = _build_harvest_payload(
        project=project,
        repo_name=repo_name,
        url=normalized_url,
        readme=readme,
        structure=structure,
        code_files=code_files,
        warnings=warnings,
        issues=issues,
        status=status,
    )

    # 保存结果
    safe_name = repo_name.replace("/", "_").replace(" ", "_")
    output_file = os.path.join(OUTPUT_DIR, f"harvest_{safe_name}.json")
    save_json(result, output_file)

    print(f"[Stage 4] 完成，保存到 {output_file}")
    return result


def fetch_repo_structure(owner: str, repo: str) -> dict:
    """
    使用 gh api 获取仓库目录结构
    """
    api_path = f"repos/{owner}/{repo}/contents/"
    try:
        result = subprocess.run(
            ["gh", "api", api_path, "--jq", ".[] | {name, type}"],
            capture_output=True, text=True, timeout=15
        )
        result.check_returncode()

        root_files = []
        directories = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            item = json.loads(line)
            name = item.get("name", "")
            if item.get("type") == "dir":
                directories.append(name)
            else:
                root_files.append(name)

        return {
            "root_files": root_files,
            "directories": directories,
            "issues": [],
        }
    except FileNotFoundError:
        print("[Warn] 获取目录结构失败: gh CLI 不可用")
        return {
            "root_files": [],
            "directories": [],
            "error": "gh CLI 不可用",
            "issues": [
                _make_issue(
                    stage="structure",
                    code="gh_cli_unavailable",
                    target="/",
                    message="获取仓库目录结构失败：gh CLI 不可用。",
                )
            ],
        }
    except Exception as e:
        print(f"[Warn] 获取目录结构失败: {e}")
        return {
            "root_files": [],
            "directories": [],
            "error": str(e),
            "issues": [
                _make_issue(
                    stage="structure",
                    code="structure_fetch_failed",
                    target="/",
                    message=f"获取仓库目录结构失败：{e}",
                )
            ],
        }


def fetch_key_files(owner: str, repo: str, structure: dict) -> dict:
    """
    根据目录结构，抓取核心代码文件

    优先级：
    1. 入口文件（package.json, setup.py, pyproject.toml 等）
    2. 核心目录下的代码文件（src/, lib/, core/ 等）
    3. 配置文件（.github/workflows/ 等）
    """
    # 常见入口文件
    entry_files = [
        "package.json", "setup.py", "pyproject.toml", "Cargo.toml",
        "go.mod", "Makefile", "CMakeLists.txt", "build.gradle",
        "pom.xml", "requirements.txt", "Pipfile", "yarn.lock",
        "Cargo.lock", "go.sum",
    ]
    entry_file_names = {name.lower() for name in entry_files}

    # 需要抓取的目录
    key_dirs = ["src", "lib", "core", "cmd", "internal", "pkg", "modules", "scripts", "tests"]
    root_reference_files = ["AGENTS.md", "CLAUDE.md", "GEMINI.md", "gemini-extension.json"]
    plugin_manifest_paths = [
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        ".cursor-plugin/plugin.json",
        ".opencode/INSTALL.md",
    ]

    fetched = {
        "entries": [],
        "configs": [],
        "source": [],
        "skill_samples": [],
    }
    errors = []
    issues: list[dict] = []
    seen_paths: set[str] = set()

    # 1. 抓取入口文件
    root_files = structure.get("root_files", [])
    for f in root_files:
        if f.lower() in entry_file_names:
            file_data = _fetch_repo_file(owner, repo, f)
            if file_data:
                file_data["content"] = file_data["content"][:5000]
            _append_unique_file(fetched, "entries", file_data, seen_paths)

    for f in root_reference_files:
        if f in root_files:
            _append_unique_file(fetched, "configs", _fetch_repo_file(owner, repo, f), seen_paths)

    for path in plugin_manifest_paths:
        top_dir = path.split("/", 1)[0]
        if top_dir in structure.get("directories", []):
            _append_unique_file(fetched, "configs", _fetch_repo_file(owner, repo, path), seen_paths)

    directories = structure.get("directories", [])
    # 2. 先抓 skills 样本，让技能框架类仓库不会被脚本/配置文件挤掉
    if "skills" in directories:
        skill_samples, skill_errors = _select_skill_samples(owner, repo)
        errors.extend(skill_errors)
        issues.extend(
            _make_issue(
                stage="code_files",
                code="directory_listing_failed",
                target=error_text.split("目录 ", 1)[1].split(" 抓取失败", 1)[0]
                if error_text.startswith("目录 ")
                else "skills",
                message=error_text,
            )
            for error_text in skill_errors
        )
        for file_data in skill_samples:
            _append_unique_file(fetched, "skill_samples", file_data, seen_paths)

    # 3. 抓取核心目录下的代表文件（必要时下钻一层）
    for d in directories:
        if d in {"skills", "docs"}:
            continue

        if d in key_dirs:
            time.sleep(REQUEST_DELAY)
            files, file_errors = _select_representative_files(
                owner,
                repo,
                d,
                limit=2,
                mode="source",
            )
            errors.extend(file_errors)
            issues.extend(
                _make_issue(
                    stage="code_files",
                    code="directory_listing_failed",
                    target=error_text.split("目录 ", 1)[1].split(" 抓取失败", 1)[0]
                    if error_text.startswith("目录 ")
                    else d,
                    message=error_text,
                )
                for error_text in file_errors
            )
            for file_data in files:
                _append_unique_file(fetched, "source", file_data, seen_paths)

    if "docs" in directories:
        files, file_errors = _select_representative_files(
            owner,
            repo,
            "docs",
            limit=2,
            mode="docs",
        )
        errors.extend(file_errors)
        issues.extend(
            _make_issue(
                stage="code_files",
                code="directory_listing_failed",
                target=error_text.split("目录 ", 1)[1].split(" 抓取失败", 1)[0]
                if error_text.startswith("目录 ")
                else "docs",
                message=error_text,
            )
            for error_text in file_errors
        )
        for file_data in files:
            _append_unique_file(fetched, "configs", file_data, seen_paths)

    # 4. 抓取 workflow 文件
    if ".github" in directories:
        time.sleep(REQUEST_DELAY)
        items, error = _run_gh_directory_listing(owner, repo, ".github/workflows")
        if error and not _is_not_found_error(error):
            errors.append(f".github/workflows 抓取失败: {error}")
            issues.append(
                _make_issue(
                    stage="code_files",
                    code="directory_listing_failed",
                    target=".github/workflows",
                    message=f".github/workflows 抓取失败：{error}",
                )
            )
        else:
            for item in items[:3]:
                if item.get("type") != "file":
                    continue
                _append_unique_file(fetched, "configs", _fetch_repo_file(owner, repo, item.get("path", "")), seen_paths)

    # 限制总数，同时给 source 留出保底样本位，避免被根目录配置文件全部挤掉
    selected = []
    selected.extend(fetched["entries"][:4])
    selected.extend(fetched["configs"][:3])
    selected.extend(fetched["skill_samples"][:3])
    selected.extend(fetched["source"][:2])

    remaining = MAX_FILES_TO_FETCH - len(selected)
    if remaining > 0:
        extras = (
            fetched["entries"][4:]
            + fetched["configs"][3:]
            + fetched["skill_samples"][3:]
            + fetched["source"][2:]
        )
        selected.extend(extras[:remaining])

    all_files = selected[:MAX_FILES_TO_FETCH]

    if not fetched["entries"]:
        issues.append(
            _make_issue(
                stage="code_files",
                code="entry_files_missing",
                target="/",
                message="没有抓到典型入口文件，技术栈判断会更依赖 README 和目录结构。",
            )
        )
    if not fetched["source"]:
        issues.append(
            _make_issue(
                stage="code_files",
                code="source_samples_missing",
                target="source",
                message="没有抓到实现层源码样本，分析容易停留在配置和说明层。",
            )
        )
    if "skills" in directories and not fetched["skill_samples"]:
        issues.append(
            _make_issue(
                stage="code_files",
                code="skill_samples_missing",
                target="skills",
                message="仓库含 skills 目录，但没有抓到技能样本文件。",
            )
        )

    payload = {
        "total": len(all_files),
        "files": all_files,
        "skill_samples": fetched["skill_samples"],
        "issues": issues,
        "coverage": {
            "entries": len(fetched["entries"]),
            "configs": len(fetched["configs"]),
            "source": len(fetched["source"]),
            "skill_samples": len(fetched["skill_samples"]),
        },
    }
    if errors:
        payload["error"] = "; ".join(errors[:3])
    return payload


def format_harvest_output(result: dict) -> str:
    """格式化输出"""
    if result.get("error"):
        return f"抓取失败：{result['error']}"

    lines = [f"**抓取完成：{result.get('project', '')}**\n"]

    # README
    readme = result.get("readme", {})
    if readme.get("raw"):
        lines.append(f"README：{readme.get('filename', 'README.md')}（{len(readme['raw'])} 字符）")
    else:
        lines.append("README：未找到")

    # 目录结构
    structure = result.get("structure", {})
    dirs = structure.get("directories", [])
    root_files = structure.get("root_files", [])
    lines.append(f"\n目录结构：")
    lines.append(f"  根目录文件：{', '.join(root_files[:10])}")
    lines.append(f"  子目录：{', '.join(dirs[:10])}")

    # 代码文件
    code_files = result.get("code_files", {})
    files = code_files.get("files", [])
    lines.append(f"\n抓取文件数：{len(files)}")
    warnings = result.get("warnings", [])
    if warnings:
        lines.append("\n警告：")
        for warning in warnings:
            lines.append(f"  - {warning}")
    issues = result.get("issues", [])
    if issues:
        lines.append("\n结构化告警：")
        for issue in issues[:5]:
            target = f" ({issue.get('target')})" if issue.get("target") else ""
            lines.append(f"  - [{issue.get('code', 'issue')}] {issue.get('message', '')}{target}")
    for f in files[:5]:
        lines.append(f"  - {f.get('name', '')}")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = harvest_repo(url)
        print(format_harvest_output(result))
    else:
        print("用法: python harvest.py <github-url>")
