# Optional asset production — design

Implements the remote-provider part of upstream issue23 and supplies the artifact
boundary used by creative MCP issue40. The original planning/review workflows,
roles and source baseline remain intact. Product decisions are delegated by the
user for this overnight work. This design is approved by the controller after
canonical-source and current official API research.

## Outcome and chosen approach

Provide small Python commands that turn an explicit request into an observable
provider operation and verified local artifacts. PixelLab, Meshy and Tripo are
optional backends. Native MCP production later uses the same local artifact
ingestion and provenance boundary. A generation task, downloaded file, engine
import and creative approval remain separate facts.

Use direct REST adapters with narrowly supported, documented parameters instead
of vendoring the contribution's173files or depending on three large SDKs. The
current PixelLab proposal mishandles asynchronous responses; the current Tripo
Python SDK's main client uses V2 while official V3 REST uses different routes.
Implement PixelLab V2, Meshy's documented V1/V2 operation routes, and Tripo V3
consistently. Unsupported parameters are errors, not silently forwarded guesses.
The native Codex MCP client will own MCP protocol/authentication; this component
does not invent a second general MCP client.

## Global Constraints

- Preserve all existing studio capabilities, original417-file lock, reviewed patch provenance and generated entry consistency. Do not edit generated wrappers directly.
- Python3.10+; core studio commands remain standard-library-only. Asset image decoding uses optional `Pillow==12.3.0` in `requirements-assets.txt`, imported lazily. No global installs, implicit model downloads, credential collection or host configuration changes.
- Production API origins are fixed official HTTPS hosts. Credentials come only from named environment variables: `PIXELLAB_SECRET`, `MESHY_API_KEY`, `TRIPO_API_KEY`. Never persist/print API keys or authorization headers. Never expose signed URL query strings or raw remote error bodies in public plans, CLI output or logs. Necessary signed input URLs and transient output material may be stored only in restrictive private operation state, never published artifacts or ordinary summaries. No arbitrary API origin/executable is accepted through request/CLI/config. Tests inject transport boundaries in library code only.
- All operation state is confined to ignored `.ccgs-assets/`; receipts contain request/source/artifact hashes, provider operation/task IDs and distinct statuses. Existing project documents and outputs are not overwritten. Dry operations do not contact providers or create state.
- Validate the complete supported request before any billable POST. Persist submission intent first and accepted task IDs immediately. Never blindly repeat an uncertain submission, including after process death. Local locks protect concurrent operations; do not claim provider or cross-host exactly-once semantics.
- Use actual HTTP boundaries in credential-free tests, not only mocked provider methods. Mark fixture evidence separately from live account, visual/audio quality and engine-import evidence. No paid calls are needed to implement or claim local contract tests.
- Downloads use bounded time/bytes, separate credential-free connections and checked redirect destinations. Validate final output paths and content before atomic create-only publication; reject traversal, symlink components, destination collisions and corrupt/mismatched artifacts.

## Request and command contract

Requests are bounded UTF-8 JSON objects with duplicate-key, nonfinite-number and
unknown-field rejection. Schema version1 contains:

```json
{
  "schema_version": 1,
  "provider": "pixellab",
  "operation": "create-image-pixen",
  "asset_id": "ASSET-101",
  "source_files": ["design/assets/specs/guardian-assets.md", "design/art/art-bible.md"],
  "parameters": {"description": "An angular stone guardian", "image_size": {"width": 64, "height": 64}},
  "outputs": [{"key": "image", "path": "assets/art/character_guardian_idle_64.png", "format": "png", "width": 64, "height": 64}],
  "rights_note": "Record actual account/input-rights context; not a license assertion"
}
```

`asset_id` is an explicit stable identifier; canonical mode requires `ASSET-NNN`
and real source spec/art-bible paths. Standalone mode is selected only by
`"standalone": true`; it permits an explicit safe user identifier and an empty
source list, and must be labeled standalone in every receipt. No invented source
approval is inferred from `Status: Needed`: the original workflow uses that for
an approved specification whose asset has not yet been produced. `--write` is the
explicit authorization for the described operation, not proof of visual approval.

Commands live under `python3 tools/ccgs_codex.py assets`:

- `plan --request PATH`: validate supported request, source/output paths and hash
  all inputs; print canonical preview and expected effect, no network or writes.
- `submit --request PATH --id SLUG [--write]`: preview by default; on write create
  one journaled operation. Same ID plus same request returns existing state;
  same ID plus changed request fails. It never silently regenerates. Separate uploads
  are their own explicit operations, not a hidden prefix to generation.
- `status --id SLUG`: read-only local/remote inspection of a known task; no paid
  submission or state mutation. Missing key/network is an explicit limitation.
- `resume --id SLUG [--write] [--wait-seconds N]`: default previews; on write poll
  a known task with a monotonic deadline and update its receipt. Zero wait means
  one status check. It never submits a new job. Failed/cancelled/expired states
  remain distinct from a local wait deadline.
- `collect --id SLUG [--write]`: preview by default; on write fetch or decode
  completed outputs, validate them and publish all declared files without
  overwriting any. A repeat with matching owned output hashes is a no-op; changed
  owned files or unrelated collisions fail visibly.
- `ingest --source PATH --output PATH --asset-id ID [--write]`: validate a real
  project-local artifact delivered by a native tool/manual producer, then copy
  with the same no-overwrite/content/hash protections and an ingestion receipt.
  This is file staging, not an engine import or an approval operation.

Request paths and source paths must be real project-confined regular files.
Output paths are explicit project-relative files in `assets/`, not protected
studio source/config, hidden state or arbitrary absolute directories. The request
hash covers canonical parameters, all declared outputs and raw source hashes.
Before submission/collection, revalidate sources and output ownership. Request
JSON is limited to4MiB; source files to2MiB each and32entries; image input files to
16MiB; artifacts to128MiB each and16outputs. Bounded HTTP JSON responses may be
larger for inline images, with an explicit64MiB cap. Reject booleans as integers.
Default per-request timeout30s; polling deadline defaults120s and is capped600s.
The actual elapsed budget must constrain per-request waits and backoff.

## Durable state and content verification

Operation IDs are safe slugs and confined to `.ccgs-assets/jobs/ID/`. Store an
atomic `receipt.json`, private request snapshot and necessary private response material
with directories0700/files0600 (or the platform equivalent). Public plans redact URL
queries/fragments and credentials; private request hashing uses complete inputs.
Do not include private request/response files in generated artifact manifests. Never expose signed URLs in ordinary CLI summaries;
prefer re-querying task output URLs for collection. State includes `prepared`,
`submitting`, `submission_unknown`, `pending`, provider-terminal failure states,
`generated` and `collected`; non-media operations use `completed` plus a typed data result. Ingestion uses a separate receipt with its actual
source hash. Receipt/state files are validated on every load, including provider,
operation, ID, source/output paths, hash associations and task-ID format.

A crash after POST starts but before task ID persistence leaves an uncertain
operation and blocks automatic resubmission. Instructions direct the user to the
provider history/support rather than guessing that no job exists. A new explicit
operation ID is a deliberate new generation, not an automatic retry. Known IDs
always resume their existing remote job. Safe GETs may retry at most3times;
mutations are attempted once. A lock is owned by an unpredictable token and is
removed only by its owner; stale locks require explicit operator inspection.

For synchronous PixelLab results, journal the returned image bytes durably before
claiming generated; a interrupted response is still uncertain. For async output,
accept only the endpoint's supported terminal/envelope shape. PixelLab UI/inpaint
collection is explicitly experimental because current official OpenAPI leaves
completed last_response unconstrained; preserve unsupported results privately and
return recoverable unsupported_provider_result rather than inventing a success. Error summaries
expose safe categories/status codes and actionable next steps, not arbitrary
provider strings or secret-bearing URLs.

PNG/JPEG must decode fully using Pillow, with decompression limits and expected
format/dimensions; headers or file suffixes alone do not suffice. GLB2.0 must have
consistent container/chunk lengths and parseable JSON, valid referenced buffer
bounds and required asset version; external URIs are rejected unless explicitly
collected and verified as a complete supported bundle. GLB validity is not mesh,
rig or animation quality. FBX/other formats are unsupported unless an actual
validator/importer is provided; never claim validation from a magic prefix.

Preflight all collection targets before downloading, including same-filesystem
capability. Persist validated private staged files and their hashes before
publication; retain those staged inodes until publication receipts are committed.
Publish each target with atomic create-only hard linking. If hard links or a
same-filesystem destination are unavailable, fail before generation/publication
rather than falling back to overwriting rename. Files do not become visible as
one atomic batch; partial collection is explicit and never collection success.

If a process dies after linking a target but before recording it, recover ownership
only when the retained staged file and target have the same filesystem identity
AND expected hash. An unrelated file with identical bytes is still a collision.
On ordinary failure, roll back only publication proven owned by that identity and
unchanged hash. Keep the journal/staging for uncertain or partial outcomes; never
delete a competing writer's or subsequently modified file. Test both crash
intervals and identical-content competitors. Source changes after preview or
submission are surfaced rather than silently attaching old output to new specs.

## Explicit provider coverage

PixelLab V2: `create-image-pixen`, `create-image-pixflux`,
`create-image-pixflux-background`, `generate-ui-v2`, `image-to-pixelart`,
`inpaint-v3`, plus read-only balance. Synchronous image objects and asynchronous
`background_job_id`/`last_response` differ; use current OpenAPI schemas, not PR115's
old success/data assumption. Local image/mask parameters are explicit path inputs
encoded using the documented nested shape after decoding and dimension checks.
Mask white/black semantics and actual source/output sizes remain explicit.
Six local background presets (forest/desert/dungeon/city/space/underwater) expand
descriptive text only; no hidden extra parallax generation or claimed API modes.

Meshy: text preview and text refine as separate operations, image-to-3D, rigging,
animation with one explicit action, retexture and remesh. Use documented operation
routes and required model/task/input fields. No default `latest` model or automatic
animation sweep. Outputs are explicit GLB selections. Preview/refine/rig/animate
dependencies use actual successful task IDs, each with its own operation receipt.

Tripo V3: upload-image, text-to-model, image-to-model, rig-check, rig and retarget. Use dedicated
V3 paths and V3 `input` fields consistently, not V2 `type` payloads. Require an
explicit supported model where applicable and explicit action selection. A
pipeline is a documented sequence of recoverable operations, never one opaque
multi-charge retry. Image input uses a documented eligible URL or a separately
journaled upload-image operation at POST/v3/files. That operation durably stores
its returned typed upload result in private state, with completed state and no
public output required. Generation is a separate explicitly authorized submit
with its own ID. An operation-specific local `input_job` reference consumes the
verified completed upload receipt; it is resolved to the official input shape
and is never forwarded as an invented vendor field. Shared code loads and pins
dependency receipt/result hashes; adapters perform typed read-only eligibility
checks, not hidden mutable substeps.

After a crash following upload persistence, rerunning that upload ID returns its
completed result and a separate generation submit can proceed once. An uncertain
upload stays submission_unknown; an uncertain generation stays submission_unknown
on its separate ID. No command silently turns resume into a POST. Test crashes
after upload persistence and before/after generation submission with separate
route counters. Dry plans validate available local dependency evidence and label
external task eligibility unverified; write-time submission performs required
read-only eligibility checks before its POST. External provider task IDs remain
explicit inputs and do not imply successful/eligible work merely by their syntax.

Rig-check is a validation operation: its schema-checked JSON result may be
collected under assets/data with format json; it must not be labeled a generated
mesh. Media output validation and pipeline completion remain separate.

For each operation, record official source URL, retrieval date and exactly which
parameter subset is implemented. Reject unknown/unsupported parameters before
network. Expanding a vendor's optional parameter surface requires its own tests;
do not claim every feature offered by these services.

### Operation-specific contract decisions

The dated `provider-contract-matrix.md` research is the implementation authority
for the narrow provider field subsets. Publish the supported subset and dated
primary-source links in user documentation; research files outside the checkout
are working evidence, not required runtime files.

- PixelLab UI initially accepts square sizes16–512 only; do not infer missing
  rectangular aspect-cap formulas. Inpaint initially rejects crop_to_mask=true
  because output-size behavior is unspecified. UI/inpaint submit/poll are exact;
  collection is experimental, accepts only explicitly tested unambiguous image
  shapes, and preserves unsupported responses without resubmitting. Tests of
  compatibility shapes are labeled assumptions, never verified live responses.
- Meshy initial explicit generation/retexture model is meshy-6. Refine inherits
  its verified preview model. Animation requires a successful rig and membership
  in the free live GET animations/library?action_ids=... response, not a numeric
  range. Task IDs are opaque bounded strings. External task dependencies require
  their explicit source operation; never probe guessed routes until one works.
  SUCCEEDED alone cannot prove humanoid anatomy or actual polygon count.
- Tripo generation model is explicit v3.1-20260211. Current image endpoint uses
  input:string, superseding the pinned old SDK's file descriptor. The initial
  humanoid rig uses explicit v1.0-20240301, rig_type:biped, spec:tripo|mixamo and
  out_format:glb; retarget accepts exactly one of preset:biped:idle/walk/run.
  The rig consumes the original model input plus successful rig-check evidence
  for that same model, not the rig-check task ID as model input. False/unknown
  rig types remain valid validation data but never enable rig submission.
- Tripo upload returns a private file_token synchronously, not an asynchronous
  task. Repeated status on completed upload is local-only; no token-query or
  expiry API is assumed. Each supported operation retains its own actual result
  type and model/action compatibility checks.

## Verification and broader issue boundary

Tests cover actual local HTTP request/response exchanges; sync/async PixelLab,
every declared3Doperation, status recovery, no second POST on rerun, uncertain
response/death, concurrency, sources changed between preview/apply, malformed
JSON/schema, credentials unavailable, HTTP200 error envelopes,429/5xx GET limits,
deadline exhaustion, bounded downloads, corrupt-but-valid-magic images, GLB
structure, signed URL/redirection/auth isolation and target races. Include real
CLI subprocesses with library-injected fixture origins, not a production flag
that permits arbitrary hosts. Every phase runs its focused suite, the preceding
integration suites and core integrity checks before independent review.

Local extraction/media/Blender helpers are a separate following phase. Pixel Guy
desktop GUI and Atlas are explicitly outside this release's provider contract;
the upstream contributor permits staged tools and indefinite GUI deferral. The
issue remains partially delivered wherever listed local/GUI capabilities or
account/engine acceptance are absent. This is not permission to omit an operation
listed above silently. Commercial rights and account entitlements are recorded
as user/provider evidence, never inferred from code's MIT license.

## Evidence

Research: `work/round3-research/external-integrations.md` outside the published
checkout; original issue23 and canonical asset-spec/art-bible/asset-audit read.
Primary sources:

- https://api.pixellab.ai/v2/openapi.json
- https://docs.meshy.ai/en/api/text-to-3d and operation references linked there
- https://developers.tripo3d.ai/en/docs/migration-v2-to-v3
- https://developers.tripo3d.ai/en/docs/task-lifecycle
- https://learn.chatgpt.com/docs/extend/mcp?surface=cli
