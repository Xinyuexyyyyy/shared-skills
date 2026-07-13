from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


VERSION_TOKEN_RE = re.compile(r"(?i)(?:^|[-_.\s])v(?:er(?:sion)?)?[-_.\s]?\d{1,4}(?=$|[-_.\s])")


def version_token_count(path: Path) -> int:
    return len(VERSION_TOKEN_RE.findall(path.stem))


def files_with_multiple_versions(paths: Iterable[Path]) -> list[Path]:
    return [path for path in paths if version_token_count(path) > 1]


def enforce_single_version_names(paths: Iterable[Path]) -> None:
    bad = files_with_multiple_versions(paths)
    if not bad:
        return
    names = ", ".join(path.name for path in bad)
    raise ValueError(
        "Versioned output filenames must contain only one version token. "
        f"Move cross-version notes into manifest/content instead of filenames: {names}"
    )


def archive_directory(directory: Path) -> str:
    archiver = Path("/Users/sure/Daily Work/scripts/archive_old_versions.py")
    if not archiver.exists() or not directory.exists() or not directory.is_dir():
        return ""
    result = subprocess.run(
        [sys.executable, str(archiver), str(directory)],
        text=True,
        capture_output=True,
        check=False,
    )
    return (result.stdout + result.stderr).strip()


def archive_artifact_dirs(paths: Iterable[Path]) -> list[str]:
    seen: set[Path] = set()
    logs: list[str] = []
    for path in paths:
        directory = path if path.is_dir() else path.parent
        directory = directory.resolve()
        if directory in seen:
            continue
        seen.add(directory)
        output = archive_directory(directory)
        if output:
            logs.append(f"{directory}\n{output}")
    return logs
