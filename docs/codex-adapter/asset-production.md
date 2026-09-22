# Optional asset production

The asset CLI implements PixelLab V2 image production and safe local artifact
staging. It does not approve art, run an engine importer or run asset-audit.
The existing 75 workflows and 57 roles are unchanged by this command addition.
All six PixelLab operations have credential-free HTTP fixtures. Live account,
billing, visual quality, rights and engine acceptance remain unverified.

Install the optional `requirements-assets.txt` into a project virtual environment
before image operations. It pins Pillow 12.3.0 for complete PNG/JPEG decoding.
Core studio commands remain standard-library-only; they do not import Pillow.
Credentials are read only from `PIXELLAB_SECRET`. Never put a key in a request.
Production uses `https://api.pixellab.ai/v2`; there is no configurable API host.
No command installs packages or downloads models automatically. Safe filesystem
operations currently require POSIX no-follow/directory-descriptor primitives;
unsupported platforms fail before production instead of weakening path checks.

## Requests and commands

Save a UTF-8 JSON request as a real project-local file:

```json
{
  "schema_version": 1,
  "provider": "pixellab",
  "operation": "create-image-pixen",
  "asset_id": "ASSET-101",
  "source_files": ["design/assets/specs/guardian-assets.md", "design/art/art-bible.md"],
  "parameters": {
    "description": "An angular stone guardian",
    "image_size": {"width": 64, "height": 64}
  },
  "outputs": [
    {"key": "image", "path": "assets/art/guardian.png", "format": "png", "width": 64, "height": 64}
  ],
  "rights_note": "Record actual input rights and account context here"
}
```

Canonical mode requires a real art bible and at least one real Markdown file
under `design/assets/specs/` containing that exact ASSET identity. It does not
infer creative approval from a filename or from `Status: Needed`. For an explicit
standalone operation, set `"standalone": true`, choose a safe stable user ID, and
use an empty source list if appropriate. Every receipt retains this distinction.
The example is illustrative; it does not create or approve a source specification.

```sh
python3 tools/ccgs_codex.py assets plan --request requests/guardian.json
python3 tools/ccgs_codex.py assets submit --request requests/guardian.json --id guardian-v1
python3 tools/ccgs_codex.py assets submit --request requests/guardian.json --id guardian-v1 --write
python3 tools/ccgs_codex.py assets status --id guardian-v1
python3 tools/ccgs_codex.py assets resume --id guardian-v1 --write --wait-seconds 120
python3 tools/ccgs_codex.py assets collect --id guardian-v1 --write
python3 tools/ccgs_codex.py assets balance --provider pixellab
python3 tools/ccgs_codex.py assets ingest --source incoming/native.png --output assets/art/native.png --asset-id ASSET-101 --write
```

Use the interpreter from the optional virtual environment for these commands.
A custom project root uses the existing top-level `--root PATH` option before
`assets`. Request, input and output arguments remain project-relative paths.
`plan` is offline and creates no state. `submit`, `resume`, `collect` and `ingest`
preview by default; `--write` authorizes their stated effect. `status` may make a
read-only provider GET but never changes local state. `balance` makes only the
read-only balance GET and returns known credit/subscription fields.

`resume` defaults to a 120-second polling budget, capped at 600 seconds. Zero
performs one check. A local wait deadline leaves pending work pending; it is not
a provider failure. One HTTP attempt is bounded by 30 seconds and the remaining
monotonic budget. GET has at most three attempts per URL; a mutation has one.

Requests reject duplicate/unknown fields, nonfinite numbers, boolean dimensions,
unsupported options, traversal, symlinks and output collisions. Limits: request
4 MiB; at most 32 source documents of 2 MiB each; image input 16 MiB; HTTP JSON
64 MiB; at most 16 outputs of 128 MiB each. PixelLab declares exactly one output,
key `image`; its dimensions must match the operation's output dimensions.
Source PNG/JPEG content determines the upload format, regardless of its suffix.
Every local image and mask is automatically hashed even when absent from
`source_files`. Source changes after submission prevent silent collection.

## Supported PixelLab subset

These are intentionally narrow local subsets, not all vendor options. Required
local fields include reproducible dimensions where the vendor supplies defaults.
Unknown parameters fail before networking. Optional nulls must be omitted instead.

| Operation | Required parameters | Optional parameters | Constraints/result |
|---|---|---|---|
| `create-image-pixen` | `description`, `image_size` | `seed`, `no_background`, `background_preset` | Sides 16–768, multiples of 4, area ≤512², square if either side <32; synchronous `image` |
| `create-image-pixflux` | `description`, `image_size` | `seed`, `no_background`, `init_image`, `init_image_strength`, `background_preset` | Sides 16–400, area ≥32²; init image matches size, strength 1–999 requires init image; synchronous `image` |
| `create-image-pixflux-background` | Same as pixflux | Same as pixflux | Same sizes; async `background_job_id`; completed `last_response.image` |
| `generate-ui-v2` | `description`, explicit `image_size` | nonnegative `seed`, `no_background`, `color_palette` ≤200 characters | Local square-only subset 16–512; async; completion decoder experimental |
| `image-to-pixelart` | local path `image`, `image_size`, `output_size` | nonnegative `seed`, `fixer`, `init_image_strength` 0–999 | Source 16–2048, output 16–512; source size matches decoded image; synchronous `image` matches output size |
| `inpaint-v3` | `description`, local paths `inpainting_image`, `mask_image` | nonnegative `seed`, `no_background`, `crop_to_mask:false` | Source 32–512; mask same size; crop true rejected and omitted crop sent false; async experimental completion |

Descriptions are nonempty and locally capped at 2000 characters. Integer seed
support is bounded locally to signed 64-bit range; UI, conversion and inpaint
add the provider's nonnegative constraint. Pixen/pixflux retain negative seeds.
PNG and JPEG are the supported declared output formats; the file content must
match the declared format and dimensions. There is no implicit format conversion.
UI concept images, prompt enhancement, inpaint context/crop/bounding-box behavior
and unlisted guidance options are outside this subset.

`init_image`, `image`, `inpainting_image` and `mask_image` are local path strings
in requests. The adapter sends documented `{type, format, base64}` wire objects;
inpaint wraps each with `{image, size}`. The mask convention is white generates,
black preserves. The tool checks dimensions and decoding, not artistic mask intent.

`background_preset` accepts `forest`, `desert`, `dungeon`, `city`, `space` or
`underwater`. Each appends one explicit descriptive sentence to the prompt. The
expanded description and selected preset are in the canonical request hash.
There is no extra generation, parallax fanout or invented vendor mode.
The pixflux `-background` endpoint means asynchronous execution, not an art style.

UI/inpaint completion is **experimental compatibility behavior**: one unambiguous
`last_response.image` object or a singleton `last_response.images` array is
accepted. The latter is an assumption tested with a fixture, not a verified live
provider contract. Ambiguous arrays, unfamiliar shapes and invalid base64 remain
`unsupported_provider_result`, retaining bounded private evidence and the known
task ID. They never cause collection success or another POST. Polling uses
`GET /background-jobs/{job_id}`, documented processing/completed/failed states and
matching returned IDs. A 404 is not permission to regenerate.

## Recovery, privacy and publication

Private state lives only under ignored `.ccgs-assets/jobs/ID/` with directories
0700 and files 0600. Atomic plan/receipt/result records bind request and source
hashes to provider IDs. Raw signed URLs, upload tokens and unknown response shapes
stay private. Public summaries exclude private data and redact URL queries and
fragments; artifact manifests never include private request/result snapshots.
HTTP errors expose categories/status codes, not raw bodies or authorization.
Artifact downloads use separate credential-free connections, validate every
redirect, reject private-network destinations and pin checked DNS addresses.

A repeated ID and identical request returns its existing state. Changed requests
under that ID fail. A crash after submission intent but before durable response
leaves `submission_unknown`; inspect provider history/support. Never delete that
state and retry casually. A new ID means a deliberate new operation. A retained
lock requires operator inspection of the original process and state; no command
automatically breaks a stale lock. These are local duplicate protections, not a
claim of provider or cross-host exactly-once semantics.

Synchronous bytes are saved before reporting generated. A complete atomic result
can reconcile the single crash interval before its receipt pointer is saved.
For a generated task with URL artifacts, explicit `resume --write` can refresh
expired URLs through that same task's GET route without a new submission.
Separate upload operations can complete with typed private data and zero public
files; later generation operations pin that result under their own IDs. Shared
fixtures cover this protocol; Meshy/Tripo adapters ship in the following task.

Collection preflights all outputs, probes same-filesystem hard-link support before
submission/publication, downloads or decodes to private staging, verifies content,
then publishes using create-only hard links. Unsupported filesystems fail; there
is no overwrite-rename fallback. Files become visible individually. Partial
collection remains explicit and is not a successful batch.

Staged files and hashes are retained for recovery. Ownership after a link-before-
receipt crash requires matching filesystem identity **and** the expected hash.
An unrelated file with identical bytes is a collision. A failed collection retains
every published target, its staging and journal for inspection; it never
automatically unlinks public files. Recovery can link missing targets from
unchanged retained staging after verifying ownership of existing targets. A
completed-owned repeat is a no-op only when every destination still exists with
the retained inode and expected hash; deleted or modified output fails visibly.

PNG/JPEG decode fully with Pillow and a 16,777,216-pixel limit. GLB 2.0 checks total
and chunk sizes, required JSON asset version, buffers/views/accessor bounds,
explicit stride constraints, effective offset alignment and embedded image
references; external URIs and sparse accessors are unsupported.
This is container/data validation, not mesh, rig, animation or engine quality.
FBX and arbitrary JSON ingestion are unsupported without a genuine validator.
Adapter-declared JSON results require that adapter's typed validator.

Ingestion validates a real project-local PNG/JPEG/GLB source and copies it through
the same owned staging boundary. It produces a separate deterministic ingestion
receipt and supports later status/collection checks. Ingestion receipts explicitly
use standalone provenance: an ASSET ID alone does not prove canonical approval.
Creative review, engine import and asset audit remain pending.

## Primary-source evidence and tests

Contract retrieval date: **2026-09-21**. Authority:
[PixelLab V2 OpenAPI](https://api.pixellab.ai/v2/openapi.json), OpenAPI 3.1.0,
provider info version `dev`, SHA256
`44c0884807ab4719a147a72e489a3f961e8219b889d4fd726ca0f61b086dcad0`.
The transitive contract excerpt SHA256 is
`dddcf471cfbaa088cc7bb567d5c2619e59443ce8be2ecdca9afa0f824ee22dd5`.
The endpoint schemas, background-job schema and balance schema were inspected;
PR wrappers and the old V1 SDK are not API authorities. Research snapshots are
working evidence outside the release and are not runtime dependencies.

Run `python3 -m unittest discover -s tests/asset_tools -v` in the optional asset
environment. Tests use an actual local HTTP server and CLI subprocesses, including
actual process death and operator-inspected stale test locks. Origin replacement
exists only through a library constructor/test launcher; no CLI/config/env host
override exists. A separate `assets` CI job installs only the asset dependency
and blocks release alongside every preceding job. Local fixture success does not
establish live entitlements, billing count, image quality, licensing, provider
availability, production TLS connectivity or engine import.
