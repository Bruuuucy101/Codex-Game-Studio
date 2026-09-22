# Local Asset Tools Implementation Plan

> For agentic workers: use superpowers:subagent-driven-development task gates.

**Goal:** Executable image/frame/CPUforeground/FBXbone-region tools from issue23.
**Spec:** docs/superpowers/specs/2026-09-21-local-asset-tools.md
**Architecture:** Explicit local commands reuse asset source/hash/publication helpers; optional native/inference workers stay separate from core.
**Tech Stack:** Python3.10/Pillow12.3.0; separatePython3.12 CPU lock; actual FFmpeg/ffprobe and Blender4.5.14.

## Global Constraints

- Python3.10+ for image/media/Blender wrappers; extraction is a separate optional Python3.12 environment with exact platform-compatible dependency locks. Preserve original417-file lock and existing workflows/roles/generated entries.
- No global installs, silent model downloads or paid APIs. Basic image/frame commands never import rembg. External tools are explicit installed executable paths or PATH discoveries, passed through argv with shell=False; requests never contain arbitrary shell commands or script paths.
- Inputs are explicit project-local regular files with no symlink/traversal. Outputs stay under project assets/. Private operation state/staging stays under ignored .ccgs-assets/. Source, settings, tool/model versions and actual output hashes are recorded; existing outputs are never overwritten or adopted by hash alone.
- Preview is default and creates no files or processes with side effects; an explicit --write authorizes processing. Read-only native probe/version operations are separately labeled. Runtime/model absence is unavailable, not PASS.
- Reuse the tested shared source/path/hash/artifact publication primitives. Stage and verify every output, publish create-only using retained inode ownership, commit manifest last. Multiple outputs are not one atomic batch; interrupted/partial publication stays explicit and cannot produce a complete manifest. Never delete unrelated/modified output.
- Actual decoder/native/inference evidence is required for corresponding claims. A fixture subprocess or mocked model cannot certify real FFmpeg/Blender/rembg execution, artistic quality or engine import.

### Task 1: Image helpers and real video frames

**Files:** tools/ccgs/local_assets/{__init__,images,media,cli}.py; tests/local_assets/{test_images,test_media,fixtures}.py; docs/codex-adapter/local-assets.md; CLI/requirements-assets/CI usage integration as needed.
- [ ] Read binding spec and ../round3-research/local-asset-tools.md; capture preceding shared asset interfaces from report. Preserve sourcealpha and independent no-model framepath.
- [ ] MeaningfulRED tests for exactRGBApad/pixelJSON, grayscale/palette/animated/corrupt/bounds/aspect/fill, actual16bitPNG rejection before downconversion; nonemptyexistingdestination and identical-byteownership races; no-write previews.
- [ ] Implement strict imagecommands with optionallazyPillow and versioned actualoutputreceipts. Implement spec deterministic local operationID and status/resume routes; samecommand rerun reuses retainedstage, repeated completedoperation verifies ownedoutput, partiallink recovery uses exactoriginalinode. Test deathafterfirstlink/before receipt, noanonymousnewstaging/adoption, changedsource/newidentitycollision and interruptedprepublication computation. No lossy undocumentedpalette or RGBconversion. Reuse publication ownership.
- [ ] Add native ffprobe/FFmpeg wrappers and bounded watchdog, fixed localprotocols, actual declaredtiming/truncation policy, validimage/manifestchecks. ActualFFmpeg4frame/2fps/VFRtests required alongside error/timeout/resource/argvtests; no mocks-only PASS.
- [ ] Publish docs/runtime provenance and CI realnative job, focusedtests then assets/board/core/strict/generation/diff gates. Selfreview andcommit; reportexact sharedlocalinterfaces +actualruntimeevidence and any unavailableacceptance. No children,globalinstalls or publication.

### Task 2: Explicit verified models and CPU foreground extraction

**Files:** tools/ccgs/local_assets/{models,foreground,foreground_worker}.py; tests/local_assets/{test_models,test_foreground}.py; hashedplatform dependencylocks; modelsource manifest/notices; dedicated CPUacceptance CI and docs.
- [ ] Read spec,Task1report, local-runtime-feasibility research and verifieddownload receipts. Resolve actualcompatible Mac/Linuxwheels; do notcalluninstalledmetadata a testedlock. Recordstrong modelpins from controller's verifiedfirstacquisition beforefetchimplementation.
- [ ] RED tests for noimplicitdownload, missing/hashbadcache, allowedmodelonly, offlineworker, alpha multiplication, credential/environmentisolation, bounds/deadline, exactproviders and publishercollision. Model-fetch has explicit--write and knownURL/hash only.
- [ ] Implement dedicatedcache/atomicboundedfetch with size+SHA256 eachload; inference explicitCPU/rembgmodel, noBRIA/default/GPUfallback. Workerprocess,2threads, bounded runtime and inputs. No core/image importofrembg.
- [ ] Run realu2net and BiRefNet CPUfixtures using licensedphoto and verifiedweights; assertcoarsefgbg/nontrivialmask/alphapreservation, no-networkofflinecache repeat and corruptedcachefailure. Distinguishmockunitvsactualinference/quality. Keepweightfilesuntracked.
- [ ] Publish platformlocks/source/rights limitations and realCI evidence; run focused/integration/core/strict gates andselfreview/commit. ReportmodelSHA,versions,actualCPU/runtime and remainingquality/importgaps. Nochildren/globalinstalls/publication.

### Task 3: Actual headless Blender bone-region FBX splitting

**Files:** tools/ccgs/local_assets/{blender,blender_worker}.py; tests/local_assets/{test_blender,blender_fixture,blender_inspect}.py; nativeCI/docs/CLIintegration.
- [ ] Readbinding spec andactualcontribution behavior. InitialFBXonly, exactmesh/explicitregionbonemapping, animationsomit; no clip-splittingclaim.
- [ ] RED purecontract/nativefixturetests for regionduplicates/unknown/unweightedvertices/emptyregion/tie/crossfaces/limits; realtrustedFBXfixture plus selectedsplit andfreshprocessreimport.
- [ ] Implement trustedchecked-inBlenderscript invocation, noarbitraryscript/requestexecution, boundedtime/output, factory/startupnoautoexec. Preserve UV/material/weights/armature; countdiscardedcrossfaces and exportwithoutanimation. Reimportoutputs andrecordactualevidencebeforepublication.
- [ ] TestnamespacedForeArm exactmapping, modifier-onlyarmature, existingoutput, secondexportfailure, unchangedsourcehash andfreshFBXinspection. ActualBlenderrequired fornativePASS; noengineimport/qualityclaim.
- [ ] Document commands/limitations/nativeversion; run allrelevantlocal/integration/core/strict/generation/diff gates,selfreview/commit. ReportREDevidence,actualnativeoutputs,CI andremaininglimits. Nochildren/globalinstall/publication.
