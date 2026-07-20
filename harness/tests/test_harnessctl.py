"""Static governance regression tests for Harness v3."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


HARNESS = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


class HarnessCtlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="harness-v3-test-")
        self.root = Path(self.temporary.name) / "harness"
        shutil.copytree(HARNESS, self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(
            [PYTHON, "-B", str(self.root / "harnessctl"), "--root", str(self.root), *args],
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )

    def assert_failure(self, result: subprocess.CompletedProcess[str], fragment: str) -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(fragment, result.stderr)

    def manifest(self) -> tuple[Path, dict]:
        path = self.root / "bundles/core-workspace-v3/manifest.yaml"
        return path, yaml.safe_load(path.read_text(encoding="utf-8"))

    def write_manifest(self, path: Path, data: dict) -> None:
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def test_five_configs_and_schemas_validate(self) -> None:
        result = self.invoke("validate")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_required_config_fails(self) -> None:
        (self.root / "config/agent.yaml").unlink()
        self.assert_failure(self.invoke("validate"), "缺少规范配置")

    def test_missing_manifest_check_path_fails(self) -> None:
        path, manifest = self.manifest()
        manifest["checks"][0]["path"] = "checks/missing.py"
        self.write_manifest(path, manifest)
        self.assert_failure(self.invoke("validate"), "check 路径不存在")

    def test_bundle_and_library_only_checks_are_distinguished(self) -> None:
        _, manifest = self.manifest()
        self.assertEqual({item["scope"] for item in manifest["checks"]}, {"bundle", "library-only"})
        path, manifest = self.manifest()
        manifest["checks"][1]["scope"] = "invalid"
        self.write_manifest(path, manifest)
        self.assert_failure(self.invoke("validate"), "check scope 无效")

    def test_manifest_sha_mismatch_fails(self) -> None:
        target = self.root / "bundles/core-workspace-v3/config/agent.yaml"
        target.write_text(target.read_text(encoding="utf-8") + "\nchanged: true\n", encoding="utf-8")
        self.assert_failure(self.invoke("validate"), "SHA-256 不一致")

    def test_undeclared_bundle_file_fails(self) -> None:
        (self.root / "bundles/core-workspace-v3/undeclared.txt").write_text("x", encoding="utf-8")
        self.assert_failure(self.invoke("validate"), "bundle 文件声明不一致")

    def test_entry_budget_hard_limit_fails(self) -> None:
        target = self.root / "components/v3/runtime/AGENTS.md.tmpl"
        target.write_text("\n".join(f"line {index}" for index in range(26)), encoding="utf-8")
        result = self.invoke("assemble")
        self.assert_failure(result, "文件预算超过硬上限")

    def test_two_assemblies_are_deterministic(self) -> None:
        first = self.invoke("assemble")
        self.assertEqual(first.returncode, 0, first.stderr)
        bundle = self.root / "bundles/core-workspace-v3"
        first_hash = fingerprint(bundle)
        second = self.invoke("assemble")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first_hash, fingerprint(bundle))

    def test_v1_and_v2_remain_legacy_drafts(self) -> None:
        result = self.invoke("validate")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_hard_enforced_capability_without_script_fails(self) -> None:
        path = self.root / "config/capabilities.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["capabilities"][0]["evidence"]["script"] = "missing.py"
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "能力脚本")

    def test_stable_is_false_without_new_session_evidence(self) -> None:
        result = self.invoke("health", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["stable_eligible"])
        self.assertFalse(report["candidate_eligible"])
        self.assertIn("pending", " ".join(report["release_blockers"]))

    def test_manual_passed_runtime_evidence_cannot_promote(self) -> None:
        evidence = self.root / "tests/runtime/evidence.json"
        evidence.write_text(json.dumps({"codex": "passed", "claude": "passed"}), encoding="utf-8")
        result = self.invoke("health", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["candidate_eligible"])
        self.assertFalse(report["stable_eligible"])
        self.assertIn("runtime evidence", " ".join(report["release_blockers"]))

    def test_invalid_nested_policy_boolean_fails_schema(self) -> None:
        path = self.root / "config/policy.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["permissions"]["writes_require_confirmed_scope"] = False
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "未通过 Schema")

    def test_workflow_ghost_state_and_terminal_exit_fail(self) -> None:
        path = self.root / "config/workflow.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["transitions"].append({"from": "ghost-state", "to": "candidate"})
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "未知状态")

    def test_hard_enforced_evidence_requires_registry_coverage(self) -> None:
        path = self.root / "tests/test-registry.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["tests"][0]["capabilities"] = []
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "未覆盖 hard-enforced")

    def test_declared_check_is_executed(self) -> None:
        script = self.root / "checks/library-smoke.py"
        script.write_text("raise SystemExit(7)\n" + script.read_text(encoding="utf-8"), encoding="utf-8")
        self.assert_failure(self.invoke("validate"), "check 执行失败")

    def test_declared_check_runs_in_sandbox(self) -> None:
        script = self.root / "checks/library-smoke.py"
        script.write_text("from pathlib import Path\nPath('check-side-effect.txt').write_text('sandbox-only')\n" + script.read_text(encoding="utf-8"), encoding="utf-8")
        result = self.invoke("validate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "check-side-effect.txt").exists())

    def test_health_returns_nonzero_for_invalid_health(self) -> None:
        (self.root / "config/agent.yaml").unlink()
        result = self.invoke("health", "--json")
        self.assertNotEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        self.assertEqual(report["health_status"], "blocked")
        allowed = self.invoke("health", "--json", "--allow-unhealthy")
        self.assertEqual(allowed.returncode, 0)

    def test_doctor_reports_missing_pyyaml_without_crashing(self) -> None:
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(
            [PYTHON, "-S", "-B", str(self.root / "harnessctl"), "--root", str(self.root), "doctor"],
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PyYAML", result.stdout)

    def test_manifest_contains_source_identity(self) -> None:
        _, manifest = self.manifest()
        self.assertEqual(manifest["profile"], "core-workspace-v3")
        self.assertIn("assembly_sha256", manifest["source_identity"])

    def test_method_and_skill_budgets_are_consumed(self) -> None:
        source = self.root / "components/v3/runtime/oversized-SKILL.md"
        source.write_text("\n".join(f"line {index}" for index in range(501)), encoding="utf-8")
        assembly_path = self.root / "assemblies/core-workspace-v3.yaml"
        assembly = yaml.safe_load(assembly_path.read_text(encoding="utf-8"))
        assembly["files"].append({"source": "components/v3/runtime/oversized-SKILL.md", "path": "skills/oversized/SKILL.md", "role": "test-skill"})
        assembly_path.write_text(yaml.safe_dump(assembly, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "文件预算超过硬上限")

    def test_assemble_does_not_write_pycache_into_bundle(self) -> None:
        result = self.invoke("assemble")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(path.name == "__pycache__" for path in (self.root / "bundles/core-workspace-v3").rglob("*")))

    def test_fixtures_are_synthetic(self) -> None:
        fixture_text = "\n".join(path.read_text(encoding="utf-8") for path in (self.root / "tests/fixtures").rglob("*") if path.is_file())
        self.assertIn("synthetic", fixture_text)
        self.assertNotIn("real-memory", fixture_text)
        self.assertNotIn("credential=", fixture_text)

    def test_health_json_has_stable_fields(self) -> None:
        result = self.invoke("health", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        for field in ("bundle", "schema_version", "budgets", "checks", "check_paths", "capabilities", "release_blockers", "candidate_eligible", "stable_eligible", "rollback_target"):
            self.assertIn(field, report)


if __name__ == "__main__":
    unittest.main()
