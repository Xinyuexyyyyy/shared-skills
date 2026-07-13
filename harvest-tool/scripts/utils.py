"""
Harvest Tool - 公共工具函数
"""

import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
import os
import sys
import json
import re
from urllib.parse import urlparse
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from configs.settings import (
    MAX_FILE_SIZE,
    REQUEST_DELAY,
)


def fetch_url(url: str, timeout: int = 10) -> Optional[str]:
    """
    获取 URL 内容，支持 GitHub raw / API
    使用 urllib，不依赖 requests
    """
    time.sleep(REQUEST_DELAY)

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Harvest-Tool)"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            if len(data) > MAX_FILE_SIZE:
                return None
            # 尝试检测编码
            charset = resp.headers.get_content_charset()
            if charset:
                return data.decode(charset)
            return data.decode("utf-8", errors="replace")
    except Exception:
        return None


def fetch_readme(repo_url: str) -> dict:
    """
    获取仓库的 README 内容
    repo_url: https://github.com/owner/repo
    """
    parts = urlparse(repo_url).path.strip("/").split("/")
    if len(parts) < 2:
        return {"raw": "", "url": ""}

    owner, repo = parts[0], parts[1]
    repo = repo.replace(".git", "")

    # 尝试常见 README 文件名
    for filename in ["README.md", "README", "README.txt"]:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{filename}"
        content = fetch_url(raw_url)
        if content:
            return {"raw": content, "url": raw_url, "filename": filename}

    return {"raw": "", "url": ""}


def fetch_file_content(file_url: str) -> Optional[str]:
    """
    获取单个文件内容
    """
    return fetch_url(file_url)


def save_json(data: dict, filepath: str):
    """保存 JSON 到文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: str) -> dict:
    """从文件加载 JSON"""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def normalize_github_repo_url(repo_url: str) -> Optional[str]:
    """规范化 GitHub 仓库 URL，仅接受 owner/repo 级别链接。"""
    raw = (repo_url or "").strip()
    if not raw:
        return None

    if raw.startswith("git@github.com:"):
        raw = raw.replace("git@github.com:", "https://github.com/", 1)

    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw

    parsed = urlparse(raw)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return None

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return None

    owner = parts[0].strip()
    repo = parts[1].strip()
    if repo.endswith(".git"):
        repo = repo[:-4]

    pattern = re.compile(r"^[A-Za-z0-9._-]+$")
    if not owner or not repo or not pattern.match(owner) or not pattern.match(repo):
        return None

    return f"https://github.com/{owner}/{repo}"


def check_gh_cli_ready() -> tuple[bool, str]:
    """检查 gh CLI 是否存在且已登录。"""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return False, "gh CLI 未安装或不可用"
    except Exception as exc:
        return False, f"gh CLI 检查失败: {exc}"

    if result.returncode == 0:
        return True, ""

    detail = (result.stderr or result.stdout or "").strip() or "未知错误"
    lowered = detail.lower()
    if "not logged into" in lowered or "authentication failed" in lowered:
        return False, "gh CLI 未登录，请先运行 `gh auth status` 或 `gh auth login`"
    return False, f"gh CLI 不可用: {detail}"
