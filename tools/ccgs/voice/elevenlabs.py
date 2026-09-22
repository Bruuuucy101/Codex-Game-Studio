"""Narrow exact ElevenLabs discovery, eligibility and synchronous generation."""
from urllib.parse import quote

from ..assets.request import fail

MAX_PAGES = 100


def _credential(value):
    if not isinstance(value, str) or not value or "\r" in value or "\n" in value:
        fail("provider_credential_unavailable")
    return value


def voices(transport, credential):
    """Read every voice page using has_more and a bounded non-repeating cursor."""
    credential = _credential(credential)
    result = []
    cursor = None
    seen = set()
    for _ in range(MAX_PAGES):
        path = "/v2/voices?page_size=100&include_total_count=false"
        if cursor is not None:
            path += "&next_page_token=" + quote(cursor, safe="")
        page = transport.elevenlabs_json("GET", path, credential=credential)
        if (not isinstance(page, dict) or not isinstance(page.get("voices"), list) or
                type(page.get("has_more")) is not bool):
            fail("malformed_voice_pagination")
        for item in page["voices"]:
            if not isinstance(item, dict) or not isinstance(item.get("voice_id"), str) or not item["voice_id"]:
                fail("malformed_voice_record")
            result.append(item)
        if not page["has_more"]:
            return result
        next_cursor = page.get("next_page_token")
        if not isinstance(next_cursor, str) or not next_cursor or next_cursor in seen:
            fail("malformed_voice_pagination")
        seen.add(next_cursor)
        cursor = next_cursor
    fail("voice_pagination_limit")


def models(transport, credential):
    """Return provider model metadata from the fixed read-only route."""
    value = transport.elevenlabs_json("GET", "/v1/models", credential=_credential(credential))
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        fail("malformed_model_list")
    return value


def validate_eligibility(plan, transport, credential):
    """Check selected voices, model, languages and conservative documented limits."""
    available_voices = {item["voice_id"]: item for item in voices(transport, credential)}
    selected = {line["voice_id"] for line in plan["lines"]}
    if not selected <= available_voices.keys():
        fail("selected_voice_unavailable")
    available_models = models(transport, credential)
    matches = [item for item in available_models if item.get("model_id") == plan["model_id"]]
    if len(matches) != 1:
        fail("selected_model_unavailable")
    model = matches[0]
    if model.get("can_do_text_to_speech") is not True:
        fail("model_text_to_speech_denied")
    languages = model.get("languages")
    if not isinstance(languages, list) or any(not isinstance(item, dict) or not isinstance(item.get("language_id"), str) for item in languages):
        fail("malformed_model_languages")
    supported = {item["language_id"].lower() for item in languages}
    if any(line["locale"].split("-", 1)[0].lower() not in supported for line in plan["lines"]):
        fail("model_language_unsupported")
    if any(line["voice_settings"].get("use_speaker_boost") is True for line in plan["lines"]):
        if model.get("can_use_speaker_boost") is not True:
            fail("model_speaker_boost_denied")
    limit_fields = ("max_characters_request_free_user", "max_characters_request_subscribed_user",
                    "maximum_text_length_per_request")
    limits = [model.get(name) for name in limit_fields]
    positive = [value for value in limits if type(value) is int and value > 0]
    if not positive:
        fail("model_character_limit_unavailable")
    limit = min(positive)
    if any(len(line["text"]) > limit for line in plan["lines"]):
        fail("model_character_limit_exceeded")
    return {"model_id": plan["model_id"], "character_limit": limit,
            "voice_ids": sorted(selected), "languages": sorted(supported)}


def generate(line, transport, credential, *, deadline=None):
    """Perform exactly one synchronous billed conversion for an already-validated line."""
    path = ("/v1/text-to-speech/" + quote(line["voice_id"], safe="")
            + "?output_format=wav_24000")
    body = {"text": line["text"], "model_id": line["model_id"],
            "voice_settings": dict(line["voice_settings"])}
    return transport.elevenlabs_audio(path, body=body, credential=_credential(credential), deadline=deadline)
