#!/usr/bin/env python3
"""Build a portable harness bundle from canonical component sources."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


def fail(message: str) -> None:
    raise SystemExit(message)


def load_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail(f"assembly must be a mapping: {path}")
    return data


def within(path: Path, boundary: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(boundary.resolve())
    except ValueError:
        fail(f"{label} escapes harness root: {path}")
    return resolved


def render(assembly_path: Path, output: Path, root: Path) -> None:
    assembly = load_mapping(assembly_path)
    if assembly.get("schema_version") != "1" or assembly.get("kind") != "bundle-source":
        fail(f"unsupported assembly: {assembly_path}")
    file_entries = assembly.get("files")
    if not isinstance(file_entries, list) or not file_entries:
        fail(f"assembly files must be a non-empty list: {assembly_path}")

    output.mkdir(parents=True, exist_ok=True)
    manifest_files: list[dict[str, str]] = []
    target_paths: set[str] = set()
    for item in file_entries:
        if not isinstance(item, dict):
            fail(f"assembly file entry must be a mapping: {assembly_path}")
        source_value = item.get("source")
        target_value = item.get("path")
        if not isinstance(source_value, str) or not isinstance(target_value, str):
            fail(f"assembly source and path must be strings: {assembly_path}")
        normalized_target = Path(target_value).as_posix()
        if normalized_target in target_paths:
            fail(f"duplicate assembly target: {target_value}")
        target_paths.add(normalized_target)
        source = within(root / source_value, root, "source")
        target = within(output / target_value, output, "target")
        if not source.is_file():
            fail(f"missing component source: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        manifest_item = {
            "path": normalized_target,
            "role": str(item.get("role", "component")),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
        component_id = item.get("component_id")
        if component_id is not None:
            manifest_item["component_id"] = str(component_id)
        manifest_files.append(manifest_item)

    passthrough = (
        "id",
        "version",
        "status",
        "description",
        "runtime",
        "entrypoint",
        "workflow",
        "memory_policy",
        "input_capture",
        "runtime_adapters",
        "checks",
    )
    manifest: dict[str, Any] = {"schema_version": "1", "kind": "bundle"}
    for key in passthrough:
        if key in assembly:
            manifest[key] = assembly[key]
    manifest["files"] = manifest_files
    manifest["excludes"] = assembly.get("excludes", [])
    (output / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def same_tree(left: Path, right: Path) -> bool:
    left_files = {path.relative_to(left) for path in left.rglob("*") if path.is_file()}
    right_files = {path.relative_to(right) for path in right.rglob("*") if path.is_file()}
    return left_files == right_files and all(
        (left / relative).read_bytes() == (right / relative).read_bytes()
        for relative in left_files
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembly", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    assembly = within(args.assembly if args.assembly.is_absolute() else root / args.assembly, root, "assembly")
    output = within(args.output if args.output.is_absolute() else root / args.output, root, "output")
    assembly_data = load_mapping(assembly)
    bundle_id = assembly_data.get("id")
    output_relative = output.relative_to(root)
    if not isinstance(bundle_id, str) or output.name != bundle_id or "bundles" not in output_relative.parts:
        fail("output must be a bundles/<bundle-id> directory matching the assembly id")
    if args.check:
        with tempfile.TemporaryDirectory() as temporary:
            expected = Path(temporary) / "bundle"
            render(assembly, expected, root)
            if not output.is_dir() or not same_tree(expected, output):
                print(f"bundle is stale: {output}", file=sys.stderr)
                return 1
        print(f"bundle is current: {output}")
        return 0

    if output.exists():
        shutil.rmtree(output)
    render(assembly, output, root)
    print(f"materialized bundle: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
