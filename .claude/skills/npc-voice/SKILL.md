---
name: npc-voice
description: "Use when planning, generating, listening-reviewing, collecting, verifying, or importing stable baked NPC dialogue voices through the optional ElevenLabs workflow."
argument-hint: "plan|bake|status|collect|listen|import|verify --request PATH [--review full|lean|solo]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Bash, Task, AskUserQuestion
model: sonnet
---

# NPC Voice Production

Read `docs/codex-adapter/npc-voice.md` and `.claude/skills/localize/SKILL.md`.
The coordinator owns the evidence chain; generation, listening review and engine
import are separate states. Never claim one from another. Preserve the selected
full/lean/solo review mode. Existing authorization for a concrete paid request
persists; otherwise present the exact request and missing-line count before the
billed `bake --write` step.

## 1. Source and request gate

Apply `localize vo-pipeline scan` and `script` to real `assets/data/strings/` and
`design/narrative/` or `production/localization/` files. Record each exact
`dialogue.*` key, locale and final text; resolve placeholders before generation.
Keep direction notes separate. Select one existing provider voice ID per NPC. This
workflow never clones or creates a voice. Cross-check every request line against
the sources before writing it; the CLI does not parse arbitrary string schemas.

Use the adapter guide's schema and run:

```sh
python3 tools/ccgs_codex.py voice plan --request PATH
```

Planning is offline and no-write. Source mismatch, duplicate identity, unsupported
field/model/setting, missing rights note or placeholder blocks the batch.

## 2. Generation

If `ELEVENLABS_API_KEY` is unavailable or recorded performance is chosen, route to
`localize vo-pipeline script`, then `validate` and `integrate`. Do not install,
authenticate, change global config or invent provider evidence.

For an authorized batch, use `voice bake --request PATH --write`. Eligibility reads
voices/models first; generation submits only missing deterministic line identities.
Never retry `submission_unknown` or `failed` lines automatically. Preserve successful
siblings and their receipts. A new take requires a user-chosen `generation_revision`
and is a new paid operation. Use `voice status --request PATH` for local recovery.

## 3. Listening review by mode

Specialists review scripts and evidence; they do not synthesize or modify audio.

- **Full:** dispatch `audio-director` for NPC distinction, direction and mix review,
  and `localization-lead` for exact text, locale, pronunciation risks and key/subtitle
  alignment. Run independent tasks when possible and collect both actual results.
- **Lean:** dispatch `audio-director`; the coordinator performs the exact source/key/
  locale checklist and labels localization-lead review missing.
- **Solo:** the coordinator performs both checklists and labels both independent
  specialist reviews unavailable. Solo review is not independent approval.

A human plays every generated line and records clarity, NPC distinction, delivery,
clipping/noise and source accuracy. Decoded WAV, waveform, filename or distinct voice
IDs are not listening evidence. Failure returns to an explicit generation revision
or recorded audio.

## 4. Collection and engine import

After every requested line exists, run:

```sh
python3 tools/ccgs_codex.py voice collect --request PATH
python3 tools/ccgs_codex.py voice collect --request PATH --write
python3 tools/ccgs_codex.py voice verify --manifest MANIFEST
```

Collection publishes verified WAVs and the immutable complete manifest last. Partial
batches have no manifest. Keep partial files/staging after collision or failure;
never unlink published files as rollback.

Dispatch the actual engine owner to import the manifest and prove playback. Full/lean
use the configured engine specialist. Solo uses the coordinator only when engine work
is within its tools and still labels missing independent engine review. Missing engine
configuration/runtime blocks import truthfully; never choose an engine or assert success.

After a proved engine import, run and record the original `localize vo-pipeline validate`
and `localize vo-pipeline integrate` checks. For validation, use the immutable manifest's
`(locale,key) → hashed WAV path` mapping as the recording manifest: reconcile every source
key with its declared audio path, report missing/extra audio, and verify the hashed filename
against that mapping rather than expecting the raw key as a filename. For integration,
verify every VO code reference resolves through the same key mapping to an existing file.
Missing runtime, source, manifest/key mapping or code-reference evidence blocks
localization validation and integration truthfully; do not report the batch complete.

## 5. Final state

Report each line and batch through distinct states:

`source reviewed → generated → listening approved → manifest verified → engine imported → localization validated → localization integrated`

Include request/manifest paths, source and generation revisions, observed POST count,
review task IDs, listening/import/localization evidence and blockers. Fixtures prove transport and
decoding only. Live entitlement, rights, provider quality/latency, listening and engine
playback remain unverified unless genuinely exercised.
