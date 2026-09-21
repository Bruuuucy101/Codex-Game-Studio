# Maintaining reviewed upstream source patches

The original `.codex/upstream-lock.json` remains the baseline for the pinned
upstream commit. Do not regenerate or reset it to make source changes pass.
Record deliberate, reviewed corrections in `.codex/upstream-patches.json` and
regenerate the Codex adapters from the corrected original source.

## Verification modes

- `python3 tools/ccgs_codex.py check` checks generated adapter integrity.
- `python3 tools/ccgs_codex.py check --strict-upstream` additionally requires
  every locked source to match its original SHA256 or its exact reviewed patch
  SHA256. Unrecorded edits and stale approved hashes fail.
- `python3 tools/ccgs_codex.py check --pristine-upstream` additionally requires
  byte equality with every original locked source. Reviewed changes fail this
  mode. If both flags are supplied, the pristine requirement applies.
- `python3 tools/ccgs_codex.py doctor` reports `upstream_drift` for pinned or
  reviewed integrity and `upstream_pristine_drift` for original byte equality.
  These reports are separate from its structural status and exit code. Doctor
  does not certify hook trust, review quality, or game-engine behavior.

An absent patch ledger means no reviewed exceptions, preserving verification
for existing pristine checkouts. A present ledger must be valid even when all
source files currently match the original baseline. Verification never enrolls
changes or writes either provenance file.

## Recording a correction

1. Review the inherited defect and the exact proposed source diff. Keep the
   original workflows, roles, engine branches, and review modes available.
2. Confirm the source path exists in the original lock's `files` dictionary.
   Copy its digest unchanged to `original_sha256`. Copy the lock's `commit`
   field to the ledger's top-level `baseline_commit`.
3. Apply and test the correction. Compute the corrected file's SHA256 locally,
   for example with `shasum -a 256 .claude/skills/example/SKILL.md`.
4. Add one patch record with that exact `patched_sha256`, the issue URL(s), and
   a rationale explaining the correction and review evidence. Never add a
   second record for the same path. When another reviewed correction changes
   the same file, update its patched hash and rationale while preserving the
   original hash and relevant issue links.
5. Run `python3 tools/ccgs_codex.py generate`, the relevant regression tests,
   `python3 -m unittest discover -s tests/codex_adapter -v`, and
   `python3 tools/ccgs_codex.py check --strict-upstream`. Inspect the source,
   ledger, and generated diffs together before committing them. A pristine
   check should report the intentionally changed baseline paths.

The schema is version 1:

```json
{
  "schema_version": 1,
  "baseline_commit": "<the original lock's 40-character commit>",
  "patches": [
    {
      "path": ".claude/skills/example/SKILL.md",
      "original_sha256": "<the original lock's 64-character SHA256>",
      "patched_sha256": "<the reviewed file's 64-character SHA256>",
      "issue_urls": ["https://github.com/owner/repository/issues/123"],
      "rationale": "What was corrected, why, and how it was reviewed."
    }
  ]
}
```

Replace placeholders with real values; this example is not a valid record.
Digests must contain hexadecimal characters. Issue links must be nonempty
HTTP(S) URLs, and the rationale must be nonempty text. Paths must be canonical
relative POSIX paths already in the baseline. Absolute paths, traversal,
backslashes, repeated separators, and symlink sources or parents are rejected.
Missing files always fail, including files with a reviewed record.

The ledger is review metadata, not a signature or proof of independent review.
Protect and review it together with the unchanged baseline lock in version
control. It covers locked upstream files; added files and generated adapter
integrity are separate concerns. Returning a file to original bytes is allowed;
remove an obsolete record deliberately during review, never by resetting the
baseline.

## Updating an adopted Codex release

Record the **adopted Codex release/commit** independently from
`.codex/upstream-lock.json.commit`. The latter is the original Claude source
baseline, not the installed Codex version: several Codex releases can retain
that same lock while changing reviewed patches, runtime code and generated
adapters. A Codex-to-Codex comparison must use the old adopted Codex commit and
the reviewed new Codex commit. Do not substitute the original source pin.

Back up local work and untracked assets, inspect the full incoming release diff,
and validate in a clean review worktree. A clone with shared history can follow
[UPGRADING.md Strategy A](../../UPGRADING.md#strategy-a--ordinary-shared-history-branch-update).
An adopted copy with separate history needs the selective three-version process
in Strategy B, using its **Codex** release baseline/target and reviewed Codex
paths. Include mutually dependent runtime, source, ledger and generated changes
in the review. Merge local wrapper/configuration customizations deliberately;
do not regenerate over unrecorded wrapper edits. When the old release is
unknown, recover it from adoption records or original files before automated
import, or use Strategy C and record the provenance uncertainty.

## Importing a selected Claude upstream correction

Use the Claude baseline-to-target source diff in
[UPGRADING.md Strategy B](../../UPGRADING.md#strategy-b--selective-baseline-aware-template-import),
then compare it with the current canonical source, including our reviewed
patches. The original lock identifies the original source snapshot; a later
selective import may have a separately recorded per-change baseline. Neither
an upstream target nor a successful patch application authorizes replacing the
lock. Never blanket merge the Claude repository into this adapter or overwrite
customized `.claude` files. Preserve `.codex`, `.agents/skills` wrappers, runtime,
and game content outside the upstream source allowlist.

Review overlapping local changes and active patch records, apply the minimal
correction, and record its exact source hash using the procedure above. Keep
unrelated patch records unchanged. Regenerate only after preserving any local
adapter customizations in a reviewable form; generator output is not a merge
strategy for custom wrappers. Run focused regressions, the full adapter suite,
`check --strict-upstream`, and the game's relevant build/tests before promoting
the review branch. Adapter checks alone do not prove the game still runs.
