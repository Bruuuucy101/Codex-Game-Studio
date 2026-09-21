"""Explicit, non-installing web template copy with complete preflight."""
import hashlib
from pathlib import Path

ENGINES = {'phaser': 'phaser', 'phaser3': 'phaser', 'threejs': 'threejs',
           'three': 'threejs', 'three.js': 'threejs'}
PROTECTED = {'.git', '.codex', '.claude', '.agents'}
FILES = tuple(sorted((
    'README-WEB.md', 'package.json', 'package-lock.json', 'index.html',
    'tsconfig.json', 'vite.config.ts', 'vitest.config.ts', 'playwright.config.ts',
    'assets/data/game.json', 'src/core/step.ts', 'src/gameplay/game.ts',
    'src/gameplay/input.ts', 'src/scenes/collect.ts', 'src/ui/hud.ts',
    'src/main.ts', 'src/styles.css', 'tests/web-unit/game_test.ts',
    'tests/browser/game.spec.ts',
)))


def checked_target(value):
    """Validate spelling before Path can normalize suspicious components."""
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise ValueError('Invalid target path')
    parts = value.split('/')
    if '..' in parts or '//' in value or ('.' in parts and value != '.'):
        raise ValueError('Target must not contain traversal or redundant separators')
    if any(part.casefold() in PROTECTED for part in parts):
        raise ValueError('Protected metadata target')
    path = Path(value).absolute()
    if any(part.casefold() in PROTECTED for part in path.parts):
        raise ValueError('Protected metadata target')
    check_chain(path)
    return path


def check_chain(path):
    """Never resolve links; inspect every existing path component."""
    for item in (*reversed(path.parents), path):
        if item.is_symlink():
            raise ValueError(f'Symlink is not allowed: {item}')
        if item != path and item.exists() and not item.is_dir():
            raise ValueError(f'Parent is not a directory: {item}')


def copy_web(root, engine, target, write=False):
    if engine not in ENGINES:
        raise ValueError(f'Unknown web engine: {engine}')
    engine = ENGINES[engine]
    destination = checked_target(target)
    if destination.exists() and not destination.is_dir():
        raise ValueError(f'Target is not a directory: {destination}')
    source = Path(root).absolute() / 'templates' / 'web' / engine
    payloads = []
    for name in FILES:
        src, dst = source / name, destination / name
        check_chain(src)
        if not src.is_file():
            raise ValueError(f'Missing template file: {src}')
        check_chain(dst)
        if dst.exists():
            raise ValueError(f'Collision; nothing overwritten: {dst}')
        payloads.append((name, src.read_bytes()))
    result = {'status': 'COPIED' if write else 'PREVIEW', 'engine': engine,
              'target': str(destination), 'files': [
                  {'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                  for name, data in payloads]}
    if not write:
        return result
    created_files, created_dirs = [], []
    try:
        for name, data in payloads:
            dst = destination / name
            check_chain(dst)
            for directory in (*reversed(dst.parent.parents), dst.parent):
                if not directory.exists():
                    directory.mkdir()
                    created_dirs.append(directory)
            # Exclusive creation protects against new file collisions after preflight.
            with dst.open('xb') as handle:
                created_files.append(dst)
                handle.write(data)
    except (OSError, ValueError):
        for path in reversed(created_files):
            path.unlink()
        for path in reversed(created_dirs):
            # A concurrent creator may have populated this directory; preserve it.
            try:
                path.rmdir()
            except OSError:
                pass
        raise
    return result
