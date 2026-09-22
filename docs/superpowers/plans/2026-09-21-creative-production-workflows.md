# Creative Production Workflow Implementation Plan

> For agentic workers: use superpowers:subagent-driven-development task gates.

**Goal:** Native creativecapability awareness and executable spec→produce→collect→review→import→audit routing with truthful phaseevidence.
**Spec:** docs/superpowers/specs/2026-09-21-creative-production-workflows.md
**Architecture:** Two canonical workflows over nativehosttool APIs and completedCLIproviders/localtools/voice. No secondMCPclient. Workflowintent records +verifiedartifactreceipts preserve recovery andstageboundaries.

## Global Constraints

- Preserve original417-file lock and originalrole/workflow capabilities. Add canonical workflows and regenerate; keep full/lean/solo and actualdelegation semantics. Existing art-director/technical-artist/audio-director restrictions remain intact.
- Configuration, visibletoolmetadata, successfulreadonlycall, acceptedgeneration, verifiedfile, creativeapproval, engineimport and audit are separate evidence. No toolname/configfile/fixture test can prove liveproduction or quality.
- No globalconfig/install/authentication changes or paidprovider calls in implementation/acceptance. Production workflows honor the user's concrete existing authorization and present missing costly/external scope only after a reviewable plan exists.
- Only call tools actually exposed by the activehost and use their current schemas. Do not guess AdobeFirefly, Unityeditor or Blender APIs from a plugin name. Preserve native tool errors/isError/disconnect/timeouts and acceptedIDs; never blindly repeat uncertainmutations.
- Existing specialists plan/review; authorizedcoordinator or actualallowedexecutor owns generation. Engineowner imports and records actualruntimeevidence. No fictitious handoffs or widening forbiddentools through anotherworkflow.
- Durable local intent/result/provenance records contain no credentials or signedURLs in public artifacts. Local artifact ingestion uses shared verifiedfile/nooverwrite receipts; creativeapproval/engineimport remain pending until actualevidence exists.

### Task 1: Capability discovery and real asset production workflows

**Files:** .claude/skills/{creative-tools,asset-produce}/SKILL.md; testingframework specs/catalog; .claude/docs/{skills-reference,coordination-rules,directory-structure}.md minimally; docs/codex-adapter/{creative-tools,asset-production,capabilities,validation}.md; README/AGENTS/generated/patchledger; tests/codex_adapter/test_creative_workflows.py; tools/ccgs/creative.py and tests/creative_tools/ for smalllocalcheckpoint/freshnessCLI (sharedassetsI/O, noMCPtransport). Use actualprecedingCLIreport interfaces, no speculativecommands.
- [ ] Readbindingspec, actualasset-spec/art-bible/asset-audit/localize workflows and relevantart/audio/tool/engine roles. Read precedingprovider/local/voicereports for supportedexactcommands andlimits. DatedofficialCodexMCP/Adobe/Blender/Unityresearch supplies sources, not proof liveavailability.
- [ ] Use existingvalidbehaviorbaseline gap and author meaningfulfailing sourceintegritytests fornewworkflowregistration/fullcontent/rolelimits/phasegates; don'tmistake these for freshagentobservations. Root dispatches behavioralacceptanceafter implementation; nochildagents byimplementer.
- [ ] Implementcreative-tools livehostdiscovery semantics/configured-vs-callable-vs-blocked, safeactualreadonlyprobe, optionaldatedinventoryreport and stale cache. Neverguesstoolnames/schemas orautoinstall/auth. Avoid restrictingworkflowto a fabricatedMCPwildcard allowed-tools list; respectactualcoordinatorruntimecapabilities and unchangedroles.
- [ ] Implementandtestcreative plan/claim/record/status/check localhelpers with fullSHAstable nativeID, exactrequestbindings, atomicexclusiveclaim, repeat accepted/completed/unknown behavior and unchangedresultrecord no-op. ActualconcurrentCLIclaims allowexactlyone invocation; sourceedit blocksclaim, artifactreplacement makeslatergateevidenceSTALE. No MCPclient/networkcall inhelpers.
- [ ] Implementasset-produce phases withuniqueactualASSETID/spec/bible/manifest resolution, reviewedconcreterequest, actualCLI/nativeexecution and distinctstatus/collect/review/import/audit. Preserveexplicitcost/actionscope, nohiddenPOSTs, rawsourcehashes and uncertainty. Nativeintent/result flow mustlocateexistingIDbeforecall andretainacceptedIDs beforepoll; nofakeengineimport fromingest.
- [ ] Registercatalog/docs/generatedentries and minimalruntimecoordinationawareness; defaultstudio workswithoutproviders. Updatecapability/issuecoverage accurately: RESTcontract/localfixture/nativeblocked/livepending, UI/inpaintexperimental, GUI/Atlasdeferred. No broadunsupportedprovidercompletenessclaims.
- [ ] Run focusedtests thenallpriorintegration/core/strict/generation/diff gates, selfreview andcommit. Reportexactworkflowcounts/rolepreservation/remaininglivegaps and fixtureinstructionsforrootfreshobservations. Nochildren,paidcalls,globalsettings,publication.
