# Creative capability discovery and asset production workflows

Addresses upstream issue40 and integrates issue23 provider/localtools and issue14
voice execution with the preserved studio. Userdelegated design. NativeCodex owns
MCP protocol, transport, authentication and live tool schemas; do not add a second
MCPclient or invent connector APIs.

## Global Constraints

- Preserve original417-file lock and originalrole/workflow capabilities. Add canonical workflows and regenerate; keep full/lean/solo and actualdelegation semantics. Existing art-director/technical-artist/audio-director restrictions remain intact.
- Configuration, visibletoolmetadata, successfulreadonlycall, acceptedgeneration, verifiedfile, creativeapproval, engineimport and audit are separate evidence. No toolname/configfile/fixture test can prove liveproduction or quality.
- No globalconfig/install/authentication changes or paidprovider calls in implementation/acceptance. Production workflows honor the user's concrete existing authorization and present missing costly/external scope only after a reviewable plan exists.
- Only call tools actually exposed by the activehost and use their current schemas. Do not guess AdobeFirefly, Unityeditor or Blender APIs from a plugin name. Preserve native tool errors/isError/disconnect/timeouts and acceptedIDs; never blindly repeat uncertainmutations.
- Existing specialists plan/review; authorizedcoordinator or actualallowedexecutor owns generation. Engineowner imports and records actualruntimeevidence. No fictitious handoffs or widening forbiddentools through anotherworkflow.
- Durable local intent/result/provenance records contain no credentials or signedURLs in public artifacts. Local artifact ingestion uses shared verifiedfile/nooverwrite receipts; creativeapproval/engineimport remain pending until actualevidence exists.

## Workflow 1: creative-tools

Entry `creative-tools [discover|status] [--category art|audio|3d|engine]` defaults to
readonlycurrentcapabilitydiscovery. Read actualhosttools/connectors and, if exposed,
the host's MCPserver/tool discovery API with pagination. Where hostonlyexposes
loadedtoolmetadata, record that limited inventory; do notclaim allinstalledservers
were enumerated. A configlist such as codexmcp list is configured-only and optional,
not an executablecapabilitytest. No globalconfiguration scan tocollectcredentials.

For relevanttools, read currentschemas and distinguish supportedpurpose, required
inputs, externalcharges, outputtype and resumestatus tools. Execute an appropriate
bounded side-effect-free health/catalog/project-inspection call only when its
schema permits and necessary explicitprojectIDs are alreadyprovided. No touching
arbitrary userprojects merelytoassertserverworks. Unavailableauth/editor/project
is BLOCKED with exactsafeerrorcategory; do notinstall/reconnect automatically.
No readonlyendpoint means callablemetadata-only, productionunverified.

Returninventory with server/toolname, evidencelevel(metadata/configured/readonly-
verified/blocked), checkedtime, selectedcategory, actualcallID/resultreference and
scope. Cache writtenonlywhen requested under production/creative-tools/ as an
explicitdatedreport; cachedstatus alwayssays staleuntilrechecked. No autostartup
mutationhook. APIkeys/envpresence is neverconnectionproof. A toolcanbevisibleand
USER_NOT_LOGGED_IN; currenthost Higgsfieldcatalog produced exactlythat realcase.

Published compatiblenotes use datedprimarysources: Adobe's documentedCodexflow
supports exposed editing tools and explicit upload/finalize, not unverifiedFirefly
or vector generation; Blenderofficial/communityservers differ; UnityCoplay is a
communityserver needing editor; otherconnectorfamilies are genericdiscoveryonly.
Never classify allserversfroma brand ascertified. Nativeclientowns initialize/list/
callprotocol; this repo's tests do notpretend tovalidate anotherclientimplementation.

## Workflow 2: asset-produce

Entry `asset-produce ASSET-NNN [plan|produce|status|collect|review|import|audit]`
defaults to plan. Resolve exactlyone actualasset-spec in design/assets/specs/,
artbible design/art/art-bible.md and mastermanifest design/assets/asset-manifest.md.
Read actualdimensions/format/prompt or audio descriptions, sourcefiles/references,
rights/evidence and intended enginepath. Needed means approvedspec pendingasset,
not completed/reviewedart. Missing/ambiguous/contradictorysources blockconcrete
production; do not guess IDs or overwritecanonicaldocs to pass.

Build a concrete explicit jobrequest for the supported PixelLab/Meshy/Tripo CLI,
localasset command, NPCvoice pipeline, or actualselectednativeMCPtool. Use current
operation schemas and supportedparameterlimits, explicitmodels/actions and
read-onlycost estimate ifactuallyavailable. No provider substitution, hidden
parallax/animation sweep or unsupported defaultparameter. Multipleuploads/stages
are explicitjobs; use saveddependencyIDs. Show destinations/inputhashes/statuses
and actualpendingeligibility. Defaultplan makes no generationcalls or filewrites.
Write a request/plan only when authorized; a request is not an artifact.

### Produce/status/collect

REST/local/voice routes invoke their actualshippedCLI and parseactualresult, using
exactreviewedrequests/IDs. Respect no-Bashparent by actualtools-programmer handoff
whenavailable, carrying fullrole/runtime/scope; if nonecanexecute, showblocker.
Do not make forbiddenart/audio specialists actasgenerators.

NativeMCP route uses only the selectedtool's real schema and documentedinputflow.
A reviewed native request fixes schema_version1, asset_id, host/server/tool identity
as actually exposed, explicit project/workspace scope, full private arguments,
source hashes, declared destinations, rights_note and optional generation_revision.
Derive JOB as native- plus the full canonical requestSHA256; persist this ID in the
reviewed plan. Every produce/status/collect uses that same selected plan/ID. A
changed request requires a new reviewed revision; existing ID with changed binding
fails. An explicit generation_revision is intentional regeneration, never added
automatically on a retry. Missing/ambiguous selected plan blocks production.

Small `creative plan/claim/record/status/check` CLI helpers reuse existing atomic
state/path/hash primitives; they do not call MCP or reimplement its protocol.
`plan --request PATH` validates offline. `claim --request PATH --write` atomically
creates an exclusive durable intent and returns invocation_allowed:true only for
the first claimant. Preview neverclaims. Concurrent or repeatedclaim returns the
existing state with invocation_allowed:false; the workflow must not reuse a prior
true response as fresh permission. A claimed intent withoutacceptedresult is
uncertain, even if the process died before actuallycallingthetool. No lockstealing.
`record --id JOB --result PATH --write` attaches the actualbounded result/callID,
using the returned localclaimtoken and matchingrequesthash; identicalresult repeat
is a no-op, conflictingresult fails. Localclaimtoken is not a providercredential.
`status --id JOB` is readonly. These records remain workflowevidence, not proof
that a providedresultJSON came from a service. Pair them with actualnativecall IDs.

Existing accepted jobs route only to the actualexposed status/collection tool and
same remote IDs; completed jobs return existingverifiedevidence. Neither branch
calls productionagain. If no executor can atomicallypersist/claim, nativeproduction
is unavailable until an actuallyauthorized persistencehandoff can do so.
Before a productioncall, persist an explicit private intent at
.ccgs-assets/native/JOB/ with toolname, supportedparameterhash, sourcehashes,
requestedresult/outputpaths and localjobID. A previous intent without a verified
result is uncertain; do not issue anothermutation. On acceptedjob/toolresult,
persist actualcallreference and job/task/outputIDs before waits/download. Do not
storecredentials/publicsignedURLs. Asyncjobs use actualexposedstatus/wait tools
and sameIDs. A localtimeout remains pending/uncertain, not failed or safe-to-retry.
If connectiondropswithunknownacceptance, reportproviderhistory/manualinspection
route. Localnativeintent is workflowevidence, not provideridempotency/cryptographic
attestation. Request/recovery records are not a fabricatedjobclient.

A synchronous tool artifact must actuallyexist or have a documenteddownload/export
route. Retrievewithin authorizedscope using tool-providedidentity, stage under
project, then invoke shared `assets ingest` with actualsource/output/ASSETID.
Retain the actualnativecall reference plus ingestionreceipt; don't claimreceipt
proves creativequality or toolremoteexecution withoutthat separateevidence.
Unsupportedfileformats failcontentverification ratherthanrename. Multioutput and
companionfiles must allhave explicitvalidatedmapping; missingoutputblocksgenerated
or collectioncompletion. Never download remotedata using forwardedAPIcredentials.

### Revision freshness across every phase

Immediately before nativeclaim and the productioncall, compare current sourcebytes
with the reviewed requesthash set; changedsources blockthatrequest. Existingaccepted
jobs may stillbe inspected by theirsavedIDs aftersourceschange, but remain linked
to originalsourceevidence and mustnot be relabeled current or regenerated.

Every phase record binds the exactrequestID, sourcehashset and collectedartifact
receipt/hashset. `creative check --evidence PATH` verifies confined referencedfiles,
receipt identities and currenthashes before advancing a phase. It verifies evidence
consistency only, not creativejudgment or authenticity of human-authoredassertions.
Review/import/audit records include the same artifactrevision plus actualreviewer/
tool/enginecall references; no reference-only approval withoutmatchinghashes.
Replacedbytes or changedsourcecriteria make affectedlatergates STALE/PENDING while
preserving historicalrecords. No import may inherit a review of differentbytes;
no audit mayinherit an import of anotherrevision. Produceaconcretefreshreviewplan
for the changedrevision ratherthan modifying oldapproval. Sourcefiles/outputs are
rechecked after externaltool steps as well tosurface interveningedits.

### Review/import/audit

Aftercollection, relevantdomainreviewer inspects actualfile (viewimage/listenaudio/
3Dinspection available) againstsourcecriteria. Recordreviewfinding/evidence, no
assumedapproval fromgenerationor automatedformatchecks. Full/lean consults actual
allowedroles; solo does localreviewbut labelsabsenceofindependentreview. Revision
creates newexplicitrequest/versionedoutput; retainspriorartifact and neverblindly
reuses uncertainpaidjob.

Importrequires an actualconfiguredengine and callableengineowner/tool; consult its
existing setup/import/test conventions, importrealfile and runappropriate engine
validation. Noengine/runtime means IMPORT_BLOCKED with nextstep. Genericfilecopy,
CLIingest, GLBparsing, catalogpresence, or a prosechecklist is notengineimport.
Audit uses actualasset-audit/localize VOvalidationand checksrealreferences and
source IDs. Updatecanonicalmanifest onlywithin authorizedscope, with separate
Produced/Reviewed/Imported/Audited facts and evidencepaths; do notinventunsupported
canonicalfields or mechanicallymarkallstatusesDone. Reportoverallphase according
to the weakest requiredgate, retain partialprogressand actionableblocker.

## Verification

Unit/sourceintegritytests verifyregistration/fullbodies/routing/provenance and
exactalloriginalidentities; they cannotprove agentbehavior. Add behavior specs and
freshfrozenfixtureobservations: (1) absent/disconnectednativecapability doesnot
inventtools or mutate; (2) actualreadonlycatalogcall recordsits realoutcome; (3)
validasset request executes allowedCLI, resumesfixturejob with0repeatPOST,
collectsverifiedfile and leavesreview/importpending; (4) existingtargetcollision
blockswithoutoverwrite; (5) no-Bashparent reallydelegates or reportsconstraint;
(6) missingengine blocksimportdespitevalidartifact; (7) native same-IDaccepted/completed/unresolved repeats make0productioncalls, concurrentclaims permitonecaller, changedbindingfails; (8) sourceeditafterplan and artifactreplacementafterreview makelatergatesstale; (9) audio routes throughvoice
ratherthanpretendinganySFXdescriptionisTTS.

Realnativeproduction/account/importacceptance remains explicitlyunverified without
an authorizedconnectedserver/editor. Currenthost readonlyHiggsfieldcall isblocked
USER_NOT_LOGGED_IN, so it supplies negativeintegrationevidence only. Original
workflows remainfullyusable without anycreativeserver. Runtimeprotocoltest belongs
to nativeclient; adaptertests assertobservedworkflow/toolboundaries, not a parallel
handwrittenMCPprotocolstack.
