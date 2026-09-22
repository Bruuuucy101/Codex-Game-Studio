"""Per-line durable voice generation, collection and manifest verification."""
import os
from pathlib import Path
import stat
import time

from ..assets import artifacts
from ..assets.http import Transport, TransportError
from ..assets.jobs import private_lock, write_private_bytes, write_private_json
from ..assets.request import (ARTIFACT_LIMIT, JSON_LIMIT, canonical, check_root, fail,
                              parent_fd, read_file, sha256, state_path, strict_json)
from .audio import WAV_LIMIT, validate_wav
from .elevenlabs import generate, validate_eligibility
from .request import prepare_request, verify_fresh


def _line_dir(line):
    return ".ccgs-assets/voice/lines/" + line["operation_id"]


def _receipt_path(line):
    return _line_dir(line) + "/receipt.json"


def _stage_path(line):
    return _line_dir(line) + "/audio.wav"


def _load_receipt(root, line):
    path = Path(root) / _receipt_path(line)
    if not path.exists() and not path.is_symlink():
        return None
    value = strict_json(read_file(root, _receipt_path(line), JSON_LIMIT, private=True), JSON_LIMIT)
    if (not isinstance(value, dict) or value.get("schema_version") != 1 or
            value.get("operation_id") != line["operation_id"] or
            value.get("request_hash") != line["request_hash"]):
        fail("voice_receipt_identity_mismatch")
    return value


def _save_receipt(root, state_dir, line, receipt):
    state_path(root, state_dir)
    write_private_json(root, _receipt_path(line), receipt)


def _summary(plan, receipts, status):
    lines = []
    for line, receipt in zip(plan["lines"], receipts):
        item = {"key": line["key"], "locale": line["locale"], "npc_id": line["npc_id"],
                "request_hash": line["request_hash"], "status": receipt.get("status", "missing")}
        if "generation_source_revision" in receipt:
            item["generation_source_revision"] = receipt["generation_source_revision"]
        if receipt.get("diagnostic"):
            item["diagnostic"] = receipt["diagnostic"]
        if item["status"] in ("submitting", "submission_unknown"):
            item["status"] = "submission_unknown"
            item["next"] = "Inspect provider history/support; automatic resubmission is blocked."
        lines.append(item)
    return {"schema_version": 1, "status": status, "batch_hash": plan["batch_hash"],
            "source_revision": plan["source_revision"], "lines": lines}


def _credential(value):
    value = value if value is not None else os.environ.get("ELEVENLABS_API_KEY")
    if not isinstance(value, str) or not value or "\r" in value or "\n" in value:
        fail("provider_credential_unavailable")
    return value


def _recover_stage(root, state_dir, line, receipt):
    """Recover only the durable-result-before-generated crash interval; never resubmit."""
    stage = Path(root) / _stage_path(line)
    if receipt["status"] != "submitting" or not stage.exists() or stage.is_symlink():
        return receipt
    raw = read_file(root, _stage_path(line), WAV_LIMIT, private=True)
    properties = validate_wav(raw)
    receipt.update(status="generated", staged_path=_stage_path(line), sha256=properties["sha256"],
                   audio=properties, diagnostic=None)
    _save_receipt(root, state_dir, line, receipt)
    return receipt


def _owned_output(root, line, receipt):
    return (receipt is not None and receipt.get("staged_path") == _stage_path(line)
            and isinstance(receipt.get("sha256"), str)
            and artifacts.prove_owned(root, line["output_path"],
                                      Path(root) / receipt["staged_path"], receipt["sha256"]))


def _preflight_outputs(root, plan, receipts, *, include_manifest=False):
    indexed = {line["output_path"]: (line, receipt) for line, receipt in zip(plan["lines"], receipts)}
    outputs = [{"path": line["output_path"]} for line in plan["lines"]]
    if include_manifest:
        outputs.append({"path": _manifest_path(plan)})

    def allow_owned(out):
        if out["path"] == _manifest_path(plan):
            staged = _manifest_stage(plan)
            path = Path(root) / staged
            if not path.is_file() or path.is_symlink():
                return False
            raw = read_file(root, staged, JSON_LIMIT, private=True)
            return artifacts.prove_owned(root, out["path"], Path(root) / staged, sha256(raw))
        line, receipt = indexed[out["path"]]
        return _owned_output(root, line, receipt)

    artifacts.preflight(root, outputs, allow_owned=allow_owned)
    return outputs


def _private_leaf(root, path):
    """Create/check private parents and return a safe existing leaf, if any."""
    with parent_fd(root, path, create=True, mode=0o700, private=True) as (fd, name):
        try:
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            return None
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
            fail("unsafe_private_file")
        return info


def _preflight_private(root, plan, receipts):
    """Check every deterministic journal/stage path before any billed submission."""
    for line, receipt in zip(plan["lines"], receipts):
        receipt_exists = receipt.get("status") != "missing"
        receipt_info = _private_leaf(root, _receipt_path(line))
        if bool(receipt_info) != receipt_exists:
            fail("voice_receipt_changed_during_preflight")
        stage_info = _private_leaf(root, _stage_path(line))
        _private_leaf(root, _line_dir(line) + "/lock")
        if stage_info is None:
            if receipt_exists and receipt.get("status") in ("generated", "collected"):
                fail("voice_stage_missing")
            continue
        if not receipt_exists:
            fail("voice_stage_without_receipt")
        if receipt.get("status") not in ("submitting", "generated", "collected"):
            fail("voice_stage_receipt_state_mismatch")
        raw = read_file(root, _stage_path(line), WAV_LIMIT, private=True)
        properties = validate_wav(raw)
        if receipt.get("status") in ("generated", "collected"):
            if (receipt.get("staged_path") != _stage_path(line) or
                    receipt.get("sha256") != properties["sha256"] or
                    receipt.get("audio") != properties):
                fail("voice_stage_hash_or_pcm_mismatch")
    manifest_stage = _manifest_stage(plan)
    if _private_leaf(root, manifest_stage) is not None:
        public_manifest = Path(root) / _manifest_path(plan)
        if not public_manifest.exists() and any(receipt.get("status") == "missing" for receipt in receipts):
            fail("voice_manifest_stage_without_complete_batch")


def bake(root, state_dir, request_path, *, write=False, transport=None, credential=None):
    """Plan by default; with write, check eligibility and submit only missing lines once."""
    root = check_root(root)
    state_path(root, state_dir)
    plan = prepare_request(root, state_dir, request_path)
    receipts = [_load_receipt(root, line) or {"status": "missing"} for line in plan["lines"]]
    if not write:
        return _summary(plan, receipts, "planned")
    credential = _credential(credential)
    transport = transport or Transport()
    outputs = _preflight_outputs(root, plan, receipts, include_manifest=True)
    # Establish the private voice subtree through the shared no-follow writer
    # before the shared hard-link capability probe creates its temporary inode.
    write_private_bytes(root, ".ccgs-assets/voice/schema", b"1", exclusive=True)
    _preflight_private(root, plan, receipts)
    artifacts.link_capability(root, state_dir, outputs)
    validate_eligibility(plan, transport, credential)
    final = []
    for line in plan["lines"]:
        verify_fresh(root, plan)
        lock_path = _line_dir(line) + "/lock"
        try:
            with private_lock(root, state_dir, lock_path):
                receipt = _load_receipt(root, line)
                if receipt is not None:
                    receipt = _recover_stage(root, state_dir, line, receipt)
                    if receipt["status"] in ("generated", "collected"):
                        raw = read_file(root, receipt["staged_path"], WAV_LIMIT, private=True)
                        properties = validate_wav(raw)
                        if properties["sha256"] != receipt["sha256"]:
                            fail("voice_stage_hash_mismatch")
                    final.append(receipt)
                    continue
                receipt = {
                    "schema_version": 1, "operation_id": line["operation_id"],
                    "request_hash": line["request_hash"], "status": "submitting",
                    "provider": "elevenlabs", "model_id": line["model_id"],
                    "voice_id": line["voice_id"], "npc_id": line["npc_id"],
                    "key": line["key"], "locale": line["locale"],
                    "generation_source_revision": plan["source_revision"],
                    "generation_sources": plan["inputs"], "staged_path": _stage_path(line),
                    "sha256": None, "audio": None, "published_path": None,
                    "diagnostic": None,
                }
                _save_receipt(root, state_dir, line, receipt)  # Durable intent before billed bytes.
                try:
                    raw = generate(line, transport, credential, deadline=time.monotonic() + 30)
                except TransportError as error:
                    receipt["status"] = ("failed" if error.category.startswith("http_") else "submission_unknown")
                    receipt["diagnostic"] = error.category
                    _save_receipt(root, state_dir, line, receipt)
                    final.append(receipt)
                    continue
                try:
                    properties = validate_wav(raw)
                except ValueError as error:
                    receipt["status"] = "failed"
                    receipt["diagnostic"] = str(error)
                    _save_receipt(root, state_dir, line, receipt)
                    final.append(receipt)
                    continue
                write_private_bytes(root, _stage_path(line), raw, exclusive=True)
                receipt.update(status="generated", sha256=properties["sha256"], audio=properties,
                               diagnostic=None)
                _save_receipt(root, state_dir, line, receipt)
                final.append(receipt)
        except ValueError as error:
            if str(error).startswith("operation_locked"):
                final.append({"status": "locked"})
            else:
                raise
    status = "generated" if all(item.get("status") in ("generated", "collected") for item in final) else "partial"
    return _summary(plan, final, status)


def status(root, state_dir, request_path):
    """Read current line receipts without provider calls or local writes."""
    root = check_root(root)
    plan = prepare_request(root, state_dir, request_path)
    receipts = [_load_receipt(root, line) or {"status": "missing"} for line in plan["lines"]]
    overall = "generated" if all(item.get("status") in ("generated", "collected") for item in receipts) else "partial"
    return _summary(plan, receipts, overall)


def _manifest_path(plan):
    return "assets/audio/vo/manifests/" + plan["batch_hash"] + ".json"


def _manifest_stage(plan):
    return ".ccgs-assets/voice/manifests/" + plan["batch_hash"] + ".json"


def _manifest(plan, receipts):
    lines = []
    for line, receipt in zip(plan["lines"], receipts):
        lines.append({
            "key": line["key"], "locale": line["locale"], "npc_id": line["npc_id"],
            "voice_id": line["voice_id"], "model_id": line["model_id"],
            "request_hash": line["request_hash"], "path": line["output_path"],
            "sha256": receipt["sha256"], "audio": receipt["audio"],
            "generation_source_revision": receipt["generation_source_revision"],
            "generation_sources": receipt["generation_sources"],
            "review": {"listening": "pending", "engine_import": "pending"},
        })
    return {"schema_version": 1, "provider": "elevenlabs", "batch_hash": plan["batch_hash"],
            "source_revision": plan["source_revision"], "sources": plan["inputs"],
            "rights_note": plan["request"]["rights_note"], "lines": lines}


def collect(root, state_dir, request_path, *, write=False):
    """Publish verified owned WAV files and then one immutable complete manifest."""
    root = check_root(root)
    plan = prepare_request(root, state_dir, request_path)
    receipts = [_load_receipt(root, line) for line in plan["lines"]]
    if any(receipt is None or receipt.get("status") not in ("generated", "collected") for receipt in receipts):
        fail("voice_batch_incomplete")
    for line, receipt in zip(plan["lines"], receipts):
        raw = read_file(root, receipt["staged_path"], WAV_LIMIT, private=True)
        properties = validate_wav(raw)
        if properties != receipt["audio"] or properties["sha256"] != receipt["sha256"]:
            fail("voice_stage_hash_or_pcm_mismatch")
    verify_fresh(root, plan)
    manifest = _manifest(plan, receipts)
    manifest_raw = canonical(manifest)
    if len(manifest_raw) > JSON_LIMIT:
        fail("voice_manifest_size_limit")
    result = {"schema_version": 1, "status": "collectable", "manifest": _manifest_path(plan),
              "batch_hash": plan["batch_hash"], "line_count": len(receipts)}
    if not write:
        return result
    outputs = _preflight_outputs(root, plan, receipts, include_manifest=True)
    artifacts.link_capability(root, state_dir, outputs)
    verify_fresh(root, plan)
    for line, receipt in zip(plan["lines"], receipts):
        artifacts.publish(root, line["output_path"], Path(root) / receipt["staged_path"], receipt["sha256"])
        receipt["status"] = "collected"
        receipt["published_path"] = line["output_path"]
        _save_receipt(root, state_dir, line, receipt)
    verify_fresh(root, plan)
    write_private_bytes(root, _manifest_stage(plan), manifest_raw, exclusive=True)
    verify_fresh(root, plan)
    artifacts.publish(root, _manifest_path(plan), Path(root) / _manifest_stage(plan), sha256(manifest_raw))
    result["status"] = "collected"
    return result


def verify_manifest(root, manifest_path):
    """Resolve every declared audio path and verify hash and exact PCM properties."""
    root = check_root(root)
    value = strict_json(read_file(root, manifest_path, JSON_LIMIT), JSON_LIMIT)
    if (not isinstance(value, dict) or value.get("schema_version") != 1 or
            not isinstance(value.get("lines"), list) or not value["lines"]):
        fail("invalid_voice_manifest")
    pairs = set()
    paths = set()
    for line in value["lines"]:
        required = {"key", "locale", "npc_id", "voice_id", "model_id", "request_hash",
                    "path", "sha256", "audio", "generation_source_revision",
                    "generation_sources", "review"}
        if not isinstance(line, dict) or set(line) != required:
            fail("invalid_voice_manifest_line")
        pair = (line["locale"], line["key"])
        if pair in pairs or line["path"] in paths:
            fail("duplicate_voice_manifest_entry")
        raw = read_file(root, line["path"], WAV_LIMIT)
        properties = validate_wav(raw)
        if properties["sha256"] != line["sha256"]:
            fail("voice_manifest_hash_mismatch")
        if properties != line["audio"]:
            fail("voice_manifest_pcm_mismatch")
        pairs.add(pair)
        paths.add(line["path"])
    return {"schema_version": 1, "status": "verified", "manifest": manifest_path,
            "line_count": len(value["lines"])}
