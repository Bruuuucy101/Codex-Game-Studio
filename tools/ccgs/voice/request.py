"""Strict offline planning for the initial ElevenLabs NPC voice contract."""
import re

from ..assets.request import (REQUEST_LIMIT, SOURCE_LIMIT, canonical, check_root,
                              fail, identifier, object_fields, read_file, sha256,
                              state_path, strict_json, string)

LOCALE = re.compile(r"[A-Za-z]{2,3}(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}|[0-9]{3}))?\Z")
VOICE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}\Z")
KEY = re.compile(r"dialogue\.[A-Za-z0-9_.-]{1,240}\Z")
PLACEHOLDER = re.compile(r"\{[^{}\n]+\}")


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        fail("invalid_voice_setting")
    return value


def _voice_settings(value):
    object_fields(value, ("stability", "similarity_boost"), ("use_speaker_boost",))
    result = {"stability": _number(value["stability"]),
              "similarity_boost": _number(value["similarity_boost"])}
    if "use_speaker_boost" in value:
        if type(value["use_speaker_boost"]) is not bool:
            fail("invalid_speaker_boost")
        result["use_speaker_boost"] = value["use_speaker_boost"]
    return result


def _source_inputs(root, paths, standalone):
    if (not isinstance(paths, list) or len(paths) > 32 or
            any(not isinstance(path, str) for path in paths) or len(set(paths)) != len(paths)):
        fail("invalid_source_files")
    inputs = []
    for path in paths:
        raw = read_file(root, path, SOURCE_LIMIT)
        inputs.append({"path": path, "sha256": sha256(raw), "size": len(raw)})
    if not standalone:
        narrative = any(path.startswith(("design/narrative/", "production/localization/")) for path in paths)
        strings = any(path.startswith("assets/data/strings/") for path in paths)
        if not narrative or not strings:
            fail("canonical_voice_sources_required")
    return sorted(inputs, key=lambda item: item["path"])


def prepare_request(root, state_dir, request_path):
    """Read a project-local request and return a deterministic plan without writes or network."""
    root = check_root(root)
    state_path(root, state_dir)
    return prepare_value(root, state_dir, strict_json(read_file(root, request_path, REQUEST_LIMIT)))


def prepare_value(root, state_dir, value):
    """Validate an already-decoded request value without writes or network."""
    root = check_root(root)
    state_path(root, state_dir)
    object_fields(value,
                  ("schema_version", "provider", "model_id", "output_format", "source_files",
                   "rights_note", "npcs", "lines"),
                  ("standalone", "generation_revision"))
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        fail("unsupported_schema_version")
    if value["provider"] != "elevenlabs":
        fail("unsupported_voice_provider")
    if value["model_id"] != "eleven_multilingual_v2":
        fail("unsupported_voice_model")
    if value["output_format"] != "wav_24000":
        fail("unsupported_voice_output_format")
    standalone = value.get("standalone", False)
    if type(standalone) is not bool:
        fail("standalone_must_be_boolean")
    string(value["rights_note"], 4000, 0)
    generation_revision = value.get("generation_revision")
    if generation_revision is not None:
        string(generation_revision, 128)
    inputs = _source_inputs(root, value["source_files"], standalone)

    if not isinstance(value["npcs"], list) or not 1 <= len(value["npcs"]) <= 100:
        fail("invalid_npcs")
    npcs = {}
    voices = set()
    normalized_npcs = []
    for npc in value["npcs"]:
        object_fields(npc, ("id", "voice_id", "voice_settings"))
        npc_id = identifier(npc["id"])
        if npc_id in npcs:
            fail("duplicate_npc_id")
        if not isinstance(npc["voice_id"], str) or not VOICE_ID.fullmatch(npc["voice_id"]):
            fail("invalid_voice_id")
        if npc["voice_id"] in voices:
            fail("duplicate_voice_id")
        settings = _voice_settings(npc["voice_settings"])
        normalized = {"id": npc_id, "voice_id": npc["voice_id"], "voice_settings": settings}
        npcs[npc_id] = normalized
        voices.add(npc["voice_id"])
        normalized_npcs.append(normalized)

    if not isinstance(value["lines"], list) or not 1 <= len(value["lines"]) <= 200:
        fail("invalid_voice_lines")
    seen_keys = set()
    seen_pairs = set()
    lines = []
    total_characters = 0
    for line in value["lines"]:
        object_fields(line, ("key", "npc_id", "locale", "text", "direction_notes"))
        if not isinstance(line["key"], str) or not KEY.fullmatch(line["key"]):
            fail("invalid_dialogue_key")
        if line["key"] in seen_keys:
            fail("duplicate_dialogue_key")
        line_npc_id = identifier(line["npc_id"])
        if line_npc_id not in npcs:
            fail("unknown_npc_id")
        if not isinstance(line["locale"], str) or not LOCALE.fullmatch(line["locale"]):
            fail("invalid_locale")
        pair = (line["key"], line["locale"])
        if pair in seen_pairs:
            fail("duplicate_dialogue_locale")
        text = string(line["text"], 2000)
        total_characters += len(text)
        if total_characters > 200000:
            fail("voice_text_total_limit")
        if PLACEHOLDER.search(text):
            fail("unresolved_dialogue_placeholder")
        notes = string(line["direction_notes"], 2000, 0)
        npc = npcs[line_npc_id]
        identity = {
            "schema_version": 1,
            "provider": "elevenlabs",
            "model_id": value["model_id"],
            "output_format": value["output_format"],
            "npc_id": line_npc_id,
            "voice_id": npc["voice_id"],
            "voice_settings": npc["voice_settings"],
            "key": line["key"],
            "locale": line["locale"],
            "text": text,
        }
        if generation_revision is not None:
            identity["generation_revision"] = generation_revision
        request_hash = sha256(canonical(identity))
        prefix = re.sub(r"[^A-Za-z0-9]+", "-", line["key"]).strip("-")[:48] or "dialogue"
        output_path = f"assets/audio/vo/{line['locale']}/{prefix}-{request_hash}.wav"
        operation_id = (re.sub(r"[^A-Za-z0-9_-]+", "-", line["npc_id"] + "-" + prefix)[:30]
                        + "-" + request_hash)
        lines.append(dict(identity, direction_notes=notes, request_hash=request_hash,
                          operation_id=operation_id, output_path=output_path))
        seen_keys.add(line["key"])
        seen_pairs.add(pair)

    source_revision = sha256(canonical(inputs))
    normalized_request = {
        "schema_version": 1, "provider": "elevenlabs", "model_id": value["model_id"],
        "output_format": value["output_format"], "source_files": list(value["source_files"]),
        "rights_note": value["rights_note"], "standalone": standalone,
        "npcs": normalized_npcs,
        "lines": [{key: item[key] for key in ("key", "npc_id", "locale", "text", "direction_notes")}
                  for item in lines],
    }
    if generation_revision is not None:
        normalized_request["generation_revision"] = generation_revision
    plan = {"schema_version": 1, "request": normalized_request, "model_id": value["model_id"],
            "output_format": value["output_format"], "inputs": inputs,
            "source_revision": source_revision, "lines": lines}
    plan["batch_hash"] = sha256(canonical(plan))
    return plan


def verify_fresh(root, plan):
    """Verify exact source bytes still match the offline plan."""
    for item in plan["inputs"]:
        raw = read_file(root, item["path"], SOURCE_LIMIT)
        if len(raw) != item["size"] or sha256(raw) != item["sha256"]:
            fail("source_changed_since_plan")
