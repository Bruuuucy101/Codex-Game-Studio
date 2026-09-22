import json
import unittest
from fixtures import Server, model, voice, wav


class ElevenLabsHTTPTests(unittest.TestCase):
    def test_discovery_missing_credential_fails_before_transport(self):
        from ccgs.voice.elevenlabs import voices
        class NoNetwork:
            def __getattr__(self, name):
                raise AssertionError(name)
        with self.assertRaisesRegex(ValueError, "credential"):
            voices(NoNetwork(), None)

    def test_http_uses_fixed_xi_api_key_and_single_binary_post(self):
        with Server() as server:
            server.routes["POST", "/v1/text-to-speech/a%2Fb?output_format=wav_24000"] = (200, wav(), {})
            raw = server.transport().elevenlabs_audio("/v1/text-to-speech/a%2Fb?output_format=wav_24000",
                                                      body={"text": "Exact", "model_id": "eleven_multilingual_v2",
                                                            "voice_settings": {"stability": 0.4, "similarity_boost": 0.7}},
                                                      credential="fixture-key")
            self.assertEqual(raw, wav())
            call = server.calls[0]
            self.assertEqual(call[2]["xi-api-key"], "fixture-key")
            self.assertNotIn("Authorization", call[2])
            self.assertEqual(json.loads(call[3])["text"], "Exact")
            self.assertEqual(len(server.calls), 1)

    def test_discovery_follows_has_more_tokens_and_rejects_repeated_cursor(self):
        from ccgs.voice.elevenlabs import voices
        with Server() as server:
            server.routes["GET", "/v2/voices?page_size=100&include_total_count=false"] = (
                200, {"voices": [voice("one", "One")], "has_more": True, "total_count": 999, "next_page_token": "cursor"}, {})
            server.routes["GET", "/v2/voices?page_size=100&include_total_count=false&next_page_token=cursor"] = (
                200, {"voices": [voice("two", "Two")], "has_more": False, "total_count": 1, "next_page_token": None}, {})
            self.assertEqual([v["voice_id"] for v in voices(server.transport(), "key")], ["one", "two"])
            server.calls.clear()
            server.routes["GET", "/v2/voices?page_size=100&include_total_count=false&next_page_token=cursor"] = (
                200, {"voices": [], "has_more": True, "total_count": 0, "next_page_token": "cursor"}, {})
            with self.assertRaisesRegex(ValueError, "pagination"):
                voices(server.transport(), "key")
            self.assertEqual(len(server.calls), 2)

    def test_eligibility_checks_model_language_voice_boost_and_smallest_limit(self):
        from ccgs.voice.elevenlabs import validate_eligibility
        with Server() as server:
            server.eligible()
            plan = {"model_id": "eleven_multilingual_v2", "lines": [{"voice_id": "voice-merchant", "locale": "en-US", "text": "abcd",
                    "voice_settings": {"stability": 0.4, "similarity_boost": 0.7, "use_speaker_boost": True}}]}
            result = validate_eligibility(plan, server.transport(), "key")
            self.assertEqual(result["character_limit"], 2500)
            server.routes["GET", "/v1/models"] = (200, [model(languages=[{"language_id": "fr", "name": "French"}])], {})
            with self.assertRaisesRegex(ValueError, "language"):
                validate_eligibility(plan, server.transport(), "key")

    def test_eligibility_rejects_denied_voice_tts_and_speaker_boost(self):
        from ccgs.voice.elevenlabs import validate_eligibility
        plan = {"model_id": "eleven_multilingual_v2", "lines": [{
            "voice_id": "voice-merchant", "locale": "en-US", "text": "abcd",
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.7,
                               "use_speaker_boost": True}}]}
        with Server() as server:
            server.eligible()
            unavailable = {**plan, "lines": [{**plan["lines"][0], "voice_id": "denied"}]}
            with self.assertRaisesRegex(ValueError, "voice_unavailable"):
                validate_eligibility(unavailable, server.transport(), "key")
            server.routes["GET", "/v1/models"] = (200, [model(can_do_text_to_speech=False)], {})
            with self.assertRaisesRegex(ValueError, "text_to_speech_denied"):
                validate_eligibility(plan, server.transport(), "key")
            server.routes["GET", "/v1/models"] = (200, [model(can_use_speaker_boost=False)], {})
            with self.assertRaisesRegex(ValueError, "speaker_boost_denied"):
                validate_eligibility(plan, server.transport(), "key")
