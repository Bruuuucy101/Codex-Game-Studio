"""Conservative, read-only project classification. No discovery-time execution."""
import json
from pathlib import Path
import re
import stat

GAME_STAGES = frozenset({'Concept', 'Systems Design', 'Technical Setup',
                         'Pre-Production', 'Production', 'Polish', 'Release'})
TOOL_STAGE = 'Tooling Project'
TOOL_SPEC = 'tools/TOOL_SPEC.md'
CONTRACT_SECTIONS = ('Scope', 'Purpose', 'Runtime and Dependencies', 'Engine Target',
                     'Input', 'Output', 'Usage', 'Determinism', 'Failure Behavior',
                     'Examples', 'Acceptance Criteria', 'Tests', 'Decisions', 'Evidence')


def _visible(text, include_code=False):
    """Ignore comments and fenced examples when looking for configuration prose."""
    text = re.sub(r'\A---\r?\n.*?\r?\n---(?:\r?\n|$)', '', text, flags=re.S)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    fence = None
    lines = []
    for line in text.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            token = match[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            if include_code:
                lines.append('    ' + line)
        elif fence is None:
            lines.append(line)
        elif include_code:
            lines.append("    " + line)
    return lines


def _meaningful(text, include_code=False):
    prose = []
    fence = None
    for line in _visible(text, include_code=include_code):
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            token = match[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        elif fence is not None:
            if line.strip():
                return True  # Literal examples, including JSON arrays, are content.
        else:
            prose.append(line)
    # A wrapped placeholder is one span; line wrapping cannot create evidence.
    visible = re.sub(r'\[[^\]]*\]', '', '\n'.join(prose))
    for line in visible.splitlines():
        if re.match(r'^\s*#', line):
            continue
        line = line.strip(' \t-*|`')
        if line and not re.fullmatch(r'(?:TODO|TBD|N/?A|None|Not configured|[-: ]+)[.!]?', line, re.I):
            return True
    return False


def _sections(text, include_code=False):
    sections = {}
    current = ''
    for line in _visible(text, include_code=include_code):
        match = re.match(r'^#{1,6}\s+(.+?)\s*#*$', line)
        if match:
            current = match[1].casefold()
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {key: '\n'.join(lines) for key, lines in sections.items()}


def _configured_engine(text, section):
    body = _sections(text).get(section.casefold(), '')
    for line in body.splitlines():
        match = re.fullmatch(r'\s*[-*]?\s*(?:\*\*)?Engine(?:\*\*)?\s*:\s*(.+)', line)
        if match:
            value = match[1].strip().strip('`')
            absent = re.match(r'^(?:N/?A|None|not[ -]configured)(?=$|[\s(:;—–-])', value, re.I)
            if not absent and _meaningful(value) and not re.search(r'engine[- ]agnostic|not applicable', value, re.I):
                return True
    return False


def detect_project_kind(root) -> dict:
    """Return kind, source, paths, gaps and observed stage without mutating root.

    Invalid configuration fails closed as conflict. Valid explicit kind wins;
    incompatible valid evidence is retained with an actionable warning.
    """
    result = {'kind': 'unknown', 'source': 'none', 'evidence': [],
              'warnings': [], 'tool_spec': None, 'stage': None}
    root = Path(root)
    if '..' in root.parts or root.is_symlink() or not root.is_dir():
        result.update(kind='conflict')
        result['warnings'].append('Use an existing non-symlink project root without traversal.')
        return result
    root = root.absolute()
    errors = []
    evidence = result['evidence']
    warnings = result['warnings']

    def read(name):
        path = root
        try:
            for part in Path(name).parts:
                path = path / part
                if path.is_symlink():
                    raise ValueError('symlink path is not allowed')
            info = path.stat()
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('expected a regular file')
            if not info.st_mode & 0o444:
                raise ValueError('file is not readable')
            return path.read_bytes().decode('utf-8')
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            errors.append(f'{name}: {exc}; repair this project path before continuing.')
            evidence.append(name)
            return None

    marker = read('production/project-kind.txt')
    if marker is not None:
        result['source'] = 'explicit'
        evidence.append('production/project-kind.txt')
        if marker not in ('game', 'game\n', 'tooling', 'tooling\n'):
            errors.append('production/project-kind.txt must be exactly game or tooling, with at most one final newline.')
        else:
            result['kind'] = marker.rstrip('\n')

    stage = read('production/stage.txt')
    if stage is not None:
        result['stage'] = stage.removesuffix('\n')
        evidence.append('production/stage.txt')
        if result['stage'] not in GAME_STAGES | {TOOL_STAGE}:
            errors.append('production/stage.txt has an invalid stage; select an original game stage or Tooling Project.')

    spec = read(TOOL_SPEC)
    meaningful_spec = False
    if spec is not None:
        result['tool_spec'] = TOOL_SPEC
        sections = _sections(spec, include_code=True)
        meaningful_spec = _meaningful(sections.get('purpose', ''), include_code=True)
        if meaningful_spec:
            evidence.append(TOOL_SPEC)
        gaps = [s for s in CONTRACT_SECTIONS if not _meaningful(sections.get(s.casefold(), ''), include_code=True)]
        if gaps:
            warnings.append('Complete tools/TOOL_SPEC.md contract sections: ' + ', '.join(gaps) + '. Content is not implementation/test evidence.')

    game = []
    for name, section in [('CLAUDE.md', 'Technology Stack'),
                          ('.claude/docs/technical-preferences.md', 'Engine & Language')]:
        text = read(name)
        if text is not None and _configured_engine(text, section):
            game.append(name)
    concept = read('design/gdd/game-concept.md')
    if concept is not None and _meaningful(concept):
        game.append('design/gdd/game-concept.md')
    if result['stage'] in GAME_STAGES:
        game.append('production/stage.txt')
    godot = read('project.godot')
    if godot and re.search(r'^config/name\s*=\s*"[^"\n]+"', godot, re.M) and '[application]' in godot:
        game.append('project.godot')
    unity = read('ProjectSettings/ProjectVersion.txt')
    if unity and re.search(r'^m_EditorVersion:\s*\d+\.\d+\.', unity, re.M):
        game.append('ProjectSettings/ProjectVersion.txt')
    try:
        unreal_paths = sorted(p.name for p in root.iterdir() if p.suffix == '.uproject')
    except OSError as exc:
        errors.append(f'Cannot inspect project root: {exc}; restore read access.')
        unreal_paths = []
    for name in ['package.json', *unreal_paths]:
        text = read(name)
        if text is None:
            continue
        try:
            data = json.loads(text)
            if not isinstance(data, dict):
                raise ValueError('manifest must be a JSON object')
            if name.endswith('.uproject'):
                if type(data.get('FileVersion')) is int and data['FileVersion'] > 0:
                    game.append(name)
            else:
                for field in ('dependencies', 'devDependencies'):
                    deps = data.get(field, {})
                    if not isinstance(deps, dict):
                        raise ValueError(field + ' must be an object')
                    if any(isinstance(deps.get(engine), str) and deps[engine].strip()
                           for engine in ('phaser', 'three')):
                        game.append(name)
        except ValueError as exc:
            evidence.append(name)
            errors.append(f'{name}: {exc}; repair the manifest before classification.')
    evidence.extend(game)
    if result['source'] == 'explicit':
        if result['kind'] == 'tooling' and game:
            warnings.append('Explicit tooling has game evidence; resolve its scope before changing game configuration.')
        if ((result['kind'] == 'game' and result['stage'] == TOOL_STAGE)
                or (result['kind'] == 'tooling' and result['stage'] in GAME_STAGES)):
            warnings.append('Explicit kind and stage are incompatible; resolve the stage with the user without rewriting it automatically.')
    elif game:
        result.update(kind='game', source='game-evidence')
        if result['stage'] == TOOL_STAGE:
            warnings.append('Game evidence conflicts with Tooling Project stage; resolve the stage and component scope.')
    elif meaningful_spec:
        result.update(kind='tooling', source='tool-spec')
        warnings.append('Tooling candidate: confirm standalone or component scope before writing kind/stage.')
    elif result['stage'] == TOOL_STAGE:
        warnings.append('Tooling Project stage lacks a kind marker or meaningful tool spec; confirm scope with /setup-tool.')
    if result['kind'] == 'tooling' and spec is None:
        warnings.append('Create tools/TOOL_SPEC.md with /setup-tool before implementation.')
    if errors:
        result['kind'] = 'conflict'
        warnings.extend(errors)
    result['evidence'] = sorted(set(evidence))
    return result
