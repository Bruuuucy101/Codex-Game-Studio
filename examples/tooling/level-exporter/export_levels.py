#!/usr/bin/env python3
"""Convert level CSV to deterministic JSON, publishing a new output only."""
import argparse
import csv
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile


def convert_csv(text):
    """Validate all rows before returning canonical UTF-8 JSON bytes."""
    reader = csv.reader(io.StringIO(text, newline=''), strict=True)
    if next(reader, None) != ['id', 'x', 'y', 'type']:
        raise ValueError('expected exact CSV header: id,x,y,type')
    levels, ids = [], set()
    for row in reader:
        line = reader.line_num
        if not row:
            continue
        if len(row) != 4:
            raise ValueError(f'row {line}: expected 4 fields (id,x,y,type)')
        identity, x, y, kind = (cell.strip() for cell in row)
        if not identity or not kind:
            raise ValueError(f'row {line}: id and type must be nonempty')
        if identity in ids:
            raise ValueError(f'row {line}: duplicate id {identity!r}')
        try:
            x, y = float(x), float(y)
        except ValueError as exc:
            raise ValueError(f'row {line}: x and y must be finite numbers') from exc
        if not all(math.isfinite(v) for v in (x, y)):
            raise ValueError(f'row {line}: x and y must be finite numbers')
        ids.add(identity)
        levels.append({'id': identity, 'x': x, 'y': y, 'type': kind})
    if not levels:
        raise ValueError('expected at least one level row')
    levels.sort(key=lambda row: row['id'])
    result = {'schema_version': 1, 'levels': levels}
    return (json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n').encode('utf-8')


def publish_create_only(temporary, target):
    """Atomically hard-link complete bytes to a previously absent final name.

    Link creation fails if any writer already owns target; never fall back to
    rename/replace. The caller owns temporary-file cleanup on every outcome.
    """
    os.link(temporary, target)


def export_file(source, target, *, publish=publish_create_only):
    """Read/validate input and publish without overwriting any existing path."""
    source, target = Path(source), Path(target)
    if source.resolve() == target.resolve():
        raise ValueError('input and output must be different paths')
    if target.exists() or target.is_symlink():
        raise FileExistsError(f'output already exists: {target}')
    payload = convert_csv(source.read_text(encoding='utf-8'))
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.' + target.name + '.', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        publish(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args(argv)
    try:
        export_file(args.input, args.output)
    except (ValueError, OSError, csv.Error) as exc:
        print(f'level-exporter: {exc}', file=sys.stderr)
        return 1
    print(f'Created {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
