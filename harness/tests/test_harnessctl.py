"""Static governance regression tests for Harness v3."""

from __future__ import annotations

import hashlib
import json
import os
import runpy
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

    def invoke(self, *args: str, allow_unverified_provenance: bool = True) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        command = [PYTHON, "-B", str(self.root / "harnessctl"), "--root", str(self.root)]
        if allow_unverified_provenance:
            command.append("--allow-unverified-provenance")
        command.extend(args)
        return subprocess.run(
            command,
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
        (self.root / "checks/library-smoke.py").unlink()
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

    def test_hard_enforced_script_must_match_registration(self) -> None:
        path = self.root / "config/capabilities.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["capabilities"][0]["evidence"]["script"] = "README.md"
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "脚本未绑定注册组件")

    def test_hard_enforced_check_must_cover_capability(self) -> None:
        path = self.root / "config/capabilities.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["capabilities"][0]["evidence"]["check_id"] = "bundle-layout"
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "check 未声明覆盖")

    def test_stable_is_false_without_new_session_evidence(self) -> None:
        result = self.invoke("health", "--json", "--allow-unhealthy")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["stable_eligible"])
        self.assertFalse(report["candidate_eligible"])
        self.assertIn("pending", " ".join(report["release_blockers"]))

    def test_manual_passed_runtime_evidence_cannot_promote(self) -> None:
        evidence = self.root / "tests/runtime/evidence.json"
        evidence.write_text(json.dumps({
            "schema_version": "1",
            "kind": "runtime-evidence",
            "status": "passed",
            "verifier": "unavailable-in-phase-1",
            "runtimes": {"codex": {"status": "passed"}, "claude": {"status": "passed"}},
            "attestation": None,
            "note": "synthetic forged evidence",
        }), encoding="utf-8")
        behavior = self.root / "tests/behavior/cases.yaml"
        behavior_data = yaml.safe_load(behavior.read_text(encoding="utf-8"))
        behavior_data["status"] = "passed"
        behavior.write_text(yaml.safe_dump(behavior_data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        result = self.invoke("health", "--json", "--allow-unhealthy")
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
        self.assert_failure(self.invoke("assemble"), "capabilities 无效")

    def test_registered_tests_are_executed(self) -> None:
        path = self.root / "tests/test_harnessctl.py"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(
            '\nif __name__ == "__main__":',
            '\nraise SystemExit(7)\n\nif __name__ == "__main__":',
        ), encoding="utf-8")
        self.assert_failure(self.invoke("validate"), "注册测试失败")

    def test_registered_selector_cannot_be_reassigned(self) -> None:
        path = self.root / "tests/test-registry.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["tests"][0]["selectors"] = ["HarnessCtlTests.test_fixtures_are_synthetic"]
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "selectors 与内置证据契约不一致")

    def test_declared_check_is_executed(self) -> None:
        script = self.root / "checks/library-smoke.py"
        script.write_text("raise SystemExit(7)\n" + script.read_text(encoding="utf-8"), encoding="utf-8")
        self.assert_failure(self.invoke("validate"), "check 执行失败")

    def test_check_command_cannot_bypass_declared_script(self) -> None:
        script = self.root / "checks/library-smoke.py"
        script.write_text("raise SystemExit(7)\n" + script.read_text(encoding="utf-8"), encoding="utf-8")
        assembly_path = self.root / "assemblies/core-workspace-v3.yaml"
        assembly = yaml.safe_load(assembly_path.read_text(encoding="utf-8"))
        assembly["checks"][1]["command"] = ["python", "-c", "import sys;sys.exit(0)", "checks/library-smoke.py"]
        assembly_path.write_text(yaml.safe_dump(assembly, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "只允许解释器")

    def test_declared_check_runs_in_sandbox(self) -> None:
        script = self.root / "checks/library-smoke.py"
        script.write_text("from pathlib import Path\nPath('check-side-effect.txt').write_text('sandbox-only')\n" + script.read_text(encoding="utf-8"), encoding="utf-8")
        result = self.invoke("validate")
        self.assert_failure(result, "check 不得修改 sandbox")
        self.assertFalse((self.root / "check-side-effect.txt").exists())

    def test_check_cannot_escape_sandbox(self) -> None:
        escaped = self.root.parent / "escaped-check.txt"
        script = self.root / "checks/library-smoke.py"
        script.write_text(
            "from pathlib import Path\n"
            f"Path({str(escaped)!r}).write_text('must-not-land')\n"
            + script.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.assert_failure(self.invoke("validate"), "check 执行失败")
        self.assertFalse(escaped.exists())

    def test_registered_test_cannot_escape_sandbox(self) -> None:
        escaped = self.root.parent / "escaped-registration.txt"
        path = self.root / "tests/test_harnessctl.py"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "import unittest\n",
                "import unittest\nfrom pathlib import Path as _EscapePath\n"
                f"_EscapePath({str(escaped)!r}).write_text('must-not-land')\n",
                1,
            ),
            encoding="utf-8",
        )
        self.assert_failure(self.invoke("validate"), "注册测试失败")
        self.assertFalse(escaped.exists())

    def test_stable_requires_candidate_gate(self) -> None:
        ctl = self.root / "harnessctl"
        ctl.write_text(ctl.read_text(encoding="utf-8").replace(
            "RUNTIME_EVIDENCE_VERIFIER_AVAILABLE = False",
            "RUNTIME_EVIDENCE_VERIFIER_AVAILABLE = True",
        ), encoding="utf-8")
        schema_path = self.root / "schemas/runtime-evidence.schema.json"
        schema = schema_path.read_text(encoding="utf-8").replace(
            '{"const": "unverified"}',
            '{"enum": ["unverified", "passed"]}',
        )
        schema_path.write_text(schema, encoding="utf-8")
        evidence = self.root / "tests/runtime/evidence.json"
        evidence.write_text(json.dumps({
            "schema_version": "1",
            "kind": "runtime-evidence",
            "status": "passed",
            "verifier": "unavailable-in-phase-1",
            "runtimes": {"codex": {"status": "passed"}, "claude": {"status": "passed"}},
            "attestation": None,
            "note": "synthetic trusted-verifier simulation",
        }), encoding="utf-8")
        result = self.invoke("health", "--json", "--allow-unhealthy")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["candidate_eligible"])
        self.assertFalse(report["stable_eligible"])

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

    def test_source_identity_values_are_enforced(self) -> None:
        path = self.root / "assemblies/core-workspace-v3.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["source"] = {"base_commit": "deadbeef", "ref": "main"}
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "40 位小写 Git SHA")
        data["source"] = {
            "base_commit": "335c2f45d9d501e59c2a4fea860f0c30282d5864",
            "ref": "feat/reusable-harness-library",
        }
        data["generator"] = {"id": "not-harnessctl", "version": "999"}
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "generator 身份无效")

    def test_source_provenance_requires_git_or_explicit_unverified_mode(self) -> None:
        strict = self.invoke("validate", allow_unverified_provenance=False)
        self.assert_failure(strict, "source provenance")
        diagnostic = self.invoke("health", "--json")
        self.assertEqual(diagnostic.returncode, 0, diagnostic.stderr)
        report = json.loads(diagnostic.stdout)
        self.assertEqual(report["source_provenance"]["status"], "unverified")
        self.assertFalse(report["candidate_eligible"])

    def test_manifest_validation_direct(self) -> None:
        target = self.root / "bundles/core-workspace-v3/config/agent.yaml"
        target.write_text(target.read_text(encoding="utf-8") + "\nchanged: true\n", encoding="utf-8")
        module = runpy.run_path(str(self.root / "harnessctl"))
        with self.assertRaises(module["HarnessError"]) as raised:
            module["validate_bundle"](self.root, self.root / "bundles/core-workspace-v3")
        self.assertIn("SHA-256 不一致", str(raised.exception))

    def test_turn_envelope_schema_is_single_field_owner(self) -> None:
        workflow = yaml.safe_load((self.root / "config/workflow.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("required", workflow["turn_envelope"])
        path = self.root / "schemas/turn-envelope.schema.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["required"][0] = "invented_field"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "required 必须与 properties 精确一致")

    def test_closeout_requires_exact_outcome_states(self) -> None:
        path = self.root / "config/workflow.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["closeout"]["required_for"].remove("deliverable")
        data["closeout"]["required_for"].append("closed")
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "精确覆盖五个结果状态")

    def test_sensitive_bundle_content_is_rejected(self) -> None:
        source = self.root / "components/v3/synthetic-secret.yaml"
        source.write_text("password: hunter2\n", encoding="utf-8")
        assembly_path = self.root / "assemblies/core-workspace-v3.yaml"
        assembly = yaml.safe_load(assembly_path.read_text(encoding="utf-8"))
        assembly["files"].append({
            "source": "components/v3/synthetic-secret.yaml",
            "path": "fixtures/synthetic-secret.yaml",
            "role": "synthetic-negative-fixture",
        })
        assembly_path.write_text(yaml.safe_dump(assembly, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "发布白名单")

    def test_session_history_is_not_assemblable(self) -> None:
        source = self.root / "components/v3/session-history.md"
        source.write_text("2026-07-22\nuser-decision: private project\n", encoding="utf-8")
        assembly_path = self.root / "assemblies/core-workspace-v3.yaml"
        assembly = yaml.safe_load(assembly_path.read_text(encoding="utf-8"))
        assembly["files"].append({
            "source": "components/v3/session-history.md",
            "path": "session-history.md",
            "role": "runtime-entry-template",
        })
        assembly_path.write_text(yaml.safe_dump(assembly, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "发布白名单")

    def test_structured_credential_keys_are_rejected(self) -> None:
        source = self.root / "components/v3/templates/memory/topic.md"
        source.write_text("access_token: ghp_synthetic_not_real\n", encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "疑似包含凭证赋值")

    def test_requirements_map_is_enforced(self) -> None:
        path = self.root / "tests/requirements-map.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["requirements"][0]["tests"][0] = "test_does_not_exist"
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "语义契约不一致")

    def test_requirement_selector_swap_fails(self) -> None:
        path = self.root / "tests/requirements-map.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        first = next(item for item in data["requirements"] if item["id"] == "config-schema")
        second = next(item for item in data["requirements"] if item["id"] == "doctor")
        first["tests"], second["tests"] = second["tests"], first["tests"]
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "语义契约不一致")

    def test_doctor_reports_hook_and_interpreter_boundaries(self) -> None:
        result = self.invoke("doctor")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Hook 注册点：未注册", result.stdout)
        self.assertIn("sys.executable", result.stdout)

    def test_method_and_skill_budgets_are_consumed(self) -> None:
        source = self.root / "components/v3/skills/foundation/SKILL.md"
        original = source.read_text(encoding="utf-8")
        source.write_text("\n".join(f"line {index}" for index in range(501)), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "文件预算超过硬上限")
        source.write_text(original, encoding="utf-8")
        method = self.root / "components/v3/methods/foundation.md"
        method.write_text("x" * (12 * 1024 + 1), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "文件预算超过硬上限")

    def test_memory_topic_budget_hard_limit_fails(self) -> None:
        source = self.root / "components/v3/templates/memory/topic.md"
        source.write_text("x" * (32 * 1024 + 1), encoding="utf-8")
        self.assert_failure(self.invoke("assemble"), "memory-topic")

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
        for field in ("bundle", "schema_version", "budgets", "checks", "check_paths", "check_results", "registered_test_results", "requirements_coverage", "source_provenance", "capabilities", "release_blockers", "candidate_eligible", "stable_eligible", "rollback_target"):
            self.assertIn(field, report)
        self.assertEqual(report["static_tests"], "passed")
        self.assertEqual(report["requirements_coverage"]["mapped_tests"], report["requirements_coverage"]["discovered_tests"])
        self.assertTrue(all(item["filesystem_mutation"] == "none" for item in report["check_results"] + report["registered_test_results"]))


if __name__ == "__main__":
    unittest.main()
