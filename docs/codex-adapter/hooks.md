# CCGS hook bridge

The project registers `tools/ccgs_hooks.py EVENT` through `.codex/hooks.json`.
The bridge calls the unchanged upstream scripts with Bash, JSON on stdin, and the
repository containing the bridge as their working directory. It never executes a
shell command received in event JSON. Python 3.10+, Git and Bash are required.
The existing source scripts optionally use jq; their own fallback remains intact.

## Activation and trust

Open this repository as a Codex project. Review the project hook definitions in
`/hooks` and trust them using the host's normal review flow. Changed hook definitions
need fresh review. No adapter command edits trust stores, enables approval bypass,
auto-approves tool calls, or changes sandbox settings. Existing global/managed
hooks remain in force. Inspect the referenced bridge and original scripts as part
of review. This delivery's tests execute the bridge directly; they are not evidence
that hooks have been trusted or fired in your desktop session.

The checked-in command is:

```sh
python3 "$(git rev-parse --show-toplevel)/tools/ccgs_hooks.py" SessionStart
```

The event changes per registration. This quoted Unix command was exercised from a
subdirectory of a temporary repository whose path contains spaces. Keep the adapter
in the Git root; an archive extraction needs `git init` before this registration
can resolve it. Git Bash/WSL can run the scripts on Windows, but the registration
uses Unix shell syntax and is **not a native PowerShell/cmd registration**. A native
Windows installation needs a reviewed `commandWindows` override that invokes the
installed Python and Bash with correct path conversion. It has not been validated
here. Do not present Unix tests as Windows compatibility evidence.

## All original hooks

| Original `.claude/hooks/` script | Codex route | Behavior and boundary |
| --- | --- | --- |
| `session-start.sh` | SessionStart | Git/sprint/milestone/bug context and active state preview become additional context. The bridge also restores full saved notes. |
| `detect-gaps.sh` | SessionStart | Documentation gaps and initial setup suggestions become additional context. Original slash names refer to corresponding `ccgs-*` workflow skills. |
| `validate-commit.sh` | PreToolUse, Bash | Direct `git commit` runs the unchanged staged-path checks. Invalid asset JSON denies the call; stderr warnings stay advisory. |
| `validate-push.sh` | PreToolUse, Bash | Direct `git push` preserves the original protected-branch advisory; upstream does not block ordinary protected-branch pushes. |
| `validate-assets.sh` | PostToolUse, apply_patch / legacy Write or Edit | One normalized file-path invocation per affected asset path. Invalid JSON creates blocking feedback with exit 2; naming warnings remain advisory. The edit has already happened. |
| `validate-skill-change.sh` | PostToolUse, apply_patch / legacy Write or Edit | Changes under `.claude/skills/` preserve the original static-test reminder. Generated `.agents/skills/` drift is checked by `ccgs_codex.py check`, not by this upstream validator. |
| `pre-compact.sh` | PreCompact | Runs the upstream snapshot/logging script and atomically saves its output to a per-session checkpoint. A UI system message identifies that file. |
| `post-compact.sh` | PostCompact | Runs the upstream reminder, surfaced as a UI system message. Recovery context is supplied separately by SessionStart and UserPromptSubmit. |
| `session-stop.sh` | Stop | Archives active state and recent Git activity at turn end. `active.md` is retained; bridge stdout is JSON. This is the upstream Stop mapping, not a claim that every process termination is captured. |
| `log-agent.sh` | SubagentStart | Preserves agent-type audit entries in `production/session-logs/agent-audit.log`. |
| `log-agent-stop.sh` | SubagentStop | Preserves completion audit entries; bridge stdout is JSON. |
| `notify.sh` | Explicit host difference | Codex has no native Notification hook event. This Windows PowerShell toast script is preserved but not automatically registered or invoked. Use Codex's own notification settings for attention notifications; there is no claim of identical messages/triggers. |

## File normalization and rules

Canonical Codex inputs use `tool_name: "Bash"` or `"apply_patch"` and a string
`tool_input.command`. The bridge extracts every Add File, Update File, Delete File,
and Move to path from raw patches, deduplicates paths, resolves them against the
provided session cwd, and passes root-relative `file_path` values to the original
validators. Both sides of a rename are included. Nested `assets/` and
`.claude/skills/` directories retain the original scripts’ path coverage. JSON
payloads preserve Unicode characters for the upstream no-jq fallback. Deleted JSON files are naturally
skipped by the original existence check; naming advisories can still mention their
paths. Unsupported patch headers, paths outside this repository, malformed JSON,
and invalid required fields return explicit errors rather than silently succeeding.
The native patch tool remains responsible for validating patch hunk syntax.

Before a patch, the bridge includes the **complete unchanged bodies** of matching
`.claude/rules/*.md` rules as additional context, using their original path lists.
Legacy Write/Edit inputs with `file_path` are also accepted. Full rule bodies may
exceed the host context threshold: registration sets a 5,000-token limit; when the
host spills context to a file, the agent must read that full file. Rules are
instructions, not mechanical proof that every edit satisfies them.

Shell writes, scripts, external editors, MCP filesystem tools, and specialized
host tools do not all have a reliable changed-file payload. They are not silently
claimed as covered: project instructions require loading matching rules before
these edits and running the original validators on the affected files afterwards.
There is no expensive post-Bash full-tree scan. Unrelated shell commands do not run
commit/push/asset validators.

## Permissions and original validation limits

The bridge reads `permissions.deny` in the unchanged `.claude/settings.json`.
For supported Bash input it applies the original `Bash(...)` wildcard deny patterns;
it also supports `Read(file_path)` events if a host emits them. A matching pattern
returns a deny decision. The original allow list is intentionally never translated
into automatic approval. Codex normally reads files through Bash or other tools,
so the Claude `Read(**/.env*)` permission does **not** become universal native file
access control. Bash's original `.env` patterns remain covered as written.

This lightweight textual guardrail does not parse arbitrary shell programs or
expand aliases, variables, wrappers, chained commands, subprocesses, heredocs,
or interactive `write_stdin` input. It is not hard permission equivalence. Use the
host's sandbox and approval policies as the enforcement boundary. The runtime
instructions require following the original deny policy regardless of tool used.

Commit/push detection preserves the upstream direct-command scope (`git commit`
and `git push` at the beginning of the string). Wrapped commands, `git -C`, leading
environment assignments, and combined shell programs need explicit validation;
run a direct Git command from the repository root when relying on these hooks.
The scripts inspect staged **path names** but read current working files, not
staged blobs. Partially staged content therefore needs separate index validation.
Push protection is advisory, and the asset validator checks JSON syntax rather
than schemas/required keys despite the broader comment in its source. Source
scripts may swallow individual I/O errors internally; the bridge can only
propagate failures they actually report. These are retained upstream boundaries.

## Recovery, errors and output

PreCompact snapshots use
`production/session-state/codex-checkpoint-<session-id-hash>.md`; session IDs never
become raw path components. Atomic replacement prevents a partial snapshot.
SessionStart and UserPromptSubmit restore full `active.md` plus this session's
checkpoint. The checkpoint is a recovery note, not authoritative current state;
verify the working tree after resuming. A missing session ID uses a shared fallback
name for manual invocation; real host events provide the session ID. Neither
recovery nor Stop deletes `active.md`.

Original stdout and stderr are combined into model-visible context for events
that support context. Warnings at exit 0 remain visible without denial. Any
nonzero script exit becomes bridge exit 2 with explicit error feedback; missing
scripts and launch/timeout errors follow the same path. PreToolUse uses a deny
permission decision; PostToolUse uses block feedback and cannot undo an edit.
Stop/SubagentStop always return JSON; normal success can be `{}`. Compaction uses
system messages and file checkpoints rather than pretending plain stdout reaches
the model. A failure in SubagentStart is reported but the host cannot prevent that
subagent starting through this event.

The event contract and trust/coverage statements above were checked against the
[official Codex hooks reference](https://learn.chatgpt.com/docs/hooks) on
2026-09-18. Actual host support, enabled features and trusted definitions remain
prerequisites.

## Deterministic evidence

```sh
python3 -m unittest discover -s tests/codex_adapter -p test_hooks.py -v
```

Seventeen tests pass on the tested macOS/Python 3.10 host. They run actual original
scripts in disposable Git repositories, covering invalid staged JSON, advisory
commit/push output, multi-file/move/delete patch handling, path-scoped complete
rules, skill reminders, lifecycle state preservation, agent audits, malformed
inputs, deny-pattern behavior, absence of command interpolation, missing scripts,
and registration from a path with spaces. One explicit fixture fault injection
makes PreCompact exit 3 to verify error propagation. The initial 12 tests failed
before the bridge existed; two later regression tests failed before their fixes.
Three review regression tests reproduced nested asset/skill coverage loss and
Unicode filename validation without jq; all failed before their fixes. The no-jq
case uses a minimal PATH of real utilities and verifies the original validator
fails on the same malformed Unicode-named file. These deterministic tests do not
prove live hook activation or game-engine behavior.
