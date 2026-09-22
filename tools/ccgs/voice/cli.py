"""NPC voice command boundary; preview is the default and endpoints stay fixed."""
import argparse
import json
import os

from ..assets.request import check_root, redact


def main(root, argv=None, *, transport=None):
    parser = argparse.ArgumentParser(prog="ccgs voice", description="Optional durable NPC voice generation; preview by default.")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("plan", "bake", "status", "collect"):
        child = commands.add_parser(command)
        child.add_argument("--request", required=True)
        if command in ("bake", "collect"):
            child.add_argument("--write", action="store_true")
    commands.add_parser("voices")
    commands.add_parser("models")
    verify = commands.add_parser("verify")
    verify.add_argument("--manifest", required=True)
    args = parser.parse_args(argv)
    try:
        from ..assets.http import Transport
        from . import batch
        from .elevenlabs import models, voices
        from .request import prepare_request
        root = check_root(root)
        state_dir = root / ".ccgs-assets"
        if args.command == "plan":
            result = prepare_request(root, state_dir, args.request)
        elif args.command == "bake":
            result = batch.bake(root, state_dir, args.request, write=args.write, transport=transport)
        elif args.command == "status":
            result = batch.status(root, state_dir, args.request)
        elif args.command == "collect":
            result = batch.collect(root, state_dir, args.request, write=args.write)
        elif args.command == "verify":
            result = batch.verify_manifest(root, args.manifest)
        else:
            credential = os.environ.get("ELEVENLABS_API_KEY")
            provider = transport or Transport()
            result = voices(provider, credential) if args.command == "voices" else models(provider, credential)
        print(json.dumps(redact(result), ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except ValueError as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}))
        return 1
    except (OSError, KeyError, TypeError, RecursionError):
        print(json.dumps({"status": "FAIL", "error": "invalid_or_unavailable_local_state"}))
        return 1
