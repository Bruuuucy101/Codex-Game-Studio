"""Exercise the bridge CLI with unchanged validators in disposable git repositories."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class HookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ccgs hooks ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / ".claude", self.root / ".claude")
        (self.root / "tools").mkdir()
        bridge = ROOT / "tools/ccgs_hooks.py"
        if bridge.exists():
            shutil.copy2(bridge, self.root / "tools/ccgs_hooks.py")
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Hook Test")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True, text=True)

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return target

    def run_hook(self, event, payload=None, raw=None, cwd=None, env=None):
        payload = {"hook_event_name": event, "cwd": str(self.root), **(payload or {})}
        p = subprocess.run([sys.executable, str(self.root / "tools/ccgs_hooks.py"), event],
                           input=raw if raw is not None else json.dumps(payload),
                           cwd=cwd or self.root, capture_output=True, text=True, env=env)
        self.assertTrue(p.stdout.strip(), p.stderr)
        return p, json.loads(p.stdout)

    def tool(self, event, command, name="Bash", **extra):
        return self.run_hook(event, {"tool_name": name, "tool_input": {"command": command}, **extra})

    def test_invalid_staged_json_blocks_commit(self):
        self.write("assets/data/bad.json", "{bad}")
        self.git("add", "assets/data/bad.json")
        p, out = self.tool("PreToolUse", "git commit -m 'test'")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("not valid JSON", p.stderr)

    def test_advisory_commit_and_push_warnings_survive_stderr(self):
        self.write("design/gdd/movement.md", "# Overview\n")
        self.git("add", "design/gdd/movement.md")
        p, out = self.tool("PreToolUse", "git commit -m 'test'")
        self.assertEqual(p.returncode, 0)
        self.assertIn("Player Fantasy", out["hookSpecificOutput"]["additionalContext"])
        p, out = self.tool("PreToolUse", "git push origin main")
        self.assertEqual(p.returncode, 0)
        self.assertIn("protected branch", out["hookSpecificOutput"]["additionalContext"])

    def test_all_patch_paths_checked_including_move_and_delete(self):
        self.write("assets/data/good.json", "{}")
        self.write("assets/data/bad.json", "{broken}")
        self.write("assets/Bad-Name.png", "image")
        patch = """*** Begin Patch
*** Add File: assets/data/good.json
+{}
*** Update File: old.txt
*** Move to: assets/data/bad.json
@@
-old
+{broken}
*** Delete File: assets/Bad-Name.png
*** End Patch"""
        p, out = self.tool("PostToolUse", patch, "apply_patch")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(out["decision"], "block")
        self.assertIn("assets/data/bad.json", out["reason"])
        self.assertIn("NAMING", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual((self.root / "assets/data/bad.json").read_text(), "{broken}")

    def test_patch_rules_resolve_tool_cwd_and_preserve_complete_rule(self):
        subdir = self.root / "src"
        subdir.mkdir()
        p, out = self.tool("PreToolUse", "*** Begin Patch\n*** Add File: gameplay/move.gd\n+x\n*** End Patch", "apply_patch", cwd=str(subdir))
        self.assertEqual(p.returncode, 0)
        body = (self.root / ".claude/rules/gameplay-code.md").read_text()
        self.assertIn(body, out["hookSpecificOutput"]["additionalContext"])

    def test_skill_change_advisory_and_unrelated_edit(self):
        p, out = self.tool("PostToolUse", "*** Begin Patch\n*** Update File: .claude/skills/start/SKILL.md\n@@\n-a\n+b\n*** End Patch", "apply_patch")
        self.assertEqual(p.returncode, 0)
        self.assertIn("skill-test static start", out["hookSpecificOutput"]["additionalContext"])
        p, out = self.tool("PostToolUse", "*** Begin Patch\n*** Add File: README.local.md\n+hello\n*** End Patch", "apply_patch")
        self.assertEqual((p.returncode, out), (0, {}))

    def test_unrelated_bash_does_not_run_validators(self):
        shutil.rmtree(self.root / ".claude/hooks")
        for event in ("PreToolUse", "PostToolUse"):
            p, out = self.tool(event, "git status --short")
            self.assertEqual((p.returncode, out), (0, {}))

    def test_lifecycle_recovers_state_and_archives_without_deleting(self):
        state = self.write("production/session-state/active.md", "Current task: recover physics\n")
        p, out = self.run_hook("SessionStart")
        self.assertEqual(p.returncode, 0)
        self.assertIn("recover physics", out["hookSpecificOutput"]["additionalContext"])
        p, out = self.run_hook("PreCompact", {"session_id": "test-session"})
        self.assertEqual(p.returncode, 0)
        self.assertIn("systemMessage", out)
        self.assertNotIn("hookSpecificOutput", out)
        p, out = self.run_hook("PostCompact", {"session_id": "test-session"})
        self.assertEqual(p.returncode, 0)
        p, out = self.run_hook("UserPromptSubmit", {"session_id": "test-session"})
        self.assertIn("recover physics", out["hookSpecificOutput"]["additionalContext"])
        self.assertIn("SESSION STATE BEFORE COMPACTION", out["hookSpecificOutput"]["additionalContext"])
        p, out = self.run_hook("Stop")
        self.assertEqual(p.returncode, 0)
        self.assertTrue(state.exists())
        self.assertIn("recover physics", (self.root / "production/session-logs/session-log.md").read_text())

    def test_subagent_audit_preserves_type(self):
        for event in ("SubagentStart", "SubagentStop"):
            p, out = self.run_hook(event, {"agent_type": "ccgs-qa-lead", "agent_id": "agent-1"})
            self.assertEqual((p.returncode, out), (0, {}))
        audit = (self.root / "production/session-logs/agent-audit.log").read_text()
        self.assertIn("Agent invoked: ccgs-qa-lead", audit)
        self.assertIn("Agent completed: ccgs-qa-lead", audit)

    def test_malformed_inputs_fail_with_valid_event_json(self):
        for raw in ("{", "[]", '{"tool_name":"Bash","tool_input":[]}', '{"tool_name":"apply_patch","tool_input":{"command":"garbage"}}'):
            p, out = self.run_hook("PreToolUse", raw=raw)
            self.assertEqual(p.returncode, 2)
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertNotIn("Traceback", p.stderr)

    def test_original_deny_patterns_and_no_autoallow(self):
        for command in ("rm -rf build", "git push --force origin dev", "sudo whoami", "cat .env.local", "echo secret>.env", "git reset --hard HEAD"):
            p, out = self.tool("PreToolUse", command)
            self.assertEqual(p.returncode, 2, command)
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        p, out = self.tool("PreToolUse", "git log -1")
        self.assertEqual((p.returncode, out), (0, {}))

    def test_missing_validator_reported_and_json_never_executed(self):
        (self.root / ".claude/hooks/validate-commit.sh").unlink()
        p, out = self.tool("PreToolUse", "git commit -m '$(touch INJECTED)'")
        self.assertEqual(p.returncode, 2)
        self.assertIn("validate-commit.sh", p.stderr)
        self.assertFalse((self.root / "INJECTED").exists())

    def test_nested_asset_invalid_json_keeps_original_coverage(self):
        path = "games/demo/assets/data/bad.json"
        self.write(path, "{broken}")
        p, out = self.tool("PostToolUse", f"*** Begin Patch\n*** Add File: {path}\n+{{broken}}\n*** End Patch", "apply_patch")
        self.assertEqual(p.returncode, 2)
        self.assertIn(path, out["reason"])

    def test_nested_skill_change_keeps_original_advisory(self):
        patch = "*** Begin Patch\n*** Update File: games/demo/.claude/skills/start/SKILL.md\n@@\n-a\n+b\n*** End Patch"
        p, out = self.tool("PostToolUse", patch, "apply_patch")
        self.assertEqual(p.returncode, 0)
        self.assertIn("skill-test static start", out.get("hookSpecificOutput", {}).get("additionalContext", ""))

    def test_unicode_asset_path_without_jq_still_validates_json(self):
        # A real minimal PATH forces the unchanged upstream grep/sed fallback.
        bindir = self.root / "no-jq-bin"
        bindir.mkdir()
        for command in ("bash", "cat", "grep", "sed", "basename"):
            (bindir / command).symlink_to(shutil.which(command))
        (bindir / "python3").symlink_to(sys.executable)
        env = {**os.environ, "PATH": str(bindir)}
        path = "assets/data/中文.json"
        self.write(path, "{broken}")
        original = subprocess.run([str(bindir / "bash"), str(self.root / ".claude/hooks/validate-assets.sh")],
                                  input=json.dumps({"tool_input": {"file_path": path}}, ensure_ascii=False),
                                  cwd=self.root, env=env, capture_output=True, text=True)
        self.assertEqual(original.returncode, 1, original.stderr)
        patch = f"*** Begin Patch\n*** Add File: {path}\n+{{broken}}\n*** End Patch"
        p, out = self.run_hook("PostToolUse", {"tool_name": "apply_patch", "tool_input": {"command": patch}}, env=env)
        self.assertEqual(p.returncode, 2)
        self.assertIn(path, out["reason"])

    def test_read_denial_and_malformed_read_path(self):
        for path in (".env", "config/.env.local"):
            p, out = self.run_hook("PreToolUse", {"tool_name": "Read", "tool_input": {"file_path": path}})
            self.assertEqual(p.returncode, 2)
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        p, out = self.run_hook("PreToolUse", {"tool_name": "Read", "tool_input": {"file_path": []}})
        self.assertEqual(p.returncode, 2)
        self.assertNotIn("Traceback", p.stderr)

    def test_compaction_failure_keeps_original_error_feedback(self):
        # Fault injection after a real upstream script, to verify failure transport.
        script = self.root / ".claude/hooks/pre-compact.sh"
        script.write_text(script.read_text().replace("exit 0", "echo CHECKPOINT_FAILURE >&2\nexit 3"))
        p, out = self.run_hook("PreCompact")
        self.assertEqual(p.returncode, 2)
        self.assertIn("CHECKPOINT_FAILURE", out["stopReason"])
        self.assertFalse(out["continue"])

    def test_registration_runs_from_subdirectory_with_spaces(self):
        config_path = ROOT / ".codex/hooks.json"
        self.assertTrue(config_path.exists())
        cfg = json.loads(config_path.read_text())
        cmd = cfg["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        subdir = self.root / "nested space"
        subdir.mkdir()
        p = subprocess.run(cmd, shell=True, cwd=subdir, input="{}", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("SessionStart", p.stdout)


if __name__ == "__main__":
    unittest.main()
