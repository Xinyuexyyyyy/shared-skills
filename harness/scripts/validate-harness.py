#!/usr/bin/env python3
"""Validate a harness library or a workspace consuming one.

The validator intentionally checks the small manifest subset defined by
MANIFEST-SPEC.md instead of trusting directory names alone.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment-specific
    raise SystemExit("PyYAML is required to validate harness manifests") from exc


class ValidationError(Exception):
    pass


ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
WORKFLOW_STAGES = [
    "input-hygiene",
    "digest",
    "broad-route",
    "theme-adapter",
    "artifact-gate",
    "execution",
    "verification",
    "output-control",
    "closeout",
    "inspiration-manual-only",
]


def fail(message: str) -> None:
    raise ValidationError(message)


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"cannot read manifest {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"manifest must be a mapping: {path}")
    return data


def require(mapping: dict[str, Any], key: str, path: Path) -> Any:
    if key not in mapping:
        fail(f"missing {key}: {path}")
    return mapping[key]


def require_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        fail(f"invalid {label}: {value!r}")
    return value


def require_version(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SEMVER_PATTERN.fullmatch(value):
        fail(f"invalid semantic version for {label}: {value!r}")
    return value


def relative_path(value: Any, base: Path, boundary: Path, label: str) -> Path:
    if not isinstance(value, str) or not value:
        fail(f"invalid path value for {label}: {value!r}")
    if value.startswith("~") or value.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", value):
        fail(f"absolute path is not portable for {label}: {value}")
    resolved = (base / value).resolve()
    boundary = boundary.resolve()
    try:
        resolved.relative_to(boundary)
    except ValueError:
        fail(f"path escapes boundary for {label}: {value}")
    return resolved


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        fail(f"missing file for {label}: {path}")


def load_skill_name(path: Path) -> str:
    require_file(path, "skill")
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        fail(f"skill frontmatter is missing: {path}")
    frontmatter = text[4:].split("\n---\n", 1)[0]
    try:
        data = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:
        fail(f"invalid skill frontmatter {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"skill frontmatter must be a mapping: {path}")
    return require_id(require(data, "name", path), "skill id")


def scan_portability(paths: list[Path]) -> None:
    forbidden_names = ("open" + "claw", "hu" + "b", "user" + "ysys")
    absolute_path = re.compile(
        r"(?<![A-Za-z0-9._-])/(?!/)[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*"
        r"|[A-Za-z]:[\\/]"
        r"|\\\\[^\\\s]+\\"
    )
    forbidden_runtime = re.compile(r"\b(?:" + "|".join(forbidden_names) + r")\b", re.IGNORECASE)
    credential_words = ("pass" + "word", "to" + "ken", "se" + "cret", "api" + "[_-]?key")
    credential_assignment = re.compile(
        r"\b(?:" + "|".join(credential_words) + r")\b\s*[:=]\s*[\"']?"
        r"(?!<redacted>|example|null|none)[^\s\"']+",
        re.IGNORECASE,
    )
    https_url = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
    for path in paths:
        text = path.read_text(encoding="utf-8")
        portability_text = https_url.sub("", text)
        if absolute_path.search(portability_text):
            fail(f"absolute path found in published content: {path}")
        if forbidden_runtime.search(text):
            fail(f"forbidden runtime or device reference: {path}")
        if credential_assignment.search(text):
            fail(f"possible credential assignment in published content: {path}")


def validate_bundle(bundle_dir: Path, expected_id: str | None = None, expected_version: str | None = None) -> dict[str, Any]:
    manifest_path = bundle_dir / "manifest.yaml"
    manifest = load_manifest(manifest_path)
    if require(manifest, "schema_version", manifest_path) != "1":
        fail(f"unsupported schema_version: {manifest_path}")
    if require(manifest, "kind", manifest_path) != "bundle":
        fail(f"manifest kind is not bundle: {manifest_path}")
    bundle_id = require_id(require(manifest, "id", manifest_path), "bundle id")
    version = require_version(require(manifest, "version", manifest_path), "bundle")
    status = require(manifest, "status", manifest_path)
    if status not in {"draft", "stable", "deprecated"}:
        fail(f"invalid bundle status: {status!r}")
    if expected_id is not None and bundle_id != expected_id:
        fail(f"bundle id mismatch: expected {expected_id}, got {bundle_id}")
    if expected_version is not None and version != expected_version:
        fail(f"bundle version mismatch: expected {expected_version}, got {version}")
    runtime = require(manifest, "runtime", manifest_path)
    if runtime not in {"neutral", "codex", "claude"}:
        fail(f"invalid bundle runtime: {runtime!r}")
    entrypoint = relative_path(require(manifest, "entrypoint", manifest_path), bundle_dir, bundle_dir, "bundle entrypoint")
    require_file(entrypoint, "bundle entrypoint")

    files = require(manifest, "files", manifest_path)
    if not isinstance(files, list) or not files:
        fail(f"bundle files must be a non-empty list: {manifest_path}")
    declared = {"manifest.yaml"}
    for item in files:
        if not isinstance(item, dict):
            fail(f"bundle file entry must be a mapping: {manifest_path}")
        value = require(item, "path", manifest_path)
        resolved = relative_path(value, bundle_dir, bundle_dir, "bundle file")
        require_file(resolved, "bundle file")
        normalized_value = Path(value).as_posix()
        if normalized_value in declared:
            fail(f"duplicate bundle file: {value}")
        checksum = require(item, "sha256", manifest_path)
        if not isinstance(checksum, str) or not SHA256_PATTERN.fullmatch(checksum):
            fail(f"invalid sha256 for bundle file {value}: {checksum!r}")
        actual_checksum = hashlib.sha256(resolved.read_bytes()).hexdigest()
        if checksum != actual_checksum:
            fail(f"sha256 mismatch for bundle file: {value}")
        declared.add(normalized_value)

    workflow = manifest.get("workflow")
    if workflow is not None:
        if not isinstance(workflow, dict):
            fail(f"workflow must be a mapping: {manifest_path}")
        require_id(require(workflow, "id", manifest_path), "workflow id")
        require_version(require(workflow, "version", manifest_path), "workflow")
        if require(workflow, "stages", manifest_path) != WORKFLOW_STAGES:
            fail(f"workflow stages or order do not match the contract: {manifest_path}")

    runtime_adapters = manifest.get("runtime_adapters")
    if runtime_adapters is not None:
        if not isinstance(runtime_adapters, dict) or set(runtime_adapters) != {"codex", "claude"}:
            fail(f"bundle runtime_adapters must declare codex and claude: {manifest_path}")
        for runtime_name, adapter_value in runtime_adapters.items():
            adapter = relative_path(adapter_value, bundle_dir, bundle_dir, f"{runtime_name} bundle adapter")
            require_file(adapter, f"{runtime_name} bundle adapter")
            if Path(str(adapter_value)).as_posix() not in declared:
                fail(f"bundle adapter is not declared in files: {adapter_value}")

    actual = {
        path.relative_to(bundle_dir).as_posix()
        for path in bundle_dir.rglob("*")
        if path.is_file()
    }
    undeclared = sorted(actual - declared)
    if undeclared:
        fail(f"undeclared bundle files: {', '.join(undeclared)}")
    for path in bundle_dir.rglob("*"):
        if path.is_symlink():
            try:
                path.resolve().relative_to(bundle_dir.resolve())
            except ValueError:
                fail(f"bundle symlink escapes bundle: {path}")
    return manifest


def validate_assembly(root: Path, assembly_path: Path) -> None:
    assembly = load_manifest(assembly_path)
    if require(assembly, "schema_version", assembly_path) != "1":
        fail(f"unsupported assembly schema_version: {assembly_path}")
    if require(assembly, "kind", assembly_path) != "bundle-source":
        fail(f"assembly kind is not bundle-source: {assembly_path}")
    bundle_id = require_id(require(assembly, "id", assembly_path), "assembly id")
    bundle_version = require_version(require(assembly, "version", assembly_path), "assembly")
    bundle_dir = root / "bundles" / bundle_id
    manifest = validate_bundle(bundle_dir, bundle_id, bundle_version)
    entries = require(assembly, "files", assembly_path)
    if not isinstance(entries, list) or not entries:
        fail(f"assembly files must be a non-empty list: {assembly_path}")
    manifest_entries = {item["path"]: item for item in manifest["files"]}
    assembly_targets: set[str] = set()
    for item in entries:
        if not isinstance(item, dict):
            fail(f"assembly file entry must be a mapping: {assembly_path}")
        source_value = require(item, "source", assembly_path)
        target_value = require(item, "path", assembly_path)
        normalized_target = Path(str(target_value)).as_posix()
        if normalized_target in assembly_targets:
            fail(f"duplicate assembly target: {target_value}")
        assembly_targets.add(normalized_target)
        source = relative_path(source_value, root, root, "component source")
        target = relative_path(target_value, bundle_dir, bundle_dir, "assembled bundle file")
        require_file(source, "component source")
        require_file(target, "assembled bundle file")
        if source.read_bytes() != target.read_bytes():
            fail(f"assembled bundle file is stale: {target_value}")
        manifest_item = manifest_entries.get(normalized_target)
        if manifest_item is None:
            fail(f"assembled bundle file is missing from manifest: {target_value}")
        if manifest_item.get("role") != item.get("role"):
            fail(f"assembled bundle role mismatch: {target_value}")
        if manifest_item.get("component_id") != item.get("component_id"):
            fail(f"assembled bundle component mismatch: {target_value}")
    if assembly_targets != set(manifest_entries):
        fail(f"assembly and bundle file sets differ: {assembly_path}")


def validate_workspace(workspace: Path, library_root: Path) -> None:
    harness = workspace / "harness"
    manifest_path = harness / "manifest.yaml"
    manifest = load_manifest(manifest_path)
    if require(manifest, "schema_version", manifest_path) != "1":
        fail(f"unsupported schema_version: {manifest_path}")
    if require(manifest, "kind", manifest_path) != "workspace":
        fail(f"manifest kind is not workspace: {manifest_path}")
    require_id(require(manifest, "id", manifest_path), "workspace id")
    require_version(require(manifest, "version", manifest_path), "workspace")
    harness_entrypoint_value = require(manifest, "harness_entrypoint", manifest_path)
    entrypoint = relative_path(harness_entrypoint_value, harness, harness, "workspace harness entrypoint")
    require_file(entrypoint, "workspace harness entrypoint")

    declared_harness_files = {
        "manifest.yaml",
        entrypoint.relative_to(harness.resolve()).as_posix(),
    }

    entrypoints = require(manifest, "entrypoints", manifest_path)
    if not isinstance(entrypoints, list) or not entrypoints:
        fail(f"workspace entrypoints must be a non-empty list: {manifest_path}")
    runtime_entry_paths: list[Path] = []
    for item in entrypoints:
        runtime_entry = relative_path(item, harness, workspace, "workspace runtime entrypoint")
        require_file(runtime_entry, "workspace runtime entrypoint")
        expected_pointer = f"harness/{Path(str(harness_entrypoint_value)).as_posix()}"
        if expected_pointer not in runtime_entry.read_text(encoding="utf-8"):
            fail(f"runtime entrypoint does not point to {expected_pointer}: {runtime_entry}")
        runtime_entry_paths.append(runtime_entry)
    expected_runtime_entries = {
        (workspace / "AGENTS.md").resolve(),
        (workspace / ".claude" / "CLAUDE.md").resolve(),
    }
    if len(runtime_entry_paths) != 2 or set(runtime_entry_paths) != expected_runtime_entries:
        fail("workspace entrypoints must declare AGENTS.md and .claude/CLAUDE.md exactly")

    bundles = require(manifest, "bundles", manifest_path)
    if not isinstance(bundles, list) or not bundles:
        fail(f"workspace bundles must be a non-empty list: {manifest_path}")
    declared_bundle_ids: set[str] = set()
    for item in bundles:
        if not isinstance(item, dict):
            fail(f"workspace bundle entry must be a mapping: {manifest_path}")
        bundle_id = require_id(require(item, "id", manifest_path), "workspace bundle id")
        if bundle_id in declared_bundle_ids:
            fail(f"duplicate workspace bundle id: {bundle_id}")
        declared_bundle_ids.add(bundle_id)
        bundle_version = require_version(require(item, "version", manifest_path), "workspace bundle")
        bundle_path = relative_path(require(item, "path", manifest_path), harness, harness, "workspace bundle")
        validate_bundle(bundle_path, bundle_id, bundle_version)
        canonical_bundle = library_root / "bundles" / bundle_id
        if not canonical_bundle.is_dir():
            fail(f"canonical bundle is missing: {canonical_bundle}")
        compare_tree(canonical_bundle, bundle_path)
        declared_harness_files.update(
            path.relative_to(harness.resolve()).as_posix()
            for path in bundle_path.rglob("*")
            if path.is_file()
        )

    skills = require(manifest, "skills", manifest_path)
    if not isinstance(skills, list) or not skills:
        fail(f"workspace skills must be a non-empty list: {manifest_path}")
    canonical_skills: dict[str, Path] = {}
    for item in skills:
        if not isinstance(item, dict):
            fail(f"workspace skill entry must be a mapping: {manifest_path}")
        skill_id = require_id(require(item, "id", manifest_path), "workspace skill id")
        if skill_id in canonical_skills:
            fail(f"duplicate workspace skill id: {skill_id}")
        skill_path = relative_path(require(item, "path", manifest_path), harness, harness, "workspace skill")
        if load_skill_name(skill_path) != skill_id:
            fail(f"workspace skill id does not match frontmatter: {skill_path}")
        canonical_skills[skill_id] = skill_path
        declared_harness_files.add(skill_path.relative_to(harness.resolve()).as_posix())

    adapters = require(manifest, "runtime_adapters", manifest_path)
    if not isinstance(adapters, dict) or set(adapters) != {"codex", "claude"}:
        fail(f"runtime_adapters must declare codex and claude: {manifest_path}")
    adapter_paths: list[Path] = []
    adapter_skill_ids: dict[str, set[str]] = {}
    for name, values in adapters.items():
        if not isinstance(values, list) or not values:
            fail(f"{name} runtime adapters must be a non-empty list: {manifest_path}")
        expected_parts = (".agents", "skills") if name == "codex" else (".claude", "skills")
        adapter_skill_ids[name] = set()
        for value in values:
            adapter_path = relative_path(value, harness, workspace, f"{name} adapter")
            require_file(adapter_path, f"{name} adapter")
            relative_adapter = adapter_path.relative_to(workspace.resolve())
            if relative_adapter.parts[:2] != expected_parts:
                fail(f"{name} adapter is in the wrong runtime directory: {adapter_path}")
            adapter_skill_id = load_skill_name(adapter_path)
            if adapter_skill_id in adapter_skill_ids[name]:
                fail(f"duplicate {name} adapter for skill {adapter_skill_id}")
            adapter_skill_ids[name].add(adapter_skill_id)
            canonical_skill = canonical_skills.get(adapter_skill_id)
            if canonical_skill is None:
                fail(f"adapter skill is not declared by workspace manifest: {adapter_path}")
            expected_reference = Path(os.path.relpath(canonical_skill, adapter_path.parent)).as_posix()
            if expected_reference not in adapter_path.read_text(encoding="utf-8"):
                fail(f"runtime adapter does not point to canonical skill: {adapter_path}")
            adapter_paths.append(adapter_path)
    expected_skill_ids = set(canonical_skills)
    for name, skill_ids in adapter_skill_ids.items():
        if skill_ids != expected_skill_ids:
            fail(f"{name} adapters do not cover every declared skill")

    private_state = require(manifest, "private_state", manifest_path)
    if not isinstance(private_state, dict):
        fail(f"private_state must be a mapping: {manifest_path}")
    excluded = require(private_state, "excluded_paths", manifest_path)
    if not isinstance(excluded, list) or not excluded:
        fail(f"private_state.excluded_paths must be a non-empty list: {manifest_path}")
    for value in excluded:
        excluded_path = relative_path(value, harness, workspace, "private state")
        if excluded_path == workspace.resolve():
            fail(f"private state cannot exclude the whole workspace: {value}")
        if excluded_path == harness.resolve() or harness.resolve() in excluded_path.parents:
            fail(f"private state must not be inside harness: {value}")

    for path in (workspace / "harness").rglob("*"):
        if path.is_symlink() and not path.resolve().is_relative_to(harness.resolve()):
            fail(f"harness symlink escapes workspace: {path}")

    actual_harness_files = {
        path.relative_to(harness.resolve()).as_posix()
        for path in harness.rglob("*")
        if path.is_file()
    }
    undeclared = sorted(actual_harness_files - declared_harness_files)
    if undeclared:
        fail(f"undeclared workspace harness files: {', '.join(undeclared)}")
    scan_portability(
        [path for path in harness.rglob("*") if path.is_file()]
        + runtime_entry_paths
        + adapter_paths
    )


def compare_tree(left: Path, right: Path) -> None:
    left_files = {path.relative_to(left).as_posix() for path in left.rglob("*") if path.is_file()}
    right_files = {path.relative_to(right).as_posix() for path in right.rglob("*") if path.is_file()}
    if left_files != right_files:
        fail(f"bundle file sets differ: {left} vs {right}")
    for relative in left_files:
        if (left / relative).read_bytes() != (right / relative).read_bytes():
            fail(f"bundle file differs: {relative}")


def validate_library(root: Path) -> None:
    required = [root / name for name in ("README.md", "METHODOLOGY.md", "MANIFEST-SPEC.md")]
    for path in required:
        require_file(path, "harness library file")
    bundle_dirs = sorted(path for path in (root / "bundles").iterdir() if path.is_dir())
    if not bundle_dirs:
        fail("harness library has no bundles")
    for bundle in bundle_dirs:
        validate_bundle(bundle)
    assembly_paths = sorted((root / "assemblies").glob("*.yaml"))
    if not assembly_paths:
        fail("harness library has no bundle assemblies")
    for assembly_path in assembly_paths:
        validate_assembly(root, assembly_path)
    example = root / "examples" / "livewithopencove-workspace"
    validate_workspace(example, root)
    if not (example / "harness" / "HARNESS.md").is_file():
        fail("example harness entrypoint is missing")
    portability_files = [root / "README.md", root / "METHODOLOGY.md", root / "MANIFEST-SPEC.md"]
    portability_files.extend(
        path
        for base in (root / "assemblies", root / "components", root / "bundles", root / "examples")
        for path in base.rglob("*")
        if path.is_file()
    )
    scan_portability(portability_files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--workspace", type=Path, action="append")
    args = parser.parse_args()
    try:
        root = args.library_root.resolve()
        validate_library(root)
        for workspace in args.workspace or []:
            validate_workspace(workspace.resolve(), root)
    except ValidationError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    print("harness validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
