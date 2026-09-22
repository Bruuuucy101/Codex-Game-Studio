#!/usr/bin/env python3
"""Engine-neutral loader acceptance for a collected CCGS NPC voice manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import wave


def audio_path(root, value):
    """Resolve one project-relative audio path while rejecting every original symlink."""
    if not isinstance(value, str):
        raise ValueError("unsafe audio path")
    relative = Path(value)
    if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
        raise ValueError("unsafe audio path")
    path = root
    try:
        for part in relative.parts:
            path = path / part
            if path.is_symlink():
                raise ValueError("unsafe audio path")
        resolved = path.resolve(strict=True)
    except OSError:
        raise ValueError("unsafe audio path") from None
    if not resolved.is_relative_to(root):
        raise ValueError("unsafe audio path")
    return path


def load(root, manifest):
    root = Path(root).resolve()
    value = json.loads(Path(manifest).resolve().read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or not isinstance(value.get("lines"), list):
        raise ValueError("invalid manifest")
    decoded = []
    for line in value["lines"]:
        path = audio_path(root, line["path"])
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != line["sha256"]:
            raise ValueError("audio hash mismatch")
        with wave.open(str(path), "rb") as stream:
            properties = (stream.getcomptype(), stream.getframerate(),
                          stream.getsampwidth(), stream.getnchannels())
            if properties not in (("NONE", 24000, 2, 1), ("NONE", 24000, 2, 2)):
                raise ValueError("unsupported PCM")
            frames = stream.getnframes()
            if frames <= 0:
                raise ValueError("empty PCM")
            decoded_pcm = stream.readframes(frames)
            expected_bytes = frames * stream.getsampwidth() * stream.getnchannels()
            if len(decoded_pcm) != expected_bytes or stream.readframes(1):
                raise ValueError("incomplete PCM")
        decoded.append({"key": line["key"], "locale": line["locale"],
                        "npc_id": line["npc_id"], "path": line["path"]})
    return {"status": "loader_acceptance", "decoded_lines": len(decoded),
            "npcs": sorted({line["npc_id"] for line in decoded}), "lines": decoded}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    print(json.dumps(load(args.root, args.manifest), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
