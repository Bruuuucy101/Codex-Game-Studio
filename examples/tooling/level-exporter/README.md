# Level exporter

A small engine-agnostic game-data converter using Python 3.10+ standard library.
The synthetic fixture is authored for this repository and covered by its MIT
license. It contains two spawn locations, deliberately out of ID order.

From the repository root, with a previously absent output path:

```sh
python3 examples/tooling/level-exporter/export_levels.py examples/tooling/level-exporter/fixtures/levels.csv /tmp/levels-new.json
python3 -m unittest discover -s tests/codex_adapter -p test_level_exporter.py -v
```

Input is UTF-8 CSV with the exact ordered header `id,x,y,type`. At least one
record is required. Blank lines are ignored. Each record has exactly four
fields. Surrounding field whitespace is trimmed. `id` is a nonempty unique
case-sensitive string; `type` is a nonempty string. `x` and `y` are finite
numbers converted to JSON floats; nonnumeric, NaN and infinities are rejected.
CSV quoting follows Python's strict CSV reader (including quoted commas).
All data is validated before publication; this in-memory example is intended
for small level files, not streaming unbounded datasets.

Output is UTF-8 compact JSON with one final LF. Root keys, in order, are
`schema_version` (integer `1`) and `levels` (array). Records sort by ascending
case-sensitive Unicode `id`. Record keys, in order, are `id`, `x`, `y`, `type`.
Coordinates are floats; IDs and types stay strings. The fixture produces exactly:

```json
{"schema_version":1,"levels":[{"id":"spawn-a","x":0.0,"y":1.0,"type":"player"},{"id":"spawn-b","x":2.5,"y":-3.0,"type":"enemy"}]}
```

There are no overwrite flags, automatic directory creation or package installs.
Success exits 0 and prints the created path. Data/filesystem failures exit 1
with an actionable stderr message; invalid command usage exits 2. Existing
output (including symlinks), input=output, missing input and malformed batches
leave inputs and any existing output unchanged. No final output is published
for partial invalid data.

Publication writes and fsyncs a temporary file in the output directory, then
creates the final path with an atomic hard link. A concurrent writer's existing
path causes failure; there is no replace/rename fallback. Temporary files are
removed on success or failure. Filesystems without hard-link support fail
explicitly. Atomic visibility is tested; power-loss durability of directory
metadata and malicious concurrent directory replacement are outside this sample.
The injected `publish` function lets integration tests place a competing output
immediately before the real create-only publication, verifying the race boundary.

This demonstrates text CSV/JSON file processing. It does not prove native Unity,
Godot or Unreal binary conversion, engine import, unknown-field preservation or
round-trip behavior. No engine runtime is required or automatically executed.
