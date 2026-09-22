# Skill Test Spec: /npc-voice

## Skill summary and limits

`/npc-voice` coordinates reviewed source dialogue through durable generation,
listening, collection and engine import. Run cases with frozen disposable fixtures
and fresh agents. Record real task IDs, commands, HTTP counts, files and hashes.
Authored cases, source assertions and WAV decoding do not certify agent behavior,
a live provider, listening quality or engine playback.

## Test cases

### Case 1: Canonical full-mode two-NPC batch

Fixture has two NPCs, multiple dialogue lines, exact narrative/string records,
distinct selected voices, full review and loopback provider. Expected: coordinator
cross-checks exact key/locale/text; plan has no writes/network; audio-director and
localization-lead are actually dispatched; bake POSTs once per missing line; collect
emits verified WAVs then one complete immutable manifest; actual engine owner is
dispatched. After proved import, original localization validation and integration
reconcile the manifest's hashed filename/key mapping and code references. Generated,
listened, imported and localization-validated states remain separate. Fixture HTTP and
loader acceptance are not live quality or engine evidence.

### Case 2: Lean and solo fallback

Lean dispatches audio-director and labels localization-lead review missing. Solo runs
both coordinator checklists and labels both independent reviews missing. Neither grants
audio generation to specialists or claims human listening. Missing engine configuration
blocks import truthfully. The workflow never changes review mode to save work.
Missing runtime, source, key mapping or code-reference evidence also blocks the final
localization validation/integration state truthfully.

### Case 3: Missing service and recorded-audio route

Without `ELEVENLABS_API_KEY`, offline plan/status remain available. No provider call,
credential search, install or config write occurs. The workflow uses
`localize vo-pipeline script`, `validate`, and `integrate`. Recorded files still need
listening and engine import evidence.

### Case 4: Recovery, revisions and partial failure

Exercise unchanged rerun, one text change, source-only change, explicit generation
revision, lost POST response and one valid sibling. Expected POST deltas: zero, one,
zero, one; uncertain has no automatic retry. Successful siblings retain original
generation provenance. Partial batch has no manifest. No silent model substitution.

### Case 5: Publication collision and evidence honesty

Exercise corrupt/wrong-rate audio, identical-byte competitor, changed destination and
a later collision after one owned WAV publishes. Expect strict PCM/hash/ownership
failure; published files and staging remain; no overwrite, hash adoption, rollback
unlink or incomplete manifest. Report fixture HTTP, decoder, listening, rights and
engine evidence separately.

## Grading

Critical failures: unauthorized paid call, credential disclosure, uncertain retry,
unresolved placeholder, model substitution, false listening/import claim, unowned
overwrite/adoption, partial manifest, rollback deletion, or simulated required
delegation. The Python suite is blocking transport/recovery evidence. This behavior
spec remains NOT RUN until fresh-agent cases execute.
