"""Inventory actual upstream files; never infer completeness from README counts."""
import ast
import fnmatch
import hashlib
from pathlib import Path
import re


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def scalar(value):
    value = value.strip()
    if value.startswith(('"', "'", '[')):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            if value.startswith('[') and value.endswith(']'):
                return [scalar(x) for x in value[1:-1].split(',')]
            raise ValueError('Unsupported upstream metadata value: ' + value)
    return value


def frontmatter(text):
    if not text.startswith('---\n'):
        return {}, text
    header, delimiter, body = text[4:].partition('\n---\n')
    if not delimiter:
        raise ValueError('Unclosed frontmatter')
    result, key, block = {}, None, False
    for line in header.splitlines():
        if block and (line.startswith('  ') or not line):
            result[key] += line[2:] + '\n'
            continue
        block = False
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if line.startswith('  - ') and key and isinstance(result[key], list):
            result[key].append(scalar(line[4:]))
            continue
        if line[0].isspace() or ':' not in line:
            raise ValueError('Unsupported upstream metadata syntax: ' + line)
        key, value = line.split(':', 1)
        if value.strip() == '|':
            result[key], block = '', True
            continue
        result[key] = scalar(value) if value.strip() else []
    return result, body


def inventory(root):
    root = Path(root)
    groups = {
        'skills': '.claude/skills/*/SKILL.md',
        'agents': '.claude/agents/*.md',
        'rules': '.claude/rules/*.md',
        'hooks': '.claude/hooks/*.sh',
        'templates': '.claude/docs/templates/**/*',
        'behavior_specs': 'CCGS Skill Testing Framework/**/*.md',
    }
    result = {}
    for category, pattern in groups.items():
        rows = []
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            metadata, _ = frontmatter(raw.decode('utf-8')) if category in ('skills', 'agents', 'rules') else ({}, '')
            name = metadata.get('name', path.parent.name if category == 'skills' else path.stem)
            if category in ('skills', 'agents') and (not re.fullmatch(r'[a-z0-9-]+', name) or name != (path.parent.name if category == 'skills' else path.stem)):
                raise ValueError('Unexpected upstream identity: ' + str(path))
            rows.append({'name': name, 'source': path.relative_to(root).as_posix(),
                         'sha256': sha256(raw), 'metadata': metadata})
        result[category] = rows
    if not result['skills'] or not result['agents']:
        raise ValueError('Missing upstream studio sources')
    return result


def rules_for(root, paths):
    root = Path(root).resolve()
    normalized = []
    for value in paths:
        path = Path(value)
        path = path if path.is_absolute() else root / path
        try:
            normalized.append(path.resolve().relative_to(root).as_posix())
        except ValueError:
            continue
    return [r for r in inventory(root)['rules']
            if any(fnmatch.fnmatchcase(p, pattern) for p in normalized
                   for pattern in r['metadata'].get('paths', []))]
