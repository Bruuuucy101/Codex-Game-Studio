# Optional GitHub board projection

`python3 tools/ccgs_codex.py board-sync snapshot [--epic SLUG]` reads canonical
`production/epics/*/story-*.md` and prints deterministic JSON. It does not write
files, run `gh`, or contact GitHub. Use the adapter's global `--root PATH` before
`board-sync` to inspect another project. This local step does not configure or
synchronize a remote board.

## Optional dependency and test isolation

Markdown-only snapshots and all other adapter commands need only Python 3.10+
standard library. When `production/sprint-status.yaml` exists, install the pinned
optional dependency in an environment you own:

```sh
python3 -m venv /tmp/ccgs-board-venv
/tmp/ccgs-board-venv/bin/python -m pip install -r requirements-board.txt
/tmp/ccgs-board-venv/bin/python tools/ccgs_codex.py board-sync snapshot
/tmp/ccgs-board-venv/bin/python -m unittest discover -s tests/board_sync -v
```

The separate core suite remains stdlib-only:

```sh
python3 -m unittest discover -s tests/codex_adapter -v
python3 tools/ccgs_codex.py check --strict-upstream
git diff --check
```

Nothing installs automatically. A missing PyYAML dependency reports the install
command only when a sprint YAML needs parsing. `requirements-board.txt` pins
`PyYAML==6.0.3`. Tests use disposable temporary source trees and real CLI processes;
no live GitHub board behavior is claimed by these checks.

## Accepted sources

The parser reads one meaningful H1 title and standard header declarations before
the first body H2. It ignores backtick/tilde fenced examples (including quoted
fences) and later body metadata such as Test Evidence Status. Canonical headers
use `> **Field**: value`; unquoted bold and plain `Field: value` also work.
Required fields are Epic, Status, Type and Estimate. Optional canonical fields
are Layer, Manifest Version and Last Updated. Duplicate, unknown or malformed
header declarations and missing/placeholder required values fail explicitly.
Raw values are retained without converting the source document.

Sprint YAML follows the original sprint-plan shape:

```yaml
sprint: 1
updated: 2026-09-21
stories:
  - file: production/epics/combat/story-001.md
    status: in_progress
```

Matching YAML `status` overrides story-header Status; the header is fallback for
stories not in YAML. Invalid header statuses still fail even if YAML overrides
one. A normalized mismatch produces a story warning. Safe references outside
the selected stories, including legacy `production/stories/...` entries, produce
warnings and are not exported. All YAML entries need valid paths and statuses;
duplicate references fail, including out-of-scope duplicates. Additional sprint
and story properties are allowed. The strict safe loader rejects aliases, custom
tags, merge keys, duplicate/non-string mapping keys, nesting over 50 levels and
more than 20,000 YAML nodes. Each source must be UTF-8 and at most 1 MiB; the
inventory permits at most 10,000 stories.

Paths are canonical project-relative POSIX paths; absolute paths, traversal,
backslashes, control characters and symlink source components are rejected.
Epics use exact lowercase folder slugs containing letters/numbers separated by
single hyphens. Story numbers may repeat across epics. An unknown filtered epic
fails; an empty unfiltered project produces an empty snapshot.

## Mappings

| Field | Source values | Board value |
|---|---|---|
| Stage | Not Started / backlog | Backlog |
| Stage | Ready / ready-for-dev | Ready |
| Stage | In Progress / in-progress / in_progress | In Progress |
| Stage | In Review / in-review / in_review / review | In Review |
| Stage | Blocked | Blocked |
| Stage | Done / Complete | Done |
| Stage | Deferred | Deferred |
| Type | Logic / Integration / UI | Same value |
| Type | Visual/Feel / Visual | Visual |
| Type | Config/Data / Config | Config |
| Size | XS / S | S |
| Size | M | M |
| Size | L / XL | L |
| Size | Positive finite hours ≤4 / ≤16 / >16 | S / M / L |
| Epic | Canonical containing folder slug | Same slug |

Mappings are case-insensitive. Hour estimates must use `h`, `hour` or `hours`,
for example `0.5h`, `4 hours`, or `16.5 h`. Unitless numbers, days, ranges, zero,
negative/non-finite values and placeholders fail with guidance. The human Epic
label remains in raw metadata for later remote body rendering.

## Schema and Python interface

`ccgs.board_snapshot.build_snapshot(root, epic=None) -> dict` returns schema v1:

- `schema_version`: integer `1`.
- `epic`: requested slug or `null`.
- `inventory`: sorted canonical story paths across **all** epics.
- `sources`: canonical source path → SHA256 of exact bytes, including all stories
  and sprint YAML when present. YAML absence is represented by no YAML key.
- `stories`: sorted selected records. Each contains `path`, `identity_input`
  (the same canonical relative path), `title` (complete H1 text), `raw_metadata`
  (canonical field names → unformatted source values), `normalized` (exact keys
  `Stage`, `Type`, `Size`, `Epic`), `status_source`, and `warnings` (string list).
- `status_source` within each story: `{path, field, value}`; header sources have
  `field: "Status"`; YAML sources have `field: "stories[N].status"`, where N is
  the zero-based list index. `value` preserves the chosen raw status string.
- `warnings`: global string list for out-of-scope sprint references.
- `sha256`: SHA256 of UTF-8 JSON of every preceding top-level field, using
  `ensure_ascii=False`, `sort_keys=True`, and `separators=(',', ':')`, with no
  timestamp and excluding the `sha256` key itself.

`ccgs.board_snapshot.validate_snapshot(root, snapshot) -> None` rebuilds the
snapshot and requires exact equality. Any story or YAML edit/addition/removal,
symlink substitution, or snapshot-record modification invalidates it. Even a
filtered snapshot includes all source hashes; changes in another epic therefore
require a fresh preview. Other documents do not participate in the hash.

`SnapshotError` subclasses `ValueError`. Messages identify the field/source and
corrective action without echoing malformed YAML payloads. Snapshot identity is
only a canonical path input; a namespace-based remote ownership marker belongs
to the remote integration. Revalidation is a pre-write freshness check, not a
filesystem transaction or a guarantee against edits after validation.

## Optional remote setup and synchronization

The remote integration is available through `/board-sync` (Codex:
`ccgs-board-sync`) or the same helper. Local snapshot requires neither gh nor
GitHub authentication. Remote operations require a callable GitHub CLI and
account access to the selected GitHub.com Projects v2 project. Nothing runs on
studio startup; no packages, credentials or global settings are installed.

Authenticate explicitly using GitHub's CLI, for example
`gh auth login --hostname github.com --scopes read:project` for preview or
`gh auth login --hostname github.com --scopes project` for mutation capability.
For an existing login, `gh auth refresh --hostname github.com --scopes project`
requests project scope. Organizational policy/SSO may require additional account
access. The helper never requests, prints or stores credentials. Classic-token
scope examples follow [GitHub's Projects API guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects).

```sh
# Default and --dry are equivalent; neither writes local state or remote data.
python3 tools/ccgs_codex.py board-sync setup --owner OWNER --namespace GAME --number 3
python3 tools/ccgs_codex.py board-sync setup --owner OWNER --namespace GAME --title "Game Board" --dry
# Explicitly adopt an existing project, or create privately if title is absent.
python3 tools/ccgs_codex.py board-sync setup --owner OWNER --namespace GAME --number 3 --write
python3 tools/ccgs_codex.py board-sync sync --epic combat --dry
python3 tools/ccgs_codex.py board-sync sync --epic combat --write
```

Use either `--number` or `--title`. Both user and organization owners are resolved
through the API. Number adopts an existing accessible project; title adopts a
unique match or proposes private creation. Multiple matches require an explicit
number. Adoption does not change project title/readme/privacy. Creation uses a
unique temporary title and then sets the intended title, private visibility and
owned setup marker; success requires a fresh verification. A conflicting existing
configuration fails instead of replacing the pinned project or namespace.

The config `.ccgs-board/board.config.json` schema v1 contains exactly `host`
(`github.com`), `owner`, `owner_id`, `owner_type` (`User`/`Organization`),
`project_id`, `project_number`, `project_url`, `namespace`, and `schema_version`.
The URL must match the selected owner type/login and number. Duplicate JSON keys,
unknown config keys, invalid types and unsafe state paths fail. The optional
GitHub dependency is reached only on setup/sync; other adapter commands remain
stdlib-only. An injectable executable exists solely at the Python library test
boundary, never as a CLI or config option.

Sync creates **draft cards**, never repository issues or comments. Each draft
body has a versioned marker containing the namespace, percent-encoded canonical
path and SHA256 of `namespace + NUL + path`. Removing the identity marker
makes a draft unmanaged; restore the verified marker before syncing if the card
should remain managed. Neither its title nor the local cache can prove ownership. The decoded path, rather than title
or story number, identifies the managed record. Human Epic label and canonical
source path remain in the body. Managed title/body and four mapped values are
repaired from the current source. Unmanaged cards, other field values, comments
and all existing options are retained. Field updates include each existing
option's id/name/color/description; new option IDs are re-read from GitHub.
GitHub's [single-select limit is 50 options](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-single-select-fields).
The union is preflighted, including dynamic Epic options; options are never
dropped to make room. Exact managed field-name/type conflicts stop writes.

Every run reads all pages of owner projects (setup), fields, items and item field
values. Item queries explicitly request `ARCHIVED` and `NOT_ARCHIVED` because the
API otherwise omits archived cards. Archived managed cards are reported and
left unchanged, not duplicated or unarchived. Removed/renamed paths report stale
cards only: there is no prune, delete or archive feature. `--epic` restricts cards
and stale reports to that epic; inventory/hash freshness still covers all epics.
Duplicate markers or redacted items prevent ownership verification and stop
before mutation. Missing/inaccessible projects and GraphQL errors inside a
successful HTTP response fail explicitly. Safe error messages omit raw remote
responses/stderr. Reads retry recognized transient failures up to three times;
mutations execute once and reconcile on the next run.

## State ownership and recovery

`.ccgs-board/` is ignored by Git. Its config, `state.json`, `mapping.json`, lock
and short-lived atomic-write files are helper-owned. No source documents change.
JSON state includes a schema version and kind; unowned files and symlinks are
preserved and rejected. Writes use temporary files, fsync and atomic replacement.
Mapping is a cache of separate `item_id` and DraftIssue `content_id`, never an
authority for skipping remote reads. Content updates use the draft ID; field
updates use the project item ID.

Write operations acquire `.ccgs-board/lock` atomically. If blocked, inspect
`lock/owner.json` for host, PID and unique owner token. Never remove a live lock.
Only after independently confirming that process on that host has stopped may
you manually remove the lock directory and rerun. A stale lock is not stolen
automatically, including after a crash. Locks serialize local runs only; no
cross-host exactly-once guarantee is claimed.

Setup persists a unique intent **before** attempting creation. After a timeout,
rerun the same setup command. It searches actual owner project pages for the
unique temporary title, saved project ID or setup readme marker. A single match
can finish setup; missing/ambiguous evidence stops instead of issuing another
create. Inspect the owner projects and explicitly adopt the intended `--number`
to resolve ambiguity. Do not clear intent merely to retry creation.

Sync similarly records pending field/card creation before that one request.
After a partial/uncertain failure, rerun sync: visible fields and ownership markers
are reconciled, missing values repaired and duplicates rejected. A pending create
still absent remotely is a blocker. Restore access, allow visibility to settle,
and inspect the project and owned state; only after independently establishing
that no create occurred may an operator explicitly clear that pending intent.
This conservative path may require manual intervention after a failure that
actually happened before the remote write. There is no automatic blind retry.

All source inventory/raw hashes, including optional sprint YAML, are revalidated
before each mutation and after apply. A changed input stops the run; previously
completed remote writes remain explicit partial state. The next invocation uses
a new snapshot and remote state. Final success requires a separate remote read
with zero remaining intended differences, not merely successful mutation exit
codes. Other-host edits between reads/writes remain a concurrency limitation.

## Evidence boundaries

`tests/board_sync/fake_gh.py` is a stateful external executable. The suite drives
the real CLI and subprocess JSON/argv boundary, one-row pagination, existing
option IDs, archived/unmanaged/duplicate/redacted cards, conflicts, authentication
errors, partial mutations, write-before-timeout and recovery. These are contract
fixtures, **not live GitHub acceptance**. The complete GraphQL documents are
inspectable in `tools/ccgs/board_github.py`; the controller independently validates
them against [GitHub's public schema](https://docs.github.com/en/graphql/overview/public-schema),
downloaded 2026-09-21 (SHA256
`8ecdb21a5c3affdeaa0e55bd9174536aa6c69cbb61f20ec796085aa1509c95df`).
The board CI job installs only `requirements-board.txt` and runs this suite;
core validation does not install PyYAML. Live authenticated account acceptance
remains unverified until a separately authorized disposable board run is possible.
