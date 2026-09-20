"""Local, non-installing diagnostics for the studio adapter."""
import argparse
import json
from pathlib import Path
import platform
import shutil
import sys
from . import catalog, generate


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def upstream_drift(root):
    lock = root / '.codex/upstream-lock.json'
    if not lock.exists():
        return ['MISSING .codex/upstream-lock.json']
    errors = []
    for name, digest in json.loads(lock.read_text())['files'].items():
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()):
            errors.append('INVALID_BASELINE_PATH ' + name)
        elif not path.is_file():
            errors.append('UPSTREAM_MISSING ' + name)
        elif catalog.sha256(path.read_bytes()) != digest:
            errors.append('UPSTREAM_CHANGED ' + name)
    return errors


def status(root):
    def read(name, fallback):
        path = root / name
        return path.read_text().strip() if path.exists() else fallback
    return {'stage': read('production/stage.txt', 'not configured'),
            'review_mode': read('production/review-mode.txt', 'not configured; resolve in the original workflow'),
            'active_state': read('production/session-state/active.md', 'no saved session'),
            'context_usage': 'not exposed by this command'}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Complete-source CCGS Codex adapter; no global installation.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('generate', help='Regenerate owned adapters after deliberate source changes.')
    check = sub.add_parser('check', help='Reject stale/missing generated entry points.')
    check.add_argument('--strict-upstream', action='store_true', help='Require all original files to match the pinned baseline.')
    sub.add_parser('doctor', help='Inspect files/dependencies; does not certify live hook trust or model behavior.')
    sub.add_parser('status', help='Show actual original project state.')
    rules = sub.add_parser('rules', help='Print complete original rules applicable to paths.')
    rules.add_argument('paths', nargs='+')
    role = sub.add_parser('role', help='Print complete composed instructions for an original role name.')
    role.add_argument('name')
    workflow = sub.add_parser('workflow', help='Print a complete original workflow with runtime contract.')
    workflow.add_argument('name')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == 'generate':
            files = generate.write(root)
            emit({'generated': len(files), 'check': generate.check(root)})
        elif args.command == 'check':
            errors = generate.check(root)
            if args.strict_upstream:
                errors += upstream_drift(root)
            emit({'status': 'FAIL' if errors else 'PASS', 'errors': errors,
                  'scope': 'source and adapter integrity only'})
            return bool(errors)
        elif args.command == 'doctor':
            rows = catalog.inventory(root)
            errors = generate.check(root)
            dependencies = {name: shutil.which(name) for name in ('git', 'bash', 'python3', 'codex', 'jq')}
            missing = [name for name in ('git', 'bash', 'python3') if not dependencies[name]]
            missing_files = [p for p in ('AGENTS.md', 'tools/ccgs_hooks.py', '.codex/hooks.json', '.codex/config.toml') if not (root / p).is_file()]
            problems = errors + ['MISSING_DEPENDENCY ' + x for x in missing] + ['MISSING ' + x for x in missing_files]
            emit({'status': 'FAIL' if problems else 'STRUCTURAL_PASS_RUNTIME_UNVERIFIED',
                  'counts': {k: len(v) for k, v in rows.items()}, 'errors': problems,
                  'upstream_drift': upstream_drift(root), 'dependencies': dependencies,
                  'host': platform.system(), 'python': platform.python_version(),
                  'runtime': {'hook_trust': 'not verified', 'native_role_loading': 'not verified',
                              'game_engine_behavior': 'not verified'},
                  'next': 'Open the project in Codex; review project and hooks with /hooks. See README-CODEX.zh-CN.md.'})
            return bool(problems)
        elif args.command == 'status':
            emit(status(root))
        elif args.command == 'rules':
            for row in catalog.rules_for(root, args.paths):
                print('\nSource: ' + row['source'])
                print((root / row['source']).read_text())
        else:
            category = 'agents' if args.command == 'role' else 'skills'
            name = args.name.removeprefix('ccgs-')
            row = next((r for r in catalog.inventory(root)[category] if r['name'] == name), None)
            if row is None:
                raise ValueError('Unknown role' if category == 'agents' else 'Unknown workflow')
            if category == 'agents':
                text = generate.render(root)[f'.codex/agents/ccgs-{name}.toml']
                value = next(x.partition(' = ')[2] for x in text.splitlines() if x.startswith('developer_instructions = '))
                print(json.loads(value))
            else:
                print((root / generate.RUNTIME).read_text())
                print('\nCOMPLETE ORIGINAL WORKFLOW: ' + row['source'])
                print((root / row['source']).read_text())
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        emit({'status': 'FAIL', 'error': str(exc)})
        return 1
