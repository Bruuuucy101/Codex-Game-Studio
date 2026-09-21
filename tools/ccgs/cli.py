"""Local, non-installing diagnostics for the studio adapter."""
import argparse
import json
from pathlib import Path
import platform
import shutil
import sys
from . import adr, catalog, generate
from .provenance import verify_upstream


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def upstream_drift(root):
    return verify_upstream(root)


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
    check.add_argument('--strict-upstream', action='store_true', help='Require pinned upstream bytes or exact recorded reviewed patches.')
    check.add_argument('--pristine-upstream', action='store_true', help='Require every baseline source file to remain byte-identical to upstream.')
    sub.add_parser('doctor', help='Inspect files/dependencies; does not certify live hook trust or model behavior.')
    sub.add_parser('status', help='Show actual original project state.')
    rules = sub.add_parser('rules', help='Print complete original rules applicable to paths.')
    rules.add_argument('paths', nargs='+')
    role = sub.add_parser('role', help='Print complete composed instructions for an original role name.')
    role.add_argument('name')
    workflow = sub.add_parser('workflow', help='Print a complete original workflow with runtime contract.')
    workflow.add_argument('name')
    context = sub.add_parser('adr-context', help='Read current ADR metadata or bounded, hash-pinned section pages.')
    context.add_argument('path')
    context.add_argument('--metadata-only', action='store_true')
    context.add_argument('--section', action='append', default=[])
    context.add_argument('--offset', type=int, default=0)
    context.add_argument('--limit', type=int, default=adr.DEFAULT_LIMIT)
    context.add_argument('--expected-sha256')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == 'adr-context':
            emit(adr.read_context(root, args.path, sections=args.section,
                                  metadata_only=args.metadata_only, offset=args.offset,
                                  limit=args.limit, expected_sha256=args.expected_sha256))
        elif args.command == 'generate':
            files = generate.write(root)
            emit({'generated': len(files), 'check': generate.check(root)})
        elif args.command == 'check':
            errors = generate.check(root)
            if args.pristine_upstream:
                errors += verify_upstream(root, pristine=True)
            elif args.strict_upstream:
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
                  'upstream_drift': upstream_drift(root),
                  'upstream_pristine_drift': verify_upstream(root, pristine=True),
                  'upstream_scope': 'reported separately: pinned or reviewed source integrity; pristine upstream byte equality',
                  'dependencies': dependencies,
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
