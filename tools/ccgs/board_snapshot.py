"""Read-only, deterministic snapshots of canonical studio stories.

Only an existing sprint YAML needs the optional PyYAML dependency. This module
never invokes commands, writes files, or derives identity from a display title.
"""
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat

SCHEMA_VERSION = 1
MAX_SOURCE_BYTES = 1_048_576
MAX_STORIES = 10_000
SPRINT_PATH = 'production/sprint-status.yaml'
EPICS_PATH = 'production/epics'
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
REQUIRED = ('Epic', 'Status', 'Type', 'Estimate')
METADATA = {key.casefold(): key for key in (*REQUIRED, 'Layer', 'Manifest Version', 'Last Updated')}
STAGES = {'not started': 'Backlog', 'backlog': 'Backlog', 'ready': 'Ready',
          'ready-for-dev': 'Ready', 'in progress': 'In Progress',
          'in-progress': 'In Progress', 'in review': 'In Review',
          'in-review': 'In Review', 'review': 'In Review', 'blocked': 'Blocked',
          'done': 'Done', 'complete': 'Done', 'deferred': 'Deferred'}
TYPES = {'logic': 'Logic', 'integration': 'Integration', 'visual/feel': 'Visual',
         'visual': 'Visual', 'ui': 'UI', 'config/data': 'Config', 'config': 'Config'}


class SnapshotError(ValueError):
    """Invalid local board source; the message is safe to show in CLI JSON."""


def _canonical_path(value):
    if (not isinstance(value, str) or not value or '\\' in value or ':' in value
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
            or value.startswith('/') or any(p in ('', '.', '..') for p in value.split('/'))):
        raise SnapshotError('UNSAFE_BOARD_PATH: use a canonical project-relative path without traversal')
    return PurePosixPath(value)


def _safe_path(root, relative):
    parts = _canonical_path(relative).parts
    current = root
    for index, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            raise SnapshotError('UNSAFE_BOARD_PATH: symlinks are not supported: ' + relative)
        if index < len(parts) - 1 and current.exists() and not current.is_dir():
            raise SnapshotError('INVALID_BOARD_PATH: source ancestors must be directories: ' + relative)
    return current


def _read(root, relative):
    path = _safe_path(root, relative)
    try:
        # Nonblocking prevents a replaced named pipe from hanging a read. Refuse
        # a final-component symlink even if it appears after the path check.
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        with os.fdopen(os.open(path, flags), 'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise SnapshotError('INVALID_BOARD_SOURCE: expected a regular file: ' + relative)
            raw = stream.read(MAX_SOURCE_BYTES + 1)
        _safe_path(root, relative)
    except OSError:
        raise SnapshotError('UNREADABLE_BOARD_SOURCE: check the file and permissions: ' + relative) from None
    if len(raw) > MAX_SOURCE_BYTES:
        raise SnapshotError('BOARD_SOURCE_TOO_LARGE: limit is 1 MiB per source: ' + relative)
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        raise SnapshotError('INVALID_BOARD_ENCODING: save as UTF-8: ' + relative) from None
    return raw, text


def _inventory(root, epic):
    base = _safe_path(root, EPICS_PATH)
    if not base.exists():
        if epic is not None:
            raise SnapshotError('UNKNOWN_BOARD_EPIC: choose an existing exact epic folder slug')
        return []
    if not base.is_dir():
        raise SnapshotError('INVALID_BOARD_SOURCE: production/epics must be a directory')
    if epic is not None and not _safe_path(root, EPICS_PATH + '/' + epic).is_dir():
        raise SnapshotError('UNKNOWN_BOARD_EPIC: choose an existing exact epic folder slug')
    result = []
    try:
        for folder in sorted(base.iterdir()):
            if folder.is_symlink():
                raise SnapshotError('UNSAFE_BOARD_PATH: epic folders must not be symlinks')
            if not folder.is_dir():
                continue
            # glob() suppresses enumeration errors and can silently erase an
            # unreadable epic from the canonical inventory. Propagate them.
            for path in sorted(folder.iterdir()):
                if not (path.name.startswith('story-') and path.name.endswith('.md')):
                    continue
                if not SLUG.fullmatch(folder.name):
                    raise SnapshotError('INVALID_BOARD_EPIC: use lowercase letters, numbers and single hyphens')
                relative = path.relative_to(root).as_posix()
                _safe_path(root, relative)
                result.append(relative)
                if len(result) > MAX_STORIES:
                    raise SnapshotError('BOARD_INVENTORY_TOO_LARGE: limit is 10000 stories')
    except OSError:
        raise SnapshotError('UNREADABLE_BOARD_INVENTORY: check epic folder permissions') from None
    return result


def _meaningful(value):
    return bool(value.strip()) and not re.search(r'\[[^\]]*\]|\b(?:TBD|TODO)\b', value, re.I)


def _stage(value, context):
    if not isinstance(value, str) or value.strip().casefold().replace('_', '-') not in STAGES:
        raise SnapshotError('INVALID_BOARD_STATUS: choose Backlog, Ready, In Progress, In Review, Blocked, Done or Deferred: ' + context)
    return STAGES[value.strip().casefold().replace('_', '-')]


def _size(value, context):
    shirts = {'XS': 'S', 'S': 'S', 'M': 'M', 'L': 'L', 'XL': 'L'}
    if value.upper() in shirts:
        return shirts[value.upper()]
    match = re.fullmatch(r'(\d+(?:\.\d+)?|\.\d+)\s*(?:h|hours?)', value, re.I)
    if match:
        hours = float(match[1])
        if math.isfinite(hours) and hours > 0:
            return 'S' if hours <= 4 else 'M' if hours <= 16 else 'L'
    raise SnapshotError('INVALID_BOARD_ESTIMATE: choose positive finite hours (e.g. 4h) or a t-shirt size XS/S/M/L/XL; days, ranges and placeholders are ambiguous: ' + context)


def _story(text, path):
    metadata, titles, fence = {}, [], None
    for line in text.splitlines():
        quoted = re.match(r'^(?: {0,3}> ?)+', line)
        depth = quoted[0].count('>') if quoted else 0
        content = line[quoted.end():] if quoted else line
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', content)
        if fence:
            if (marker and depth == fence[2] and marker[1][0] == fence[0]
                    and len(marker[1]) >= fence[1] and not marker[2].strip()):
                fence = None
            continue
        if marker:
            fence = (marker[1][0], len(marker[1]), depth)
            continue
        if re.match(r'^ {0,3}##\s', line):
            break
        title = re.fullmatch(r' {0,3}#\s+(.+?)(?:\s+#+)?\s*', line)
        if title:
            titles.append(title[1])
            continue
        # Only header field declarations are parsed. Bold labels are the
        # canonical create-stories form; plain labels are accepted too.
        field = re.fullmatch(r' {0,3}(?:\*\*([^*]+)\*\*|([A-Za-z][A-Za-z ]*))\s*:\s*(.*?)\s*', content)
        if field:
            name = (field[1] or field[2]).strip().casefold()
            if name not in METADATA:
                raise SnapshotError('UNKNOWN_BOARD_METADATA: use the canonical create-stories header fields: ' + path)
            key = METADATA[name]
            if key in metadata:
                raise SnapshotError('DUPLICATE_BOARD_METADATA: duplicate ' + key + ': ' + path)
            metadata[key] = field[3]
        elif (content.lstrip().startswith('**') or
              re.match(r'(?i)^\s*(?:Epic|Status|Type|Estimate|Layer|Manifest Version|Last Updated)\b', content)):
            raise SnapshotError('MALFORMED_BOARD_METADATA: use **Field**: value in the story header: ' + path)
    if len(titles) != 1 or not _meaningful(titles[0]):
        raise SnapshotError('INVALID_BOARD_TITLE: provide one meaningful H1 story title: ' + path)
    for key in REQUIRED:
        if key not in metadata or (key != 'Estimate' and not _meaningful(metadata[key])):
            raise SnapshotError('INVALID_BOARD_METADATA: missing or placeholder ' + key + ': ' + path)
    stage = _stage(metadata['Status'], path)
    kind = TYPES.get(metadata['Type'].casefold())
    if kind is None:
        raise SnapshotError('INVALID_BOARD_TYPE: choose Logic, Integration, Visual/Feel, UI or Config/Data: ' + path)
    return {'path': path, 'identity_input': path, 'title': titles[0],
            'raw_metadata': metadata,
            'normalized': {'Stage': stage, 'Type': kind, 'Size': _size(metadata['Estimate'], path),
                           'Epic': PurePosixPath(path).parts[2]},
            'status_source': {'path': path, 'field': 'Status', 'value': metadata['Status']},
            'warnings': []}


def _sprint(text, root):
    try:
        import yaml
    except ImportError:
        raise SnapshotError('MISSING_BOARD_DEPENDENCY: install the optional dependency in your environment with python -m pip install -r requirements-board.txt') from None

    class StrictLoader(yaml.SafeLoader):
        def __init__(self, stream):
            super().__init__(stream)
            self.depth = 0
            self.nodes = 0

        def compose_node(self, parent, index):
            if self.check_event(yaml.AliasEvent):
                raise SnapshotError('INVALID_BOARD_YAML: aliases are not supported')
            self.depth += 1
            self.nodes += 1
            if self.depth > 50 or self.nodes > 20_000:
                raise SnapshotError('INVALID_BOARD_YAML: nesting or node limit exceeded')
            try:
                return super().compose_node(parent, index)
            finally:
                self.depth -= 1

        def construct_mapping(self, node, deep=False):
            keys = set()
            for key_node, _ in node.value:
                key = self.construct_object(key_node, deep=deep)
                if not isinstance(key, str) or key in keys:
                    raise SnapshotError('INVALID_BOARD_YAML: duplicate or non-string mapping key')
                keys.add(key)
            return super().construct_mapping(node, deep=deep)

    try:
        data = yaml.load(text, Loader=StrictLoader)
    except (yaml.YAMLError, RecursionError, TypeError, OverflowError, ValueError) as exc:
        if isinstance(exc, SnapshotError):
            raise
        raise SnapshotError('INVALID_BOARD_YAML: fix syntax and use plain standard data without custom tags or merge keys') from None
    if not isinstance(data, dict) or not isinstance(data.get('stories'), list):
        raise SnapshotError('INVALID_BOARD_YAML: expected a mapping with stories: [{file, status, ...}]')
    entries = {}
    for index, entry in enumerate(data['stories']):
        if not isinstance(entry, dict) or 'file' not in entry or 'status' not in entry:
            raise SnapshotError('INVALID_BOARD_YAML: every story needs file and status')
        path = _canonical_path(entry['file']).as_posix()
        _safe_path(root, path)
        if path in entries:
            raise SnapshotError('INVALID_BOARD_YAML: duplicate story file reference: ' + path)
        stage = _stage(entry['status'], SPRINT_PATH + ' stories[' + str(index) + ']')
        entries[path] = (stage, {'path': SPRINT_PATH, 'field': f'stories[{index}].status', 'value': entry['status']})
    return entries


def _digest(snapshot):
    encoded = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def build_snapshot(root, epic=None):
    """Return schema-v1 JSON data without writing or invoking external tools.

    All canonical stories participate in inventory/source hashes even when epic
    filters the exported records. Sprint YAML, if present, overrides matching
    header statuses. Invalid header values still fail instead of being hidden.
    """
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise SnapshotError('INVALID_BOARD_ROOT: choose an existing non-symlink project directory')
    root = root.resolve()
    if epic is not None and (not isinstance(epic, str) or not SLUG.fullmatch(epic)):
        raise SnapshotError('INVALID_BOARD_EPIC: choose one exact lowercase folder slug')
    inventory = _inventory(root, epic)
    sources, stories, warnings = {}, [], []
    for path in inventory:
        raw, text = _read(root, path)
        sources[path] = hashlib.sha256(raw).hexdigest()
        if epic is None or PurePosixPath(path).parts[2] == epic:
            stories.append(_story(text, path))
    yaml_path = _safe_path(root, SPRINT_PATH)
    if yaml_path.exists():
        raw, text = _read(root, SPRINT_PATH)
        sources[SPRINT_PATH] = hashlib.sha256(raw).hexdigest()
        entries = _sprint(text, root)
        selected = {row['path']: row for row in stories}
        for path, (stage, source) in entries.items():
            if path not in selected:
                warnings.append('SPRINT_REFERENCE_OUT_OF_SCOPE: not exported: ' + path)
                continue
            row = selected[path]
            if row['normalized']['Stage'] != stage:
                row['warnings'].append('SPRINT_STATUS_OVERRIDES_HEADER: sprint YAML is authoritative')
            row['normalized']['Stage'] = stage
            row['status_source'] = source
    snapshot = {'schema_version': SCHEMA_VERSION, 'epic': epic, 'inventory': inventory,
                'sources': sources, 'stories': stories, 'warnings': warnings}
    snapshot['sha256'] = _digest(snapshot)
    return snapshot


def validate_snapshot(root, snapshot):
    """Raise SnapshotError if inputs or supplied snapshot changed since preview.

    Rebuilds the full inventory and all raw-source hashes, rejecting symlink
    substitutions. This is a freshness check, not a filesystem transaction.
    """
    if not isinstance(snapshot, dict) or snapshot.get('schema_version') != SCHEMA_VERSION:
        raise SnapshotError('INVALID_BOARD_SNAPSHOT: rebuild with board-sync snapshot')
    if build_snapshot(root, snapshot.get('epic')) != snapshot:
        raise SnapshotError('BOARD_SNAPSHOT_CHANGED: rebuild the preview before applying')
