import copy
import json
from pathlib import Path
import tempfile
import unittest
from fixtures import request


class VoiceRequestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def plan(self, **changes):
        from ccgs.voice.request import prepare_request
        path = request(self.root, **changes)
        return prepare_request(self.root, self.root / ".ccgs-assets", path.name)

    def test_request_standalone_plan_is_offline_nowrite_and_keeps_exact_unicode(self):
        text = "你好，旅人。  Café"
        plan = self.plan(lines=[{"key": "dialogue.npc.merchant.greeting", "npc_id": "merchant",
                                "locale": "zh-CN", "text": text, "direction_notes": "轻声"}])
        self.assertEqual(plan["lines"][0]["text"], text)
        self.assertEqual(len(plan["lines"][0]["request_hash"]), 64)
        self.assertFalse((self.root / ".ccgs-assets").exists())

    def test_request_canonical_requires_both_real_source_families(self):
        (self.root / "design/narrative").mkdir(parents=True)
        (self.root / "design/narrative/dialogue.md").write_text("dialogue.npc.merchant.greeting: Welcome, traveller.")
        (self.root / "assets/data/strings").mkdir(parents=True)
        (self.root / "assets/data/strings/en.json").write_text('{"dialogue.npc.merchant.greeting":"Welcome, traveller."}')
        plan = self.plan(standalone=False, source_files=["design/narrative/dialogue.md", "assets/data/strings/en.json"])
        self.assertEqual([item["path"] for item in plan["inputs"]],
                         ["assets/data/strings/en.json", "design/narrative/dialogue.md"])
        with self.assertRaisesRegex(ValueError, "canonical_voice_sources_required"):
            self.plan(standalone=False, source_files=["design/narrative/dialogue.md"])

    def test_request_rejects_unknown_duplicate_and_nonfinite_json_fields(self):
        from ccgs.voice.request import prepare_request
        path = request(self.root)
        value = json.loads(path.read_text())
        value["surprise"] = True
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "unsupported_or_missing_fields"):
            prepare_request(self.root, self.root / ".ccgs-assets", path.name)
        path.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaisesRegex(ValueError, "duplicate_json_field"):
            prepare_request(self.root, self.root / ".ccgs-assets", path.name)
        path.write_text(json.dumps(request_value := json.loads(request(self.root).read_text())).replace("0.4", "NaN", 1))
        with self.assertRaisesRegex(ValueError, "nonfinite_number"):
            prepare_request(self.root, self.root / ".ccgs-assets", path.name)

    def test_request_rejects_invalid_ids_settings_placeholders_and_duplicates(self):
        base = json.loads(request(self.root).read_text())
        cases = []
        duplicate_voice = copy.deepcopy(base); duplicate_voice["npcs"][1]["voice_id"] = duplicate_voice["npcs"][0]["voice_id"]; cases.append(duplicate_voice)
        bool_number = copy.deepcopy(base); bool_number["npcs"][0]["voice_settings"]["stability"] = True; cases.append(bool_number)
        placeholder = copy.deepcopy(base); placeholder["lines"][0]["text"] = "Welcome, {player}."; cases.append(placeholder)
        duplicate_pair = copy.deepcopy(base); duplicate_pair["lines"][1]["key"] = base["lines"][0]["key"]; cases.append(duplicate_pair)
        bad_locale = copy.deepcopy(base); bad_locale["lines"][0]["locale"] = "../../en"; cases.append(bad_locale)
        missing_npc = copy.deepcopy(base); missing_npc["lines"][0]["npc_id"] = "ghost"; cases.append(missing_npc)
        malformed_text = copy.deepcopy(base); malformed_text["lines"][0]["text"] = 7; cases.append(malformed_text)
        malformed_npc = copy.deepcopy(base); malformed_npc["lines"][0]["npc_id"] = []; cases.append(malformed_npc)
        for index, value in enumerate(cases):
            with self.subTest(index=index):
                (self.root / "voice-request.json").write_text(json.dumps(value))
                from ccgs.voice.request import prepare_request
                with self.assertRaises(ValueError):
                    prepare_request(self.root, self.root / ".ccgs-assets", "voice-request.json")

    def test_request_generation_revision_changes_only_generation_identity(self):
        first = self.plan()
        second = self.plan(generation_revision="director-take-2")
        self.assertNotEqual(first["lines"][0]["request_hash"], second["lines"][0]["request_hash"])
        self.assertNotEqual(first["batch_hash"], second["batch_hash"])

    def test_request_voice_settings_locale_and_voice_each_invalidate_line_identity(self):
        base_value = json.loads(request(self.root).read_text())
        from ccgs.voice.request import prepare_request
        base = prepare_request(self.root, self.root / ".ccgs-assets", "voice-request.json")["lines"][0]["request_hash"]
        changes = []
        voice_change = copy.deepcopy(base_value); voice_change["npcs"][0]["voice_id"] = "voice-merchant-take-b"; changes.append(voice_change)
        settings_change = copy.deepcopy(base_value); settings_change["npcs"][0]["voice_settings"]["stability"] = 0.41; changes.append(settings_change)
        locale_change = copy.deepcopy(base_value); locale_change["lines"][0]["locale"] = "en-GB"; changes.append(locale_change)
        for value in changes:
            (self.root / "voice-request.json").write_text(json.dumps(value))
            changed = prepare_request(self.root, self.root / ".ccgs-assets", "voice-request.json")["lines"][0]["request_hash"]
            self.assertNotEqual(changed, base)

    def test_request_source_only_change_keeps_line_identity_and_changes_batch(self):
        (self.root / "design/narrative").mkdir(parents=True)
        source = self.root / "design/narrative/dialogue.md"; source.write_text("first")
        (self.root / "assets/data/strings").mkdir(parents=True)
        strings = self.root / "assets/data/strings/en.json"; strings.write_text("{}")
        kwargs = {"standalone": False, "source_files": ["design/narrative/dialogue.md", "assets/data/strings/en.json"]}
        first = self.plan(**kwargs); source.write_text("second"); second = self.plan(**kwargs)
        self.assertEqual(first["lines"][0]["request_hash"], second["lines"][0]["request_hash"])
        self.assertNotEqual(first["batch_hash"], second["batch_hash"])
