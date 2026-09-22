# Optional NPC voice production

The NPC voice tool turns reviewed dialogue into durable 24 kHz, 16-bit PCM WAV
files and an immutable playback manifest. It extends the existing
`localize vo-pipeline` process; scan, recording scripts, validation and integration
remain the localization workflow's responsibility. Runtime synthesis, cloning,
timestamps, pronunciation dictionaries, style, speed and seed are outside this
initial contract.

The default is offline and read-only:

```sh
python3 tools/ccgs_codex.py voice plan --request production/localization/npc-voice.json
python3 tools/ccgs_codex.py voice bake --request production/localization/npc-voice.json
python3 tools/ccgs_codex.py voice status --request production/localization/npc-voice.json
python3 tools/ccgs_codex.py voice collect --request production/localization/npc-voice.json
```

`plan` and default `bake` do not create state or contact a provider. `status` reads
only local receipts. Default `collect` verifies a complete batch and previews its
manifest path. The explicit paid/write steps are:

```sh
ELEVENLABS_API_KEY=... python3 tools/ccgs_codex.py voice bake --request production/localization/npc-voice.json --write
python3 tools/ccgs_codex.py voice collect --request production/localization/npc-voice.json --write
python3 tools/ccgs_codex.py voice verify --manifest assets/audio/vo/manifests/HASH.json
```

Credentials come only from `ELEVENLABS_API_KEY` and are sent only as `xi-api-key`
to fixed `https://api.elevenlabs.io` routes. They are not persisted. `voice voices`
and `voice models` are explicit remote read-only commands. There is no endpoint,
host or credential-file option.

Schema 1 supports only `provider: elevenlabs`,
`model_id: eleven_multilingual_v2`, and `output_format: wav_24000`. Every NPC has a
stable distinct voice ID and explicit stability/similarity settings. Lines use a
`dialogue.*` key, NPC ID, conservative BCP-47 locale, final exact spoken text and
direction notes. Unresolved `{placeholders}` are rejected. `generation_revision`
is the optional explicit nonce for a deliberately paid new take.

Canonical requests list real files from `design/narrative/` or
`production/localization/` and from `assets/data/strings/`. The workflow checks the
selected key, locale and exact text against those sources before writing a request.
The CLI pins full raw source hashes but cannot infer arbitrary string-table schemas.
Use `standalone: true` only for a deliberate source-free fixture or isolated tool.

Each line records durable intent before its one synchronous POST. A lost response
becomes `submission_unknown` and is never retried automatically. Failed and uncertain
lines remain blocked while successful lines remain usable. Repeating unchanged input
reuses verified staged bytes. A source-only change creates a new batch manifest while
reusing unchanged audio and retaining its original generation provenance.

Before any paid conversion, bake checks every public WAV and immutable-manifest
destination, hard-link capability, and every deterministic private receipt/stage/lock
path for all lines. A foreign manifest, unsafe ancestor, orphan stage or later-line
private blocker stops the batch with zero POSTs. A previously completed manifest is
reusable only when its private stage and public destination still prove shared-inode
ownership and the expected hash.

Collection validates the full RIFF/WAVE structure, PCM codec, sample rate, sample
width, channels, frame completeness, 64 MiB limit and ten-minute limit. It publishes
owned WAV files with create-only hard links, retains partial publication on a later
failure, and publishes the complete manifest last. Existing unrelated or changed files
are never overwritten or adopted by hash alone. Private state lives under ignored
`.ccgs-assets/voice/` with restrictive permissions.

The engine-neutral loader in `examples/npc-voice/playback_manifest_loader.py` proves
only that a consumer resolves, hashes and decodes selected files. Generated WAV is
not listening approval, and loader acceptance is not engine import. Availability does
not prove billing entitlement, commercial rights, perceptual quality, latency or that
two voices sound distinct. Those require a real account, human listening and actual
engine playback.

Without a configured service, keep plan/status offline and use recorded audio through
`localize vo-pipeline script`, `validate`, and `integrate`. WAV-only commands use
Python 3.10+ standard library and do not import Pillow.

Provider success does not bypass localization completion. After listening approval,
manifest verification and proved engine import, run the original `localize vo-pipeline
validate` and `integrate` checks. Treat the immutable manifest's `(locale,key)` to
hashed WAV path entries as the recording/key map when finding missing or extra audio,
checking filenames and resolving code references. Missing source, runtime, key-map or
reference evidence leaves localization validation/integration blocked.
