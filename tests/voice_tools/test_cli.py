import json
from pathlib import Path
import tempfile
import unittest
from fixtures import cli, request, Server


class VoiceCLIIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        request(self.root)

    def test_actual_cli_plan_bake_status_collect_verify(self):
        plan = cli(self.root, "plan", "--request", "voice-request.json")
        self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
        self.assertFalse((self.root / ".ccgs-assets").exists())
        with Server() as server:
            server.eligible()
            bake = cli(self.root, "bake", "--request", "voice-request.json", "--write", server=server,
                       extra_env={"ELEVENLABS_API_KEY": "fixture-key"})
            self.assertEqual(bake.returncode, 0, bake.stdout + bake.stderr)
        status = cli(self.root, "status", "--request", "voice-request.json")
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
        collected = cli(self.root, "collect", "--request", "voice-request.json", "--write")
        self.assertEqual(collected.returncode, 0, collected.stdout + collected.stderr)
        manifest = json.loads(collected.stdout)["manifest"]
        verified = cli(self.root, "verify", "--manifest", manifest)
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertNotIn("fixture-key", bake.stdout + bake.stderr)

    def test_cli_voices_and_models_are_explicit_remote_commands(self):
        with Server() as server:
            server.eligible()
            for command in ("voices", "models"):
                result = cli(self.root, command, server=server, extra_env={"ELEVENLABS_API_KEY": "key"})
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIsInstance(json.loads(result.stdout), list)
