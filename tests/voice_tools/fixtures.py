"""Credential-free voice fixtures using real loopback HTTP and WAV bytes."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))


def wav(frames=2400, channels=1, rate=24000, width=2, sample=b"\x01\x00"):
    stream = io.BytesIO()
    with wave.open(stream, "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(width)
        output.setframerate(rate)
        output.writeframes(sample * frames * channels)
    return stream.getvalue()


def model(**changes):
    value = {
        "model_id": "eleven_multilingual_v2",
        "name": "Eleven Multilingual v2",
        "can_do_text_to_speech": True,
        "can_use_speaker_boost": True,
        "max_characters_request_free_user": 2500,
        "max_characters_request_subscribed_user": 5000,
        "maximum_text_length_per_request": 1000000,
        "languages": [{"language_id": "en", "name": "English"}],
    }
    value.update(changes)
    return value


def voice(voice_id, name):
    return {"voice_id": voice_id, "name": name, "category": "premade",
            "labels": {}, "available_for_tiers": [], "high_quality_base_model_ids": []}


def request(root, *, standalone=True, lines=None, npcs=None, source_files=None, **changes):
    value = {
        "schema_version": 1,
        "provider": "elevenlabs",
        "model_id": "eleven_multilingual_v2",
        "output_format": "wav_24000",
        "source_files": [] if source_files is None else source_files,
        "rights_note": "Synthetic fixture; no live rights or quality claim.",
        "standalone": standalone,
        "npcs": npcs or [
            {"id": "merchant", "voice_id": "voice-merchant",
             "voice_settings": {"stability": 0.4, "similarity_boost": 0.7, "use_speaker_boost": True}},
            {"id": "guard", "voice_id": "voice-guard",
             "voice_settings": {"stability": 0.6, "similarity_boost": 0.8}},
        ],
        "lines": lines or [
            {"key": "dialogue.npc.merchant.greeting", "npc_id": "merchant", "locale": "en-US",
             "text": "Welcome, traveller.", "direction_notes": "Warm but cautious."},
            {"key": "dialogue.npc.guard.warning", "npc_id": "guard", "locale": "en-US",
             "text": "Keep moving.", "direction_notes": "Firm and clipped."},
        ],
    }
    value.update(changes)
    path = root / "voice-request.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


class Server:
    def __init__(self):
        self.routes = {}
        self.calls = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.reply()

            def do_POST(self):
                self.reply()

            def reply(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                owner.calls.append((self.command, self.path, dict(self.headers), body))
                route = owner.routes.get((self.command, self.path), (404, {"detail": "private provider body"}, {}))
                if isinstance(route, list):
                    route = route.pop(0)
                if callable(route):
                    route(self)
                    return
                status, value, headers = route
                raw = value if isinstance(value, bytes) else json.dumps(value).encode()
                self.send_response(status)
                for key, item in headers.items():
                    self.send_header(key, item)
                if "Content-Length" not in headers:
                    self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                try:
                    self.wfile.write(raw)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        self.http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.http.daemon_threads = True
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.origin = "http://127.0.0.1:%d" % self.http.server_port

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()

    def transport(self, **kwargs):
        from ccgs.assets.http import Transport
        return Transport(origin_map={"https://api.elevenlabs.io": self.origin}, **kwargs)

    def eligible(self):
        self.routes["GET", "/v2/voices?page_size=100&include_total_count=false"] = (
            200, {"voices": [voice("voice-merchant", "Merchant"), voice("voice-guard", "Guard")],
                  "has_more": False, "total_count": 2, "next_page_token": None}, {})
        self.routes["GET", "/v1/models"] = (200, [model()], {})
        self.routes["POST", "/v1/text-to-speech/voice-merchant?output_format=wav_24000"] = (200, wav(sample=b"\x01\x00"), {})
        self.routes["POST", "/v1/text-to-speech/voice-guard?output_format=wav_24000"] = (200, wav(sample=b"\x02\x00"), {})


def cli(root, *args, server=None, extra_env=None):
    env = {key: value for key, value in os.environ.items() if key != "ELEVENLABS_API_KEY"}
    env["PYTHONPATH"] = str(REPO / "tools")
    if extra_env:
        env.update(extra_env)
    if server:
        code = ("from ccgs.assets.http import Transport; from ccgs.voice.cli import main; "
                "from pathlib import Path; import sys; "
                "sys.exit(main(Path(sys.argv[1]), sys.argv[2:], transport=Transport(origin_map="
                + repr({"https://api.elevenlabs.io": server.origin}) + ")))" )
        command = [sys.executable, "-c", code, str(root), *args]
    else:
        command = [sys.executable, str(REPO / "tools/ccgs_codex.py"), "--root", str(root), "voice", *args]
    return subprocess.run(command, env=env, text=True, capture_output=True, timeout=20)
