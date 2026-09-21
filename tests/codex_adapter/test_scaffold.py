"""Filesystem integration coverage for the non-installing scaffold copier."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from ccgs import scaffold


class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT.parent)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.target = self.base / 'game with spaces'

    def test_preview_and_copy_exact_bytes_for_both_engines(self):
        for engine in ('phaser', 'threejs'):
            target = self.target / engine
            preview = scaffold.copy_web(ROOT, engine, str(target))
            self.assertGreater(len(preview['files']), 0)
            self.assertFalse(target.exists())
            result = scaffold.copy_web(ROOT, engine, str(target), write=True)
            self.assertEqual(preview['files'], result['files'])
            actual = sorted(p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file())
            self.assertEqual(actual, [row['path'] for row in result['files']])
            for row in result['files']:
                data = (target / row['path']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
                self.assertEqual(len(data), row['bytes'])
                self.assertEqual(data, (ROOT / 'templates/web' / engine / row['path']).read_bytes())

    def test_reject_invalid_engine_and_paths_without_creating_target(self):
        for engine in ('unknown', '../phaser', 'Phaser', ''):
            with self.assertRaises(ValueError):
                scaffold.copy_web(ROOT, engine, str(self.target), write=True)
        for name in ('', 'x/../game', 'x\\game', 'x//game', 'x/./game', 'bad\x00name'):
            with self.assertRaises(ValueError):
                scaffold.copy_web(ROOT, 'phaser', name, write=True)
        for meta in ('.git', '.codex', '.claude', '.agents'):
            with self.assertRaises(ValueError):
                scaffold.copy_web(ROOT, 'phaser', str(self.base / meta / 'nested'), write=True)
        self.assertFalse(self.target.exists())

    def test_all_file_collisions_are_preflighted(self):
        manifest = scaffold.copy_web(ROOT, 'phaser', str(self.target))['files']
        for row in manifest:
            with self.subTest(path=row['path']):
                path = self.target / row['path']
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('keep')
                before = sorted(str(p.relative_to(self.target)) for p in self.target.rglob('*'))
                for write in (False, True):
                    with self.assertRaises(ValueError):
                        scaffold.copy_web(ROOT, 'phaser', str(self.target), write=write)
                self.assertEqual(before, sorted(str(p.relative_to(self.target)) for p in self.target.rglob('*')))
                self.assertEqual(path.read_text(), 'keep')
                shutil.rmtree(self.target)

    def test_existing_studio_and_repeat_invocation_are_safe(self):
        self.target.mkdir()
        for name in ('README.md', '.gitignore', 'CLAUDE.md'):
            (self.target / name).write_text('studio')
        scaffold.copy_web(ROOT, 'three', str(self.target), write=True)
        with self.assertRaises(ValueError):
            scaffold.copy_web(ROOT, 'threejs', str(self.target), write=True)
        for name in ('README.md', '.gitignore', 'CLAUDE.md'):
            self.assertEqual((self.target / name).read_text(), 'studio')

    def test_file_as_destination_ancestor_rejected_without_damage(self):
        self.target.mkdir()
        (self.target / 'src').write_text('keep')
        with self.assertRaises(ValueError):
            scaffold.copy_web(ROOT, 'phaser', str(self.target), write=True)
        self.assertEqual(list(self.target.iterdir()), [self.target / 'src'])

    def test_source_and_destination_symlinks_rejected(self):
        source = self.base / 'source'
        shutil.copytree(ROOT / 'templates/web', source / 'templates/web',
                        ignore=shutil.ignore_patterns('node_modules', 'dist', 'test-results', 'playwright-report'))
        for relative in ('templates/web/phaser/package.json', 'templates/web/phaser/src', 'templates/web/phaser'):
            path = source / relative
            backup = path.with_name(path.name + '-real')
            path.rename(backup)
            path.symlink_to(backup, target_is_directory=backup.is_dir())
            with self.assertRaises(ValueError):
                scaffold.copy_web(source, 'phaser', str(self.target), write=True)
            path.unlink()
            backup.rename(path)
        real = self.base / 'real'
        real.mkdir()
        self.target.symlink_to(real, target_is_directory=True)
        with self.assertRaises(ValueError):
            scaffold.copy_web(ROOT, 'phaser', str(self.target / 'nested'), write=True)
        self.target.unlink()
        self.target.mkdir()
        (self.target / 'src').symlink_to(real, target_is_directory=True)
        with self.assertRaises(ValueError):
            scaffold.copy_web(ROOT, 'phaser', str(self.target), write=True)
        self.assertEqual(list(real.iterdir()), [])

    def test_mid_write_failure_rolls_back_only_new_files_and_directories(self):
        self.target.mkdir()
        (self.target / 'src').mkdir()
        (self.target / 'keep.txt').write_text('keep')
        original = Path.open
        writes = 0
        def failing_open(path, mode='r', *args, **kwargs):
            nonlocal writes
            if mode == 'xb':
                writes += 1
                if writes == 3:
                    raise OSError('injected disk failure')
            return original(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', failing_open):
            with self.assertRaises(OSError):
                scaffold.copy_web(ROOT, 'phaser', str(self.target), write=True)
        self.assertEqual(sorted(p.name for p in self.target.iterdir()), ['keep.txt', 'src'])
        self.assertEqual(list((self.target / 'src').iterdir()), [])

    def test_relative_target_cannot_hide_protected_working_directory(self):
        import os
        protected = self.base / '.codex'
        protected.mkdir()
        previous = Path.cwd()
        try:
            os.chdir(protected)
            with self.assertRaises(ValueError):
                scaffold.copy_web(ROOT, 'phaser', '.', write=True)
        finally:
            os.chdir(previous)
        self.assertEqual(list(protected.iterdir()), [])

    def test_symlink_file_target_and_source_root_are_rejected(self):
        real = self.base / 'real.json'
        real.write_text('keep')
        self.target.mkdir()
        (self.target / 'package.json').symlink_to(real)
        with self.assertRaises(ValueError):
            scaffold.copy_web(ROOT, 'phaser', str(self.target), write=True)
        self.assertEqual(real.read_text(), 'keep')
        link = self.base / 'linked-root'
        link.symlink_to(ROOT, target_is_directory=True)
        command = [sys.executable, str(ROOT / 'tools/ccgs_codex.py'), '--root', str(link),
                   'scaffold-web', 'phaser', '--target', str(self.base / 'new')]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Symlink', json.loads(result.stdout)['error'])

    def test_cli_emits_json_and_nonzero_error(self):
        command = [sys.executable, str(ROOT / 'tools/ccgs_codex.py'), 'scaffold-web']
        good = subprocess.run(command + ['phaser3', '--target', str(self.target)], capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
        self.assertEqual(json.loads(good.stdout)['engine'], 'phaser')
        self.assertFalse(self.target.exists())
        bad = subprocess.run(command + ['bad', '--target', str(self.target)], capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertEqual(json.loads(bad.stdout)['status'], 'FAIL')
