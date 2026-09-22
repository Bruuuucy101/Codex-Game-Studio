"""libGDX source contracts and real filesystem behavior; agent behavior is separate."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from ccgs import catalog, generate, scaffold

ROLES = {'libgdx-specialist', 'libgdx-scene2d-specialist', 'libgdx-graphics-specialist',
         'libgdx-ashley-specialist', 'libgdx-core-specialist'}


class LibGdxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT.parent)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.target = self.base / 'game with spaces'

    def copy(self, target=None, write=False):
        self.assertTrue(hasattr(scaffold, 'copy_libgdx'), 'Missing safe libGDX scaffold entry')
        return scaffold.copy_libgdx(ROOT, str(target or self.target), write=write)

    def test_full_native_roles_preserve_exact_original_identity_subsets(self):
        baseline = json.loads((ROOT / '.codex/upstream-lock.json').read_text())['files']
        original = {Path(p).stem for p in baseline if p.startswith('.claude/agents/') and p.endswith('.md')}
        original_skills = {Path(p).parent.name for p in baseline if p.startswith('.claude/skills/') and p.endswith('/SKILL.md')}
        rows = catalog.inventory(ROOT)
        self.assertEqual({r['name'] for r in rows['agents']}, original | ROLES | {'phaser-specialist', 'threejs-specialist', 'game-pipeline-developer'})
        self.assertEqual({r['name'] for r in rows['skills']}, original_skills | {'setup-tool', 'board-sync', 'npc-voice'})
        files = generate.render(ROOT)
        for name in ROLES:
            meta, body = catalog.frontmatter((ROOT / f'.claude/agents/{name}.md').read_text())
            text = files[f'.codex/agents/ccgs-{name}.toml']
            instructions = json.loads(next(line.partition(' = ')[2] for line in text.splitlines() if line.startswith('developer_instructions = ')))
            self.assertIn(body, instructions)
            self.assertEqual(meta['tools'], 'Read, Glob, Grep, Write, Edit, Bash, Task')
            self.assertEqual(int(meta['maxTurns']), 20)

    def test_configured_routing_resolves_all_real_delegates(self):
        text = (ROOT / '.claude/skills/setup-engine/SKILL.md').read_text()
        self.assertIn('### libgdx routing', text)
        block = text.split('### libgdx routing', 1)[1].split('```markdown', 1)[1].split('```', 1)[0]
        fields = dict(re.findall(r'^- \*\*([^*]+)\*\*: ([a-z][a-z0-9-]+)$', block, re.M))
        self.assertEqual(fields['Primary'], 'libgdx-specialist')
        self.assertEqual(fields['Shader Specialist'], 'libgdx-graphics-specialist')
        self.assertEqual(fields['UI Specialist'], 'libgdx-scene2d-specialist')
        routes = set(re.findall(r'^\|[^|]+\| ([a-z][a-z0-9-]+) \|$', block, re.M))
        self.assertTrue(ROLES <= routes)
        actual = {r['name'] for r in catalog.inventory(ROOT)['agents']}
        self.assertTrue(routes <= actual)

    def test_references_and_behavioral_spec_catalog_resolve(self):
        behavior = (ROOT / 'CCGS Skill Testing Framework/catalog.yaml').read_text()
        for name in ROLES:
            path = ROOT / f'.claude/agents/{name}.md'
            self.assertTrue(path.is_file(), name)
            for link in re.findall(r'`(docs/engine-reference/[^`]+\.md)`', path.read_text()):
                self.assertTrue((ROOT / link).is_file(), link)
            spec = f'CCGS Skill Testing Framework/agents/engine/libgdx/{name}.md'
            self.assertIn('spec: ' + spec, behavior)
            self.assertTrue((ROOT / spec).is_file())

    def test_real_module_paths_receive_rules_without_losing_root_rules(self):
        cases = {
            'core/src/main/java/com/game/gameplay/Player.java': 'gameplay-code',
            'core/src/main/kotlin/com/game/ui/Menu.kt': 'ui-code',
            'core/src/main/java/com/game/core/Assets.java': 'engine-code',
            'lwjgl3/src/main/java/com/game/Desktop.java': 'engine-code',
            'desktop/src/main/java/com/game/DesktopLauncher.java': 'engine-code',
            'desktop/src/test/java/com/game/LauncherTest.java': 'test-standards',
            'headless/src/test/java/com/game/LifecycleTest.java': 'test-standards',
            'android/assets/data/player_stats.json': 'data-files',
            'src/gameplay/player.gd': 'gameplay-code',
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertIn(expected, {r['name'] for r in catalog.rules_for(ROOT, [path])})
        for bundled in ('templates/libgdx/core/src/main/java/com/game/gameplay/Player.java',
                        'templates/libgdx/desktop/src/main/java/com/game/DesktopLauncher.java',
                        'templates/libgdx/desktop/src/test/java/com/game/LauncherTest.java'):
            self.assertEqual(catalog.rules_for(ROOT, [bundled]), [], bundled)

    def test_preview_and_binary_executable_copy_preserve_studio(self):
        preview = self.copy()
        self.assertFalse(self.target.exists())
        self.target.mkdir()
        for name in ('README.md', '.gitignore', 'CLAUDE.md'):
            (self.target / name).write_text('keep')
        result = self.copy(write=True)
        self.assertEqual(preview['files'], result['files'])
        for row in result['files']:
            source = ROOT / 'templates/libgdx' / row['path']
            dest = self.target / row['path']
            self.assertEqual(dest.read_bytes(), source.read_bytes())
            self.assertEqual(dest.stat().st_mode & 0o777, source.stat().st_mode & 0o777)
        jar = self.target / 'gradle/wrapper/gradle-wrapper.jar'
        self.assertEqual(hashlib.sha256(jar.read_bytes()).hexdigest(), '7d3a4ac4de1c32b59bc6a4eb8ecb8e612ccd0cf1ae1e99f66902da64df296172')
        self.assertTrue((self.target / 'gradlew').stat().st_mode & 0o111)
        for name in ('README.md', '.gitignore', 'CLAUDE.md'):
            self.assertEqual((self.target / name).read_text(), 'keep')

    def test_all_libgdx_collisions_abort_before_any_copy(self):
        for row in self.copy()['files']:
            path = self.target / row['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'keep\x00\xff')
            before = sorted(p.relative_to(self.target).as_posix() for p in self.target.rglob('*'))
            with self.assertRaises(ValueError):
                self.copy(write=True)
            self.assertEqual(before, sorted(p.relative_to(self.target).as_posix() for p in self.target.rglob('*')))
            self.assertEqual(path.read_bytes(), b'keep\x00\xff')
            shutil.rmtree(self.target)

    def test_libgdx_reuses_protected_path_and_symlink_checks(self):
        self.assertTrue(hasattr(scaffold, 'copy_libgdx'))
        for name in ('../escape', 'foo//bar', '.git/game', '.codex/game'):
            with self.assertRaises(ValueError):
                scaffold.copy_libgdx(ROOT, name, write=True)
        self.target.mkdir()
        real = self.base / 'real'
        real.mkdir()
        (self.target / 'gradle').symlink_to(real, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.copy(write=True)
        self.assertEqual(list(real.iterdir()), [])

    def test_mode_copy_failure_rolls_back_new_files(self):
        self.target.mkdir()
        (self.target / 'keep').write_text('keep')
        self.assertTrue(hasattr(scaffold, 'copy_libgdx'))
        with patch.object(Path, 'chmod', side_effect=OSError('mode failure')):
            with self.assertRaises(OSError):
                self.copy(write=True)
        self.assertEqual([p.name for p in self.target.iterdir()], ['keep'])

    def test_cli_is_read_only_without_write(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tools/ccgs_codex.py'), 'scaffold-libgdx', '--target', str(self.target)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['engine'], 'libgdx')
        self.assertFalse(self.target.exists())

    def test_module_source_discovery_excludes_bundled_build_and_test_code(self):
        paths = ['src/Game.java', 'core/src/main/kotlin/example/Game.kt', 'lwjgl3/src/main/java/example/Desktop.java',
                 'headless/src/main/java/example/Runner.java', 'android/src/main/java/example/Android.java',
                 'core/src/test/java/example/GameTest.java', 'core/src/main/java/vendor/External.java',
                 'templates/libgdx/core/src/main/java/Game.java', 'examples/Example.kt', 'core/build/Generated.java']
        for name in paths:
            path = self.base / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('// fixture')
        command = [sys.executable, str(ROOT / 'tools/ccgs_codex.py'), '--root', str(self.base), 'source-files']
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['files'], sorted(paths[:5]))

    def test_real_hook_recognizes_module_java_kotlin_and_ignores_templates(self):
        hook = ROOT / '.claude/hooks/detect-gaps.sh'
        path = self.base / 'templates/libgdx/core/src/main/java/Game.java'
        path.parent.mkdir(parents=True)
        path.write_text('// bundled only')
        fresh = subprocess.run(['bash', str(hook)], cwd=self.base, capture_output=True, text=True)
        self.assertIn('NEW PROJECT', fresh.stdout)
        path = self.base / 'core/src/main/kotlin/game/Game.kt'
        path.parent.mkdir(parents=True)
        path.write_text('// real adopted code')
        adopted = subprocess.run(['bash', str(hook)], cwd=self.base, capture_output=True, text=True)
        self.assertNotIn('NEW PROJECT', adopted.stdout)


if __name__ == '__main__':
    unittest.main()
