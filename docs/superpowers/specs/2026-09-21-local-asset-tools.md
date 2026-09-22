# Local asset helpers — design

Implements issue23's image/media, CPU extraction and actual bone-weight FBX mesh
splitting utilities. This follows the provider phase and retains all original
studio workflows. User delegates design decisions. PixelGuy desktop GUI remains
explicitly deferred; none of these commands require it.

## Global Constraints

- Python3.10+ for image/media/Blender wrappers; extraction is a separate optional Python3.12 environment with exact platform-compatible dependency locks. Preserve original417-file lock and existing workflows/roles/generated entries.
- No global installs, silent model downloads or paid APIs. Basic image/frame commands never import rembg. External tools are explicit installed executable paths or PATH discoveries, passed through argv with shell=False; requests never contain arbitrary shell commands or script paths.
- Inputs are explicit project-local regular files with no symlink/traversal. Outputs stay under project assets/. Private operation state/staging stays under ignored .ccgs-assets/. Source, settings, tool/model versions and actual output hashes are recorded; existing outputs are never overwritten or adopted by hash alone.
- Preview is default and creates no files or processes with side effects; an explicit --write authorizes processing. Read-only native probe/version operations are separately labeled. Runtime/model absence is unavailable, not PASS.
- Reuse the tested shared source/path/hash/artifact publication primitives. Stage and verify every output, publish create-only using retained inode ownership, commit manifest last. Multiple outputs are not one atomic batch; interrupted/partial publication stays explicit and cannot produce a complete manifest. Never delete unrelated/modified output.
- Actual decoder/native/inference evidence is required for corresponding claims. A fixture subprocess or mocked model cannot certify real FFmpeg/Blender/rembg execution, artistic quality or engine import.

## Local operation identity and publication recovery

Each processing command derives a deterministic fullSHA256 operation ID from
schema, operation, canonical options, declared destinations and all raw input
hashes, including region/model identity and resolved native executable bytes/hash where applicable.
A missing required tool makes the executable plan unavailable until installed; do
not assign a complete processing identity from a guessed executable version. Preview returns this
ID and the existing operation state without writes. An explicit repeated --write
with identical inputs uses the same private local job/staged files, never a fresh
anonymous directory. Changed sources/options produce a new identity and an
existing destination remains a collision; use a new output destination explicitly.

`local-assets status --id ID` reads the saved receipt. `local-assets resume --id ID
[--write]` previews by default and on write resumes only verified retained staged
publication, never silently reruns FFmpeg/inference/Blender. Original settings,
source freshness, stage hashes/inodes and published target ownership are checked.
Same-command rerun on collected job verifies ownedoutputs and is a no-op; partial
publication consumes original retainedstaging and completes missinglinks. If death
occurs between link and receipt, sameinode+hash proves ownership; identicalbytes
from an unrelatedinode neverdo. Missing/corruptstaging or changedownedtarget fails.

Computation must finish and everyoutput bevalidated before firstpublication. A
process interrupted during computation with no publishedoutput may be explicitly
rerun using the samecommand/--write and cleaned only within its ownedstaging;
retained publication staging is never regenerated once anytarget exists. Persist
phase and intendedmanifest beforepublication. Locks neversteal live/staleownership;
manual recovery requires independently verifying originalprocess termination.
Model-fetch cache identity is selectedmodel+reviewedstronghash, distinct from these
processingjobs, and uses the same create-only/hashvalidation semantics.

## Image utilities

`local-assets pad --input PATH --output PATH [--left N --right N --top N --bottom N | --aspect W:H] --fill transparent|#RRGGBBAA [--write]`
uses Pillow12.3.0, full decode and orientation normalization, canvas expansion only.
Initial inputs are PNG with sample depth≤8 or ordinary8bit JPEG. Reject16bit PNG
by actual IHDR sample-depth inspection before conversion (Pillow may expose an
already-downconverted RGB mode), and reject floating/highprecision image modes.
Do not claim lossless8bit RGBA output from higherprecision input.
Borders are nonnegative integers; aspect is positive bounded reduced integers.
Pick smallest integer multiple containing the oriented source; odd extra goes to
right/bottom. No scaling/cropping; preserve all original RGBA including transparent
colored pixels. PNG output only, no silent flattening. Initial scope omits lossy
palette conversion, corner-average fill and fractional flags. Bound input16MiB,
image16million pixels, eachside8192 and output128MiB; reject animated images unless
a separately supported frame option is implemented. Record metadata handling:
pixel/alpha preservation is promised; unrelated source EXIF/ICC preservation is not.

`local-assets pixels --input PATH --output PATH [--write]` accepts actual PNG,
accepts only PNG sampledepth1/2/4/8, rejecting16bit from actualIHDR before
conversion; converts supported palette/grayscale to RGBA losslessly at represented color resolution,
and emits strict versioned JSON with width,height,mode:RGBA,order:row-major and
pixels rows of [r,g,b,a] byte tuples. No code execution output, quantization or
alpha threshold. Bound export1millionpixels/64MiB. Opaque black and transparent
black remain distinct.

## Video frames

`local-assets frames --input PATH --output-dir PATH [--fps RATIONAL] --max-frames N [--ffmpeg PATH --ffprobe PATH] [--write]`.
Initial selectedstream v:0; declared maxframes1–512, outputbudget512MiB, deadline
120seconds default/max600, dimensions≤4096 each and16millionpixels. Explicit cap
means possibly truncated, not a full-decode claim. Without fps, preserve decoded
frames with passthrough; with positive fps≤120, record resampled timeline and
possible duplicate/drop behavior. Do not invent VFR timestamps as index/avgfps.

Probe actual stream/format through bounded ffprobe JSON and record versions,
sourcehash, orientation/pixel-format policy. Require a real video stream. Invoke
FFmpeg with -nostdin, -n, -xerror, -map0:v:0, -an -sn -dn, explicit RGBA/PNG and
-fps_mode passthrough, with fps filter only when requested. Restrict native input
protocols to local file/pipe and do not follow network playlists. Record decoded
frame timestamps from a bounded ffprobe frame pass when source mode claims them;
otherwise label timing unavailable and provide ordered indices. Resampled output
uses its explicit rational timeline, labeled resampled, not original timestamps.

A watchdog enforces deadline, totalbytes/filecount while child runs and terminates
its owned process group on breach. Probe metadata is not sufficient resource
control. All outputs fully decode and match declared dimensions. Manifest lists
actual files, exact count, hashes, requested cap, truncation/unknown completeness,
source vs resampled timing and tool versions. No foreground removal in this path.

## CPU foreground extraction

`local-assets model-info --model u2net|birefnet-general` reports exact source,
size, hashes, dependency availability and model-license qualification offline.
`local-assets model-fetch --model NAME [--write]` is the only model-network path;
private fixed model cache under .ccgs-assets/models/. Atomic staged acquisition,
fixed official rembg-release URLs, bounded time/bytes/redirects, verified strong
SHA256 pin once established from independently recorded first acquisition. Never
silently trust an existing cache or fall back to an unverified model. Keep weights
outside Git/release archives. If no reviewed strong pin exists, fail clearly rather
than pretending MD5 supplies strong authenticity.

`local-assets foreground --input PATH --output PATH --model NAME [--write]`
processes one image offline; batching is explicit repeated jobs/frames composition.
Required model alreadyverified before rembg import/session, CPUExecutionProvider
only and confirmed active, explicit model name everycall (rembg2.0.85 defaultBRIA
must never be used). Dedicated child with REMBG_HOME under job-controlled cache,
neutralize U2NET_HOME and enforce offline no-fetch behavior before session creation.
Use a bounded worker deadline, max2threads, max16millionpixels and fixed verified
model sizes. One model session per invocation; no GPU requirement.

Output sourceRGB with predicted soft alpha multiplied by original source alpha;
original transparent pixels never become opaque. No implicit gamma/threshold or
hard cutout. Record modelname/SHA256/rembg/ORTversions, actualproviders, measured
elapsed time and hash. Maskquality is distinct from successful inference. Missing,
corrupt cache or unsupported runtime fails without network. A fully opaque/zero
mask can be legitimate; report degenerate-mask diagnostic rather than fabricate
foreground quality. Unit fixtures cover alpha arithmetic; real inference tests
use licensed photograph and coarse observable foreground/background samples.

Initial model source qualifications: u2net converted ONNX links upstream Apache2
code/checkpoints but has no separate converted-weight license; BiRefNet author's
code/modelcard MIT, rembg conversion provenance recorded. Do not apply wrapperMIT
to weights. Contribution semantics are reimplemented with attribution; any copied
code must preserve its explicit MIT grant/source commit.

## Blender bone-region splitting

`local-assets split-mesh --input PATH --output-dir PATH --mesh NAME --regions PATH --format fbx --animations omit [--blender PATH] [--write]`.
Initial input actualFBX, outputFBX, explicit exactmesh selection. `--regions` is a
strict project-local JSON mapping region safeID→list of exact bone names, plus
optional explicit fallbackregion. This avoids hidden substring anatomydetection
(the original can misclassify ForeArm as ear). Namespaced bones are exact inputs;
no fuzzy guessing. Unknown mapping bone or duplicatebone assignments fail; unused
vertex weights/unknown/unweighted vertices require explicitfallback or fail.

Checked-in trusted Blender script only, --background --factory-startup
--disable-autoexec --python-exit-code1. Find armature via modifier or parent;
ambiguity fails. Vertexregion is strongestpositive mappeddeformweight, stable
lexicalbonename tie-break. Keepfaces only when all vertices fall in same requested
region; countcross-region discardedfaces and open-seam limitation. No automatic
watertight surgery/clothing separation. Eachrequestedregion must have at least
onecompleteface, otherwise wholeoperation fails before publication.

Preserve UV/material/weights and required armature; exportanimations=false.
Reimport each producedFBX in a fresh process to verifyactualmesh/face/UV/material/
armature/weight properties. No claim of animationclips or animationpreservation.
Bound source128MiB, meshes64, vertices1million, regions32, output512MiB, process
max600seconds. Native crash/failedsecondexport leaves no completesuccessmanifest.
Record source+regionsJSONhash, mesh/bone selection, counts, discardedfaces,
Blenderexactversion, outputs/reimportevidence. Blender4.5.14LTS initialtestedtarget.

## Acceptance and CI

Stage1 imageunit+realFFmpeg: exact2x2RGBA transparency/black/128alpha roundtrip;
odd/aspect/border cases; corruption/collision/resourcebounds. Create1s16x16fourframe
FFV1 clip using realFFmpeg, all4frames and2fps→2; verifydifferentpixelcontent and
VFRtimingpolicy; malformed/no-video/networkplaylist/timeoutfailures.

Stage2 CPU: exactplatformlocks actuallyinstall; verifyu2net and BiRefNet complete
weights and realCPUinference on licensedphoto; offlinecache rerun, missing/badhash
and inputalpha. Slow large-modelacceptance can be a separate manualCI job, but must
run once for this release's actualinferenceclaim. Never substitute u2netp/mock for
u2net. Preserve actualruntime/peakmemory/versions, no unmeasured performancepromise.

Stage3 Blender: trusted script creates tinyFBX with2triangles/2bones/UV/2materials;
actualsplit+freshreimport verifiesexpectedfaces/weights and unchangedinputhash.
Additional cross-regiontri, modifier-onlyarmature, exactnamespacedForeArm,
unknown/unweighted/emptyregion, collisions and secondexportfailure cases. Real
native evidence required; absentbinary is unavailable. Eachstage then reruns its
relevant precedingintegration/core/provenancegates before independentreview.

Sources: upstream issue23 and contribution a22bf7954bde72b206a1efe8f35c8a541fd6d8a0;
Pillow12.3.0 docs; FFmpeg official options/fpsfilter; rembgv2.0.85 sessionfactory and
u2net/BiRefNet sessions; Blender4.5.14 FBX operators. Dated research/lock manifests
must be summarized in published local-tools docs, not required outsidecheckout.
