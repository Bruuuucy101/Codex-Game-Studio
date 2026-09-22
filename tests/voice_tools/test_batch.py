import json
from pathlib import Path
import tempfile
import unittest
from fixtures import request, Server, wav


class VoiceBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        request(self.root)

    def test_bake_default_is_no_write_no_network(self):
        from ccgs.voice.batch import bake
        class NoNetwork:
            def __getattr__(self, name):
                raise AssertionError(name)
        result = bake(self.root, self.root / ".ccgs-assets", "voice-request.json", transport=NoNetwork())
        self.assertEqual(result["status"], "planned")
        self.assertFalse((self.root / ".ccgs-assets").exists())

    def test_bake_two_npcs_repeat_zero_posts_and_collect_manifest_last(self):
        from ccgs.voice.batch import bake, collect
        with Server() as server:
            server.eligible()
            first = bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                         transport=server.transport(), credential="fixture-key")
            self.assertEqual([line["status"] for line in first["lines"]], ["generated", "generated"])
            post_count = sum(call[0] == "POST" for call in server.calls)
            second = bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                          transport=server.transport(), credential="fixture-key")
            self.assertEqual(sum(call[0] == "POST" for call in server.calls), post_count)
            result = collect(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True)
            manifest = self.root / result["manifest"]
            self.assertTrue(manifest.is_file())
            value = json.loads(manifest.read_text())
            self.assertEqual(len(value["lines"]), 2)
            self.assertTrue(all((self.root / line["path"]).is_file() for line in value["lines"]))
            self.assertTrue(all(line["review"] == {"listening": "pending", "engine_import": "pending"} for line in value["lines"]))

    def test_changed_one_line_posts_once_and_source_only_change_posts_zero(self):
        from ccgs.voice.batch import bake, collect
        with Server() as server:
            server.eligible()
            bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                 transport=server.transport(), credential="fixture-key")
            before = sum(call[0] == "POST" for call in server.calls)
            value = json.loads((self.root / "voice-request.json").read_text())
            value["lines"][1]["text"] = "Halt."
            (self.root / "voice-request.json").write_text(json.dumps(value))
            bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                 transport=server.transport(), credential="fixture-key")
            self.assertEqual(sum(call[0] == "POST" for call in server.calls) - before, 1)

        canonical = json.loads((self.root / "voice-request.json").read_text())
        (self.root / "design/narrative").mkdir(parents=True); (self.root / "design/narrative/dialogue.md").write_text("v1")
        (self.root / "assets/data/strings").mkdir(parents=True); (self.root / "assets/data/strings/en.json").write_text("{}")
        canonical.update(standalone=False, source_files=["design/narrative/dialogue.md", "assets/data/strings/en.json"])
        (self.root / "voice-request.json").write_text(json.dumps(canonical))
        with Server() as server:
            server.eligible()
            bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True, transport=server.transport(), credential="key")
            (self.root / "design/narrative/dialogue.md").write_text("v2")
            before = sum(call[0] == "POST" for call in server.calls)
            result = bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True, transport=server.transport(), credential="key")
            self.assertEqual(sum(call[0] == "POST" for call in server.calls), before)
            self.assertNotEqual(result["source_revision"], result["lines"][0]["generation_source_revision"])
        collected = collect(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True)
        manifest = json.loads((self.root / collected["manifest"]).read_text())
        self.assertEqual(manifest["source_revision"], result["source_revision"])
        self.assertTrue(all(line["generation_source_revision"] != manifest["source_revision"]
                            for line in manifest["lines"]))

    def test_bake_preflights_foreign_manifest_and_blocked_manifest_ancestor_with_zero_posts(self):
        from ccgs.voice.batch import bake
        from ccgs.voice.request import prepare_request
        for blocked_ancestor in (False, True):
            with self.subTest(blocked_ancestor=blocked_ancestor), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                request(root)
                plan = prepare_request(root, root / ".ccgs-assets", "voice-request.json")
                manifest = root / "assets/audio/vo/manifests" / (plan["batch_hash"] + ".json")
                manifest.parent.parent.mkdir(parents=True)
                if blocked_ancestor:
                    manifest.parent.write_text("not a directory")
                else:
                    manifest.parent.mkdir()
                    manifest.write_text("foreign")
                with Server() as server:
                    server.eligible()
                    with self.assertRaises(ValueError):
                        bake(root, root / ".ccgs-assets", "voice-request.json", write=True,
                             transport=server.transport(), credential="key")
                    self.assertEqual(sum(call[0] == "POST" for call in server.calls), 0)

    def test_bake_preflights_later_line_private_parent_and_stage_with_zero_posts(self):
        from ccgs.voice.batch import bake
        from ccgs.voice.request import prepare_request
        for blocker_kind in ("parent", "stage"):
            with self.subTest(blocker_kind=blocker_kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                request(root)
                plan = prepare_request(root, root / ".ccgs-assets", "voice-request.json")
                lines = root / ".ccgs-assets/voice/lines"
                lines.mkdir(parents=True, mode=0o700)
                (root / ".ccgs-assets").chmod(0o700)
                (root / ".ccgs-assets/voice").chmod(0o700)
                line_dir = lines / plan["lines"][1]["operation_id"]
                if blocker_kind == "parent":
                    line_dir.write_text("not a directory")
                    line_dir.chmod(0o600)
                else:
                    line_dir.mkdir(mode=0o700)
                    blocker = line_dir / "audio.wav"
                    blocker.write_bytes(b"foreign")
                    blocker.chmod(0o600)
                with Server() as server:
                    server.eligible()
                    with self.assertRaises(ValueError):
                        bake(root, root / ".ccgs-assets", "voice-request.json", write=True,
                             transport=server.transport(), credential="key")
                    self.assertEqual(sum(call[0] == "POST" for call in server.calls), 0)

    def test_bake_allows_genuinely_owned_prior_complete_manifest_without_post(self):
        from ccgs.voice.batch import bake, collect
        with Server() as server:
            server.eligible()
            bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                 transport=server.transport(), credential="key")
            collected = collect(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True)
            before = sum(call[0] == "POST" for call in server.calls)
            repeated = bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                            transport=server.transport(), credential="key")
            self.assertEqual(repeated["status"], "generated")
            self.assertEqual(sum(call[0] == "POST" for call in server.calls), before)
            self.assertTrue((self.root / collected["manifest"]).is_file())

    def test_response_loss_blocks_retry_while_other_line_succeeds(self):
        from ccgs.voice.batch import bake
        with Server() as server:
            server.eligible()
            def lost(handler):
                handler.connection.shutdown(2)
                handler.connection.close()
            server.routes["POST", "/v1/text-to-speech/voice-merchant?output_format=wav_24000"] = lost
            first = bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                         transport=server.transport(retry_delay=0), credential="key")
            self.assertEqual([line["status"] for line in first["lines"]], ["submission_unknown", "generated"])
            self.assertEqual(first["lines"][0]["diagnostic"], "network_or_partial_response")
            before = sum(call[0] == "POST" for call in server.calls)
            again = bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                         transport=server.transport(retry_delay=0), credential="key")
            self.assertEqual(sum(call[0] == "POST" for call in server.calls), before)
            self.assertEqual(again["lines"][0]["status"], "submission_unknown")

    def test_known_failed_http_line_is_not_automatically_replayed(self):
        from ccgs.voice.batch import bake
        with Server() as server:
            server.eligible()
            server.routes["POST", "/v1/text-to-speech/voice-merchant?output_format=wav_24000"] = (
                429, {"detail": "fixture denial"}, {})
            first = bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                         transport=server.transport(retry_delay=0), credential="key")
            self.assertEqual(first["lines"][0]["status"], "failed")
            self.assertEqual(first["lines"][0]["diagnostic"], "http_429")
            before = sum(call[0] == "POST" for call in server.calls)
            again = bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                         transport=server.transport(retry_delay=0), credential="key")
            self.assertEqual(sum(call[0] == "POST" for call in server.calls), before)
            self.assertEqual(again["lines"][0]["status"], "failed")

    def test_collect_rejects_corrupt_stage_and_retains_partial_publication(self):
        from ccgs.voice.batch import bake, collect
        with Server() as server:
            server.eligible()
            bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                 transport=server.transport(), credential="key")
        receipts = sorted((self.root / ".ccgs-assets/voice/lines").glob("*/receipt.json"))
        second = json.loads(receipts[1].read_text())
        (self.root / second["staged_path"]).write_bytes(b"not wave")
        with self.assertRaises(ValueError):
            collect(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True)
        self.assertFalse(list((self.root / "assets/audio/vo/manifests").glob("*.json")) if (self.root / "assets/audio/vo/manifests").exists() else [])

    def test_collect_retains_first_publication_when_later_destination_is_claimed(self):
        from unittest.mock import patch
        from ccgs.assets import artifacts
        from ccgs.voice.batch import bake, collect
        from ccgs.voice.request import prepare_request
        with Server() as server:
            server.eligible()
            bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                 transport=server.transport(), credential="key")
        plan = prepare_request(self.root, self.root / ".ccgs-assets", "voice-request.json")
        first = self.root / plan["lines"][0]["output_path"]
        second = self.root / plan["lines"][1]["output_path"]
        original = artifacts.publish
        calls = []

        def claim_second_after_first(root, destination, staged, expected_hash):
            if calls and destination == plan["lines"][1]["output_path"]:
                second.parent.mkdir(parents=True, exist_ok=True)
                second.write_bytes(b"foreign competitor")
            original(root, destination, staged, expected_hash)
            calls.append(destination)

        with patch.object(artifacts, "publish", side_effect=claim_second_after_first):
            with self.assertRaisesRegex(ValueError, "collision"):
                collect(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True)
        self.assertTrue(first.is_file())
        self.assertEqual(second.read_bytes(), b"foreign competitor")
        self.assertFalse((self.root / "assets/audio/vo/manifests").exists())

    def test_verify_manifest_detects_hash_or_pcm_changes(self):
        from ccgs.voice.batch import bake, collect, verify_manifest
        with Server() as server:
            server.eligible(); bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True, transport=server.transport(), credential="key")
        result = collect(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True)
        verified = verify_manifest(self.root, result["manifest"])
        self.assertEqual(verified["status"], "verified")
        manifest = json.loads((self.root / result["manifest"]).read_text())
        (self.root / manifest["lines"][0]["path"]).write_bytes(wav(sample=b"\x09\x00"))
        with self.assertRaisesRegex(ValueError, "hash"):
            verify_manifest(self.root, result["manifest"])

    def test_durable_audio_before_generated_receipt_recovers_without_post(self):
        from ccgs.voice.batch import bake
        with Server() as server:
            server.eligible()
            bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                 transport=server.transport(), credential="key")
            receipt_path = sorted((self.root / ".ccgs-assets/voice/lines").glob("*/receipt.json"))[0]
            receipt = json.loads(receipt_path.read_text())
            receipt["status"] = "submitting"
            receipt["sha256"] = None
            receipt["audio"] = None
            receipt_path.write_text(json.dumps(receipt))
            before = sum(call[0] == "POST" for call in server.calls)
            recovered = bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                             transport=server.transport(), credential="key")
            self.assertEqual(sum(call[0] == "POST" for call in server.calls), before)
            self.assertEqual(recovered["lines"][0]["status"], "generated")

    def test_concurrent_duplicate_bake_makes_one_post_for_one_line(self):
        from concurrent.futures import ThreadPoolExecutor
        import time
        from ccgs.voice.batch import bake
        value = json.loads((self.root / "voice-request.json").read_text())
        value["lines"] = value["lines"][:1]
        (self.root / "voice-request.json").write_text(json.dumps(value))
        with Server() as server:
            server.eligible()
            def slow(handler):
                time.sleep(0.15)
                raw = wav()
                handler.send_response(200); handler.send_header("Content-Length", str(len(raw))); handler.end_headers(); handler.wfile.write(raw)
            server.routes["POST", "/v1/text-to-speech/voice-merchant?output_format=wav_24000"] = slow
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: bake(self.root, self.root / ".ccgs-assets", "voice-request.json",
                                                       write=True, transport=server.transport(), credential="key"), range(2)))
            self.assertEqual(sum(call[0] == "POST" for call in server.calls), 1)
            self.assertTrue(any(result["lines"][0]["status"] == "generated" for result in results))

    def test_source_change_during_batch_stops_remaining_post_and_keeps_completed_line(self):
        from ccgs.voice.batch import bake
        (self.root / "design/narrative").mkdir(parents=True)
        source = self.root / "design/narrative/dialogue.md"; source.write_text("v1")
        (self.root / "assets/data/strings").mkdir(parents=True)
        (self.root / "assets/data/strings/en.json").write_text("{}")
        value = json.loads((self.root / "voice-request.json").read_text())
        value.update(standalone=False, source_files=["design/narrative/dialogue.md", "assets/data/strings/en.json"])
        (self.root / "voice-request.json").write_text(json.dumps(value))
        with Server() as server:
            server.eligible()
            def change_source(handler):
                source.write_text("v2")
                raw = wav()
                handler.send_response(200); handler.send_header("Content-Length", str(len(raw))); handler.end_headers(); handler.wfile.write(raw)
            server.routes["POST", "/v1/text-to-speech/voice-merchant?output_format=wav_24000"] = change_source
            with self.assertRaisesRegex(ValueError, "source_changed"):
                bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                     transport=server.transport(), credential="key")
            self.assertEqual(sum(call[0] == "POST" for call in server.calls), 1)
            receipts = list((self.root / ".ccgs-assets/voice/lines").glob("*/receipt.json"))
            self.assertEqual(len(receipts), 1)
            self.assertEqual(json.loads(receipts[0].read_text())["status"], "generated")

    def test_identical_byte_competitor_is_not_adopted_and_manifest_is_absent(self):
        from ccgs.voice.batch import bake, collect
        with Server() as server:
            server.eligible()
            bake(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True,
                 transport=server.transport(), credential="key")
        receipt = json.loads(sorted((self.root / ".ccgs-assets/voice/lines").glob("*/receipt.json"))[0].read_text())
        stage = self.root / receipt["staged_path"]
        destination = self.root / json.loads((self.root / "voice-request.json").read_text())["lines"][0]["locale"]
        from ccgs.voice.request import prepare_request
        plan = prepare_request(self.root, self.root / ".ccgs-assets", "voice-request.json")
        destination = self.root / plan["lines"][0]["output_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(stage.read_bytes())
        with self.assertRaisesRegex(ValueError, "collision"):
            collect(self.root, self.root / ".ccgs-assets", "voice-request.json", write=True)
        self.assertEqual(destination.read_bytes(), stage.read_bytes())
        self.assertFalse((self.root / "assets/audio/vo/manifests").exists())
