"""Explicit, non-installing template copy with complete preflight."""
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
    'src/main.ts', 'src/styles.css', 'src/core/page-lifecycle.ts',
    'tests/web-unit/game_test.ts', 'tests/web-unit/input_test.ts',
    'tests/web-unit/lifecycle_test.ts',
    'tests/browser/game.spec.ts',
)))


LIBGDX_FILES = tuple(sorted((
    'README-LIBGDX.md',
    'THIRD-PARTY-NOTICES.md',
    'settings.gradle',
    'build.gradle',
    'gradlew',
    'gradlew.bat',
    'gradle/wrapper/gradle-wrapper.jar',
    'gradle/wrapper/gradle-wrapper.properties',
    'assets/data/game_config.json',
    'assets/i18n/messages.properties',
    'core/build.gradle',
    'headless/build.gradle',
    'lwjgl3/build.gradle',
    'core/gradle.lockfile',
    'headless/gradle.lockfile',
    'lwjgl3/gradle.lockfile',
    'core/src/main/java/studio/collect/gameplay/GameConfig.java',
    'core/src/main/java/studio/collect/gameplay/CollectState.java',
    'core/src/main/java/studio/collect/gameplay/CollectGame.java',
    'core/src/test/java/studio/collect/gameplay/CollectStateTest.java',
    'headless/src/main/java/studio/collect/headless/HeadlessRunner.java',
    'headless/src/main/java/studio/collect/headless/HeadlessLauncher.java',
    'headless/src/test/java/studio/collect/headless/HeadlessLifecycleTest.java',
    'lwjgl3/src/main/java/studio/collect/desktop/DesktopLauncher.java',
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
    return copy_template(Path(root).absolute() / 'templates' / 'web' / engine,
                         FILES, engine, target, write)


def copy_libgdx(root, target, write=False):
    return copy_template(Path(root).absolute() / 'templates' / 'libgdx',
                         LIBGDX_FILES, 'libgdx', target, write)


def copy_template(source, names, engine, target, write=False):
    destination = checked_target(target)
    if destination.exists() and not destination.is_dir():
        raise ValueError(f'Target is not a directory: {destination}')
    payloads = []
    for name in names:
        src, dst = source / name, destination / name
        check_chain(src)
        if not src.is_file():
            raise ValueError(f'Missing template file: {src}')
        check_chain(dst)
        if dst.exists():
            raise ValueError(f'Collision; nothing overwritten: {dst}')
        payloads.append((name, src.read_bytes(), src.stat().st_mode & 0o777))
    result = {'status': 'COPIED' if write else 'PREVIEW', 'engine': engine,
              'target': str(destination), 'files': [
                  {'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'mode': format(mode, '04o')}
                  for name, data, mode in payloads]}
    if not write:
        return result
    created_files, created_dirs = [], []
    try:
        for name, data, mode in payloads:
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
            dst.chmod(mode)
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
