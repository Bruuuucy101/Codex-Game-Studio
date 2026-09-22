"""Local, non-installing diagnostics for the studio adapter."""
import argparse
import json
from pathlib import Path
import platform
import shutil
import sys
from . import adr, catalog, generate, project, scaffold
from .provenance import verify_upstream


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def upstream_drift(root):
    return verify_upstream(root)


def status(root):
    kind = project.detect_project_kind(root)
    def read(name, fallback):
        if kind['kind'] == 'conflict':
            return 'not read: resolve project-kind conflict first'
        path = root / name
        return path.read_text().strip() if path.exists() else fallback
    return {'project_kind': kind, 'stage': kind['stage'] or 'not configured',
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
    sub.add_parser('project-kind', help='Classify project kind read-only; report conflicting configuration.')
    sub.add_parser('status', help='Show actual original project state.')
    rules = sub.add_parser('rules', help='Print complete original rules applicable to paths.')
    rules.add_argument('paths', nargs='+')
    role = sub.add_parser('role', help='Print complete composed instructions for an original role name.')
    role.add_argument('name')
    workflow = sub.add_parser('workflow', help='Print a complete original workflow with runtime contract.')
    workflow.add_argument('name')
    web = sub.add_parser('scaffold-web', help='Preview or copy an explicit web template; never install packages.')
    web.add_argument('engine')
    web.add_argument('--target', required=True)
    web.add_argument('--write', action='store_true')
    libgdx = sub.add_parser('scaffold-libgdx', help='Preview or copy the pinned Java desktop/headless starter.')
    libgdx.add_argument('--target', required=True)
    libgdx.add_argument('--write', action='store_true')
    sub.add_parser('source-files', help='List actual game implementation source in root/conventional module roots.')
    context = sub.add_parser('adr-context', help='Read current ADR metadata or bounded, hash-pinned section pages.')
    context.add_argument('path')
    context.add_argument('--metadata-only', action='store_true')
    context.add_argument('--section', action='append', default=[])
    context.add_argument('--offset', type=int, default=0)
    context.add_argument('--limit', type=int, default=adr.DEFAULT_LIMIT)
    context.add_argument('--expected-sha256')
    board = sub.add_parser('board-sync', help='Optional GitHub Projects projection; default preview, explicit --write.')
    board_commands = board.add_subparsers(dest='board_command', required=True)
    snapshot = board_commands.add_parser('snapshot', help='Emit deterministic local JSON; no gh required.')
    snapshot.add_argument('--epic')
    setup = board_commands.add_parser('setup', help='Preview/adopt/create a private GitHub project.')
    setup.add_argument('--owner', required=True)
    setup.add_argument('--namespace', required=True)
    target = setup.add_mutually_exclusive_group(required=True)
    target.add_argument('--number', type=int)
    target.add_argument('--title')
    sync = board_commands.add_parser('sync', help='Preview or apply and verify current story differences.')
    sync.add_argument('--epic')
    for command in (setup, sync):
        mode = command.add_mutually_exclusive_group()
        mode.add_argument('--write', action='store_true')
        mode.add_argument('--dry', action='store_true', help='Explicit default: no local or remote writes.')
    assets = sub.add_parser('assets', help='Optional asset production; preview by default.', add_help=False)
    assets.add_argument('--help', action='store_true', dest='assets_help')
    assets.add_argument('asset_args', nargs=argparse.REMAINDER)
    voice = sub.add_parser('voice', help='Optional NPC voice generation; preview by default.', add_help=False)
    voice.add_argument('--help', action='store_true', dest='voice_help')
    voice.add_argument('voice_args', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    root = args.root.absolute() if args.command in ('scaffold-web', 'scaffold-libgdx', 'source-files', 'project-kind', 'status', 'board-sync', 'assets', 'voice') else args.root.resolve()
    try:
        if args.command == 'voice':
            from .voice.cli import main as voice_main
            return voice_main(root, ['--help'] if args.voice_help else args.voice_args)
        elif args.command == 'assets':
            from .assets.cli import main as assets_main
            return assets_main(root, ['--help'] if args.assets_help else args.asset_args)
        elif args.command == 'board-sync':
            if args.board_command == 'snapshot':
                from .board_snapshot import build_snapshot
                emit(build_snapshot(root, args.epic))
            else:
                from . import board_sync
                if args.board_command == 'setup':
                    emit(board_sync.setup(root, args.owner, args.namespace, number=args.number, title=args.title, write=args.write))
                else:
                    emit(board_sync.sync(root, args.epic, write=args.write))
        elif args.command == 'scaffold-web':
            emit(scaffold.copy_web(root, args.engine, args.target, write=args.write))
        elif args.command == 'scaffold-libgdx':
            emit(scaffold.copy_libgdx(root, args.target, write=args.write))
        elif args.command == 'source-files':
            emit({'files': project.source_files(root)})
        elif args.command == 'adr-context':
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
        elif args.command == 'project-kind':
            result = project.detect_project_kind(root)
            emit(result)
            return result['kind'] == 'conflict'
        elif args.command == 'status':
            result = status(root)
            emit(result)
            return result['project_kind']['kind'] == 'conflict'
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
