import json
import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from fixtures import REPO, wav


class PlaybackLoaderAcceptance(unittest.TestCase):
    def run_loader(self, root, manifest):
        return subprocess.run([sys.executable, str(REPO / "examples/npc-voice/playback_manifest_loader.py"),
                               "--root", str(root), "--manifest", str(manifest)],
                              text=True, capture_output=True, timeout=10)

    def test_loader_resolves_and_decodes_two_npc_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines = []
            for index, npc in enumerate(("merchant", "guard")):
                path = f"assets/audio/vo/en-US/dialogue-{npc}.wav"
                target = root / path; target.parent.mkdir(parents=True, exist_ok=True)
                raw = wav(sample=bytes((index + 1, 0))); target.write_bytes(raw)
                lines.append({"key": f"dialogue.npc.{npc}.line", "locale": "en-US", "npc_id": npc,
                              "path": path, "sha256": hashlib.sha256(raw).hexdigest()})
            manifest = root / "manifest.json"; manifest.write_text(json.dumps({"schema_version": 1, "lines": lines}))
            result = self.run_loader(root, manifest)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output["decoded_lines"], 2)
            self.assertEqual(output["npcs"], ["guard", "merchant"])

    def test_loader_rejects_internal_symlink_component(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            actual = root / "actual"
            actual.mkdir()
            raw = wav()
            (actual / "line.wav").write_bytes(raw)
            audio = root / "assets/audio/vo"
            audio.mkdir(parents=True)
            (audio / "en-US").symlink_to(actual, target_is_directory=True)
            line = {"key": "dialogue.npc.guard.line", "locale": "en-US", "npc_id": "guard",
                    "path": "assets/audio/vo/en-US/line.wav", "sha256": hashlib.sha256(raw).hexdigest()}
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "lines": [line]}))
            result = self.run_loader(root, manifest)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsafe audio path", result.stderr)

    def test_loader_rejects_short_decoded_frame_data_even_when_hash_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = bytearray(wav())
            del raw[-2:]
            raw[4:8] = struct.pack("<I", len(raw) - 8)
            path = "assets/audio/vo/en-US/short.wav"
            target = root / path
            target.parent.mkdir(parents=True)
            target.write_bytes(raw)
            line = {"key": "dialogue.npc.guard.line", "locale": "en-US", "npc_id": "guard",
                    "path": path, "sha256": hashlib.sha256(raw).hexdigest()}
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "lines": [line]}))
            result = self.run_loader(root, manifest)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("incomplete PCM", result.stderr)

    def test_canonical_workflow_runs_localization_validation_after_import(self):
        workflow = (REPO / ".claude/skills/npc-voice/SKILL.md").read_text()
        behavior = (REPO / "CCGS Skill Testing Framework/skills/utility/npc-voice.md").read_text()
        imported = workflow.index("engine imported")
        validated = workflow.index("localization validated")
        self.assertLess(imported, validated)
        self.assertIn("localize vo-pipeline validate", workflow)
        self.assertIn("localize vo-pipeline integrate", workflow)
        self.assertIn("(locale,key) → hashed WAV path", workflow)
        self.assertIn("Missing runtime, source, manifest/key mapping or code-reference evidence blocks", workflow)
        self.assertIn("localization validation and integration", behavior)
