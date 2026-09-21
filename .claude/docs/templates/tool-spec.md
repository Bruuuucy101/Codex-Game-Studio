# Tool Specification: [Name]

## Scope
[Standalone project or game component; exact owned source/test/doc paths and excluded paths.]

## Purpose
[Problem, users, workflow/pipeline position, upstream producer and downstream consumer.]

## Runtime and Dependencies
[Language/runtime and verified version/pin; dependency versions/lockfiles or standard
library only; supported OS/filesystem, size/memory limits; actual verification source.]

## Engine Target
[Explicit engine-agnostic status and reason, or target engine/version with verified
reference paths, import/round-trip expectations and responsible engine specialist.]

## Input
[Exact paths and format/version, fields/types/required/default values, encoding,
valid ranges, duplicate/missing/unknown field policy, source ownership.]

## Output
[Exact schema/version, keys/types/paths, compatibility/migration and unknown-reference
preservation; partial success semantics or whole-batch rejection.]

## Usage
[Exact executable commands, positional arguments/flags/configuration and help,
working directory, preconditions and opt-in side effects.]

## Determinism
[Ordering, formatting, numeric precision, newline/encoding, locale/time/randomness
policy; how identical input leads to identical output bytes.]

## Failure Behavior
[Actionable errors and exit codes; input/output identity checks; overwrite policy,
atomic publication, concurrent writers, cleanup, recovery and durability limits.]

## Examples
[Representative input/output fixtures with actual paths, provenance/license and
expected bytes or semantic results; mark invented samples explicitly synthetic.]

## Acceptance Criteria
[Testable outcomes for valid data, invalid/duplicate/missing inputs, existing output,
partial batch failures and concurrent publication; actual engine acceptance if needed.]

## Tests
[Units versus real file/CLI integration versus native-engine/manual checks; exact
commands/fixtures, expected outcomes, NOT RUN gaps, CI scope and supported platforms.]

## Decisions
[ADR paths, current statuses/hashes, dependencies and implementation blockers;
explicit reasoned N/A when no significant decisions/ADR references exist.]

## Evidence
[Observed/inferred/unverified facts; command/date/runtime/platform, input/output
checksums, independent reviewer identity/verdict, unresolved gaps and resume task.]
