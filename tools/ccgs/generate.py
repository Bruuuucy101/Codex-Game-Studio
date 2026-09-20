"""Generate thin full-source skill routes and lossless native role instructions."""
import json
from pathlib import Path
from .catalog import frontmatter, inventory, sha256

MANIFEST = '.codex/generated.json'
RUNTIME = 'docs/codex-adapter/runtime.md'


def encode(value):
    return json.dumps(value, ensure_ascii=False)


def safe_destination(root, relative):
    """Reject redirected outputs, including symlinked parent directories."""
    target = root / relative
    if not target.resolve().is_relative_to(root):
        raise ValueError('UNSAFE_GENERATED_PATH ' + relative)
    candidate = target
    while candidate != root:
        if candidate.is_symlink():
            raise ValueError('SYMLINK_GENERATED_PATH ' + relative)
        candidate = candidate.parent
    return target


def render(root):
    root = Path(root)
    rows = inventory(root)
    model_path = root / '.codex/ccgs-models.json'
    model_map = json.loads(model_path.read_text()) if model_path.exists() else {}
    if not isinstance(model_map, dict) or set(model_map) - {'opus', 'sonnet', 'haiku'}:
        raise ValueError('Model map must contain only original opus/sonnet/haiku tiers')
    for tier, settings in model_map.items():
        if not isinstance(settings, dict) or set(settings) - {'model', 'model_reasoning_effort'}:
            raise ValueError('Invalid model mapping for ' + tier)
        if not isinstance(settings.get('model'), str) or not settings['model'].strip():
            raise ValueError('Model mapping needs a nonempty model name')
        if settings.get('model_reasoning_effort') not in ('low', 'medium', 'high', 'xhigh', 'max', 'ultra'):
            raise ValueError('Model mapping needs an explicit supported reasoning effort')
    out = {}
    for row in rows['skills']:
        name, source = row['name'], row['source']
        description = row['metadata']['description']
        out[f'.agents/skills/ccgs-{name}/SKILL.md'] = f'''---
name: ccgs-{name}
description: {encode(description)}
---

# CCGS Codex entry: {name}

Source: `{source}` (relative to the project root).
SHA256: `{row['sha256']}`
Original metadata: {encode(row['metadata'])}

1. Locate the project root by walking up from this SKILL.md to `AGENTS.md` and `.claude/`. Resolve original project paths from that root, not the skill directory.
2. Read `{RUNTIME}` before interpreting Claude-specific instructions.
3. Read the COMPLETE `{source}` workflow, in chunks if needed; do not execute from this entry or description alone. Read its required references and matched rules. This entry is not a condensed replacement.
4. Execute every applicable phase, dependency check, review gate and recovery step from the original, using the compatibility contract. Preserve arguments, outputs, original role assignments, review mode and engine branches.
5. Treat `/workflow` references as the matching `ccgs-workflow` skill, or read the named original workflow when the host cannot invoke a skill from a skill. Pass arguments unchanged. Do not send legacy Claude slash commands to a shell.
6. If the original requires Task/subagents, delegate to real agents under the named source role; this skill explicitly requests delegation for those phases. Use bounded waves within host limits. If no delegation tools are available, report a blocker instead of silently role-playing the entire team.

The original workflow is authoritative for WHAT to do; the runtime contract translates HOW tools and lifecycle mechanisms operate in Codex. Source edits require `python3 tools/ccgs_codex.py generate`; generated entries are not edited by hand.
'''
    if not (root / RUNTIME).is_file():
        raise ValueError('Missing required runtime contract: ' + RUNTIME)
    runtime = (root / RUNTIME).read_text()
    for row in rows['agents']:
        name, source, meta = row['name'], row['source'], row['metadata']
        _, body = frontmatter((root / source).read_text())
        instructions = f'''You are the original CCGS {name} role running in Codex.
Source: {source}; SHA256: {row['sha256']}.
Original metadata (preserved; not native Codex configuration): {encode(meta)}

CODEX COMPATIBILITY CONTRACT
{runtime}

ROLE METADATA CONTRACT
Respect the original tool allowlist and disallowedTools as role policy. Read required files with the host file tools or narrow read-only shell commands; this transport is not permission to run arbitrary Bash for a role forbidding Bash. If a role needs a disallowed action, return a handoff to the authorized role. Original maxTurns is a bounded-work budget: report progress/blocker before exceeding the budget; the host does not expose identical turn enforcement. For a role with original memory enabled, first load its existing .claude/agent-memory/{name}/MEMORY.md and relevant linked memory files, then its Codex continuation at production/agent-memory/{name}.md. Preserve original memory files; record new durable decisions with source evidence in the Codex continuation when authorized. User-scoped memory remains explicit opt-in. Load the required original skills before work. Original worktree isolation requires a separate checkout if the runtime supports it; otherwise report the isolation blocker before writing. Inherit the parent Codex model; do not try to invoke opus/sonnet/haiku as Codex models.

COMPLETE ORIGINAL ROLE BODY (not summarized)
{body}'''
        out[f'.codex/agents/ccgs-{name}.toml'] = '\n'.join([
            '# Generated from unchanged CCGS source. Model deliberately inherited.',
            f'name = {encode("ccgs-" + name)}',
            f'description = {encode(meta["description"])}',
            *[f'{key} = {encode(value)}' for key, value in model_map.get(meta['model'], {}).items()],
            f'developer_instructions = {encode(instructions)}', ''])
    capability = {
        'schema_version': 1,
        'upstream': 'https://github.com/Donchitos/Claude-Code-Game-Studios',
        'baseline_commit': '984023ddac0d5e27624f2baacde6105e45de375f',
        'verification_contract': 'Source coverage is not runtime or behavioral certification. See validation.md.',
        'counts': {key: len(value) for key, value in rows.items()},
        'surfaces': rows,
        'host_differences': ['Notification event', 'custom statusLine UI', 'Claude model tiers',
                             'hard per-role tool allowlists/maxTurns', 'user-scoped memory',
                             'worktree scheduling and host concurrency', 'hook trust required'],
    }
    out['.codex/capabilities.json'] = json.dumps(capability, ensure_ascii=False, indent=2) + '\n'
    index = ['# CCGS complete capability inventory', '',
             'Generated from actual files. Counts prove coverage only; see [validation](validation.md) for execution evidence.', '']
    for category, items in rows.items():
        index += [f'## {category}: {len(items)}', '', '| Name | Original source | Codex route |', '|---|---|---|']
        for row in items:
            route = ('ccgs-' + row['name']) if category in ('skills', 'agents') else ('event bridge; see hooks.md' if category == 'hooks' else 'original file, preserved')
            if category == 'hooks' and row['name'] == 'notify':
                route = 'preserved; no identical native event; use host notifications'
            index.append(f"| {row['name']} | `{row['source']}` | {route} |")
        index.append('')
    out['docs/codex-adapter/capabilities.md'] = '\n'.join(index)
    return out


def check(root):
    root = Path(root).resolve()
    expected = render(root)
    errors = []
    try:
        for path in [*expected, MANIFEST]:
            safe_destination(root, path)
    except ValueError as exc:
        return [str(exc)]
    for path, text in expected.items():
        file = root / path
        if not file.is_file():
            errors.append('MISSING ' + path)
        elif file.read_text() != text:
            errors.append('STALE_OR_MODIFIED ' + path)
    manifest = root / MANIFEST
    if not manifest.is_file():
        errors.append('MISSING ' + MANIFEST)
    else:
        data = json.loads(manifest.read_text())
        for path in sorted(set(data['files']) - set(expected)):
            errors.append('SOURCE_REMOVED ' + path)
        wanted = {p: sha256(t.encode()) for p, t in expected.items()}
        if data['files'] != wanted:
            errors.append('STALE ' + MANIFEST)
    for pattern in ('.agents/skills/ccgs-*/SKILL.md', '.codex/agents/ccgs-*.toml'):
        for file in root.glob(pattern):
            path = file.relative_to(root).as_posix()
            if path not in expected:
                errors.append('UNEXPECTED ' + path)
    return errors


def write(root):
    root = Path(root).resolve()
    expected = render(root)
    for path in [*expected, MANIFEST]:
        safe_destination(root, path)
    manifest = root / MANIFEST
    previous = json.loads(manifest.read_text()).get('files', {}) if manifest.exists() else {}
    removed = set(previous) - set(expected)
    if removed:
        raise ValueError('Upstream sources removed; review before removing generated adapters: ' + ', '.join(sorted(removed)))
    # Preflight ALL paths before writing anything; never overwrite unrelated user work.
    for path, text in expected.items():
        file = root / path
        if file.exists() and path not in previous and file.read_text() != text:
            raise ValueError('Refusing to overwrite an unowned file: ' + path)
    for path, text in expected.items():
        file = root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)
    manifest.write_text(json.dumps({'schema_version': 1, 'files': {
        p: sha256(t.encode()) for p, t in expected.items()}}, indent=2) + '\n')
    return expected
