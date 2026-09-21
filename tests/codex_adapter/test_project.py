"""Real filesystem classification and CLI boundary regressions."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
SPEC = '# Level exporter\n\n## Purpose\nConvert designer CSV levels to deterministic JSON.\n'


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def detect(self):
        try:
            from ccgs.project import detect_project_kind
        except ImportError:
            self.fail('Shared read-only project classifier is missing')
        return detect_project_kind(self.root)

    def test_pristine_adapter_and_arbitrary_scripts_are_unknown(self):
        for name in ('CLAUDE.md', '.claude/docs/technical-preferences.md'):
            self.put(name, (ROOT / name).read_text())
        self.put('tools/convert.py', 'raise RuntimeError("must never run")')
        self.put('tests/test_tool.py', '# not tool implementation evidence')
        self.put('templates/game/project.godot', '[application]\nconfig/name="Example"')
        self.put('examples/web/package.json', '{"dependencies":{"three":"0.183.2"}}')
        self.assertEqual(self.detect(), {'kind': 'unknown', 'source': 'none', 'evidence': [],
                                        'warnings': [], 'tool_spec': None, 'stage': None})

    def test_empty_and_placeholder_specs_are_gaps_not_tooling(self):
        for content in ('', '# Tool Spec\n## Purpose\n', '# Tool\n## Purpose\n[DESCRIBE PURPOSE]\n',
                        '# Tool\n<!-- Convert CSV to JSON -->\n## Purpose\nTODO\n'):
            with self.subTest(content=content):
                self.put('tools/TOOL_SPEC.md', content)
                result = self.detect()
                self.assertEqual(result['kind'], 'unknown')
                self.assertEqual(result['tool_spec'], 'tools/TOOL_SPEC.md')
                self.assertTrue(result['warnings'])

    def test_actual_tool_template_preserves_every_untouched_contract_gap(self):
        template = (ROOT / '.claude/docs/templates/tool-spec.md').read_text()
        sections = {'Scope', 'Purpose', 'Runtime and Dependencies', 'Engine Target',
                    'Input', 'Output', 'Usage', 'Determinism', 'Failure Behavior',
                    'Examples', 'Acceptance Criteria', 'Tests', 'Decisions', 'Evidence'}
        placeholder = '[Problem, users, workflow/pipeline position, upstream producer and downstream consumer.]'
        self.assertIn(placeholder, template)
        for purpose in (None, 'Convert designer CSV levels to deterministic JSON.'):
            with self.subTest(purpose=purpose):
                self.put('tools/TOOL_SPEC.md', template if purpose is None else template.replace(placeholder, purpose))
                result = self.detect()
                self.assertEqual(result['kind'], 'unknown' if purpose is None else 'tooling')
                warning = next(w for w in result['warnings'] if w.startswith('Complete tools/TOOL_SPEC.md'))
                gaps = set(warning.split(': ', 1)[1].split('. Content', 1)[0].split(', '))
                self.assertEqual(gaps, sections if purpose is None else sections - {'Purpose'})

    def test_wrapping_a_purpose_placeholder_does_not_change_project_kind(self):
        for purpose in ('[Problem, users and pipeline position.]',
                        '[Problem, users and\npipeline position.]',
                        '[Problem, users and\n    pipeline position.]'):
            with self.subTest(purpose=purpose):
                self.put('tools/TOOL_SPEC.md', '# Tool\n## Purpose\n' + purpose + '\n')
                result = self.detect()
                self.assertEqual((result['kind'], result['source']), ('unknown', 'none'))
                self.assertTrue(any('Purpose' in warning for warning in result['warnings']))

    def test_fenced_json_array_is_real_contract_example_content(self):
        self.put('tools/TOOL_SPEC.md', SPEC + '## Examples\n```json\n[\n  {"id":"a","x":1}\n]\n```\n')
        result = self.detect()
        self.assertEqual(result['kind'], 'tooling')
        gaps = next(w for w in result['warnings'] if w.startswith('Complete tools/TOOL_SPEC.md'))
        self.assertNotIn('Examples', gaps)

    def test_meaningful_spec_is_candidate_with_missing_contract_gaps(self):
        self.put('tools/TOOL_SPEC.md', SPEC)
        result = self.detect()
        self.assertEqual(result['kind'], 'tooling')
        self.assertEqual(result['source'], 'tool-spec')
        self.assertEqual(result['evidence'], ['tools/TOOL_SPEC.md'])
        self.assertTrue(any('candidate' in w.lower() for w in result['warnings']))
        self.assertTrue(any('Input' in w for w in result['warnings']))

    def test_complete_contract_recognizes_fenced_examples(self):
        sections = ('Scope', 'Purpose', 'Runtime and Dependencies', 'Engine Target',
                    'Input', 'Output', 'Usage', 'Determinism', 'Failure Behavior',
                    'Acceptance Criteria', 'Tests', 'Decisions', 'Evidence')
        content = '# Level exporter\n' + ''.join('## ' + name + '\nConcrete documented contract.\n' for name in sections)
        content += '## Examples\n```csv\nid,x,y,type\na,1,2,enemy\n```\n'
        self.put('tools/TOOL_SPEC.md', content)
        self.put('production/project-kind.txt', 'tooling\n')
        self.assertEqual(self.detect()['warnings'], [])

    def test_exact_marker_bytes_reject_crlf(self):
        self.put('production/project-kind.txt', 'tooling')
        (self.root / 'production/project-kind.txt').write_bytes(b'tooling\r\n')
        self.assertEqual(self.detect()['kind'], 'conflict')

    def test_unreadable_or_nonregular_configuration_is_conflict(self):
        path = self.put('tools/TOOL_SPEC.md', SPEC)
        path.chmod(0)
        try:
            self.assertEqual(self.detect()['kind'], 'conflict')
        finally:
            path.chmod(0o600)
        path.unlink()
        path.mkdir()
        self.assertEqual(self.detect()['kind'], 'conflict')

    def test_explicit_marker_wins_and_preserves_contradictions(self):
        for kind, stage in (('tooling', 'Production'), ('game', 'Tooling Project')):
            with self.subTest(kind=kind):
                self.put('production/project-kind.txt', kind + '\n')
                self.put('production/stage.txt', stage + '\n')
                self.put('tools/TOOL_SPEC.md', SPEC)
                result = self.detect()
                self.assertEqual((result['kind'], result['source'], result['stage']), (kind, 'explicit', stage))
                self.assertTrue(any('stage' in w.lower() for w in result['warnings']))
                self.assertIn('production/stage.txt', result['evidence'])

    def test_explicit_tooling_without_spec_and_with_runtime_warns(self):
        self.put('production/project-kind.txt', 'tooling')
        self.put('project.godot', '[application]\nconfig/name="Real game"\n')
        result = self.detect()
        self.assertEqual(result['kind'], 'tooling')
        self.assertTrue(any('TOOL_SPEC' in w for w in result['warnings']))
        self.assertTrue(any('game evidence' in w.lower() for w in result['warnings']))
        self.assertIn('project.godot', result['evidence'])

    def test_all_game_stages_remain_authoritative_with_tool_component(self):
        self.put('tools/TOOL_SPEC.md', SPEC)
        for stage in ('Concept', 'Systems Design', 'Technical Setup', 'Pre-Production', 'Production', 'Polish', 'Release'):
            self.put('production/stage.txt', stage)
            result = self.detect()
            self.assertEqual((result['kind'], result['stage']), ('game', stage))

    def test_real_engine_manifests_outweigh_tool_contract(self):
        fixtures = {
            'project.godot': '[application]\nconfig/name="Maze"\n',
            'ProjectSettings/ProjectVersion.txt': 'm_EditorVersion: 6000.0.1f1\n',
            'Maze.uproject': '{"FileVersion":3,"EngineAssociation":"5.5"}',
            'package.json': '{"dependencies":{"phaser":"3.90.0"}}',
        }
        for path, value in fixtures.items():
            with self.subTest(path=path):
                source = self.put(path, value)
                self.put('tools/TOOL_SPEC.md', SPEC)
                result = self.detect()
                self.assertEqual((result['kind'], result['source']), ('game', 'game-evidence'))
                self.assertIn(path, result['evidence'])
                source.unlink()
        self.put('package.json', '{"devDependencies":{"three":"0.183.2"}}')
        self.assertEqual(self.detect()['kind'], 'game')

    def test_concept_metadata_without_body_is_not_game_evidence(self):
        self.put('design/gdd/game-concept.md', '---\ntitle: Game Concept\nstatus: template\n---\n# Game Concept\n[DESCRIBE]\n')
        self.assertEqual(self.detect()['kind'], 'unknown')

    def test_fenced_engine_configuration_is_only_an_example(self):
        self.put('CLAUDE.md', '# Studio\n## Technology Stack\n```markdown\n- **Engine**: Godot 4.4\n```\n')
        self.assertEqual(self.detect()['kind'], 'unknown')

    def test_reasoned_engine_absence_is_not_game_evidence(self):
        self.put('tools/TOOL_SPEC.md', SPEC)
        for path, section in (('CLAUDE.md', 'Technology Stack'),
                              ('.claude/docs/technical-preferences.md', 'Engine & Language')):
            for marked in (False, True):
                marker = self.root / 'production/project-kind.txt'
                if marked:
                    self.put('production/project-kind.txt', 'tooling\n')
                for value in ('N/A — standalone Python CSV/JSON tool; no engine runtime',
                              'None (standalone CLI)', 'Not configured — standalone tool',
                              'not-configured: no runtime needed', 'N/A', 'None'):
                    with self.subTest(path=path, marked=marked, value=value):
                        self.put(path, '## ' + section + '\n- **Engine**: ' + value + '\n')
                        result = self.detect()
                        self.assertEqual((result['kind'], result['source']),
                                         ('tooling', 'explicit' if marked else 'tool-spec'))
                        self.assertNotIn(path, result['evidence'])
                        self.assertFalse(any('game evidence' in w for w in result['warnings']))
                if marked:
                    marker.unlink()
            (self.root / path).unlink()

    def test_engine_absence_prefix_matching_preserves_real_and_custom_engines(self):
        self.put('tools/TOOL_SPEC.md', SPEC)
        for path, section in (('CLAUDE.md', 'Technology Stack'),
                              ('.claude/docs/technical-preferences.md', 'Engine & Language')):
            for value in ('Godot 4.4', 'Unity 6000.0.1f1', 'Unreal Engine 5.5',
                          'Phaser 3', 'Three.js', 'Custom C++ runtime', 'NoneSuch custom runtime'):
                with self.subTest(path=path, value=value):
                    self.put(path, '## ' + section + '\n- **Engine**: ' + value + '\n')
                    result = self.detect()
                    self.assertEqual((result['kind'], result['source']), ('game', 'game-evidence'))
                    self.assertIn(path, result['evidence'])
            (self.root / path).unlink()

    def test_configured_engine_field_and_meaningful_concept_not_prose_mentions(self):
        self.put('CLAUDE.md', '# Notes\nConsidering Unity or Godot some day.\n')
        self.put('design/gdd/game-concept.md', '# Game Concept\n[DESCRIBE]\n')
        self.assertEqual(self.detect()['kind'], 'unknown')
        for engine in ('Godot 4.4', 'Unity 6000.0.1f1', 'Unreal Engine 5.5', 'Phaser 3', 'Three.js', 'Custom C++ runtime'):
            self.put('CLAUDE.md', '# Studio\n## Technology Stack\n- **Engine**: ' + engine + '\n')
            self.assertEqual(self.detect()['kind'], 'game')
        self.put('CLAUDE.md', '# Notes\n## Other\n- **Engine**: Godot\n')
        self.assertEqual(self.detect()['kind'], 'unknown')
        self.put('design/gdd/game-concept.md', '# Maze\n## Core Loop\nExplore rooms and unlock doors with collected keys.\n')
        self.assertEqual(self.detect()['kind'], 'game')

    def test_invalid_marker_stage_encoding_and_json_fail_closed(self):
        cases = [('production/project-kind.txt', v) for v in ('', 'tools', 'GAME', ' game', 'game\n\n', 'game\ntooling')]
        cases += [('production/stage.txt', v) for v in ('', 'Done', 'Production\nPolish')]
        cases += [('package.json', '{invalid'), ('Maze.uproject', '[]')]
        for path, value in cases:
            with self.subTest(path=path, value=value):
                source = self.put(path, value)
                result = self.detect()
                self.assertEqual(result['kind'], 'conflict')
                self.assertIn(path, result['evidence'])
                self.assertTrue(result['warnings'])
                source.unlink()
        source = self.put('tools/TOOL_SPEC.md', '')
        source.write_bytes(b'\xff')
        self.assertEqual(self.detect()['kind'], 'conflict')

    def test_symlink_files_directories_root_and_invalid_path_are_rejected(self):
        external = self.put('outside.md', SPEC)
        link = self.root / 'tools'
        link.symlink_to(self.root, target_is_directory=True)
        self.assertEqual(self.detect()['kind'], 'conflict')
        link.unlink()
        self.put('tools/TOOL_SPEC.md', '').unlink()
        (link / 'TOOL_SPEC.md').symlink_to(external)
        self.assertEqual(self.detect()['kind'], 'conflict')
        from ccgs.project import detect_project_kind
        root_link = self.root / 'root-link'
        root_link.symlink_to(self.root, target_is_directory=True)
        self.assertEqual(detect_project_kind(root_link)['kind'], 'conflict')
        self.assertEqual(detect_project_kind(self.root / '..' / self.root.name)['kind'], 'conflict')

    def test_detection_does_not_write_or_execute(self):
        self.put('tools/TOOL_SPEC.md', SPEC)
        self.put('tools/run.py', 'from pathlib import Path; Path("EXECUTED").touch()')
        self.put('production/stage.txt', 'Tooling Project\n')
        self.put('production/project-kind.txt', 'tooling\n')
        before = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.root.rglob('*') if p.is_file()}
        for _ in range(2):
            self.assertEqual(self.detect()['kind'], 'tooling')
        after = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_status_does_not_read_through_rejected_root(self):
        self.put('production/session-state/active.md', 'outside-root-state-must-not-be-read')
        alias = self.root / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        result = subprocess.run([sys.executable, str(ROOT / 'tools/ccgs_codex.py'), '--root', str(alias), 'status'],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['project_kind']['kind'], 'conflict')
        self.assertNotIn('outside-root-state-must-not-be-read', result.stdout)

    def test_cli_and_status_expose_same_classification_and_conflict_exit(self):
        self.put('tools/TOOL_SPEC.md', SPEC)
        def run(command):
            return subprocess.run([sys.executable, str(ROOT / 'tools/ccgs_codex.py'), '--root', str(self.root), command],
                                  capture_output=True, text=True)
        direct = run('project-kind')
        self.assertEqual(direct.returncode, 0, direct.stderr)
        self.assertEqual(json.loads(direct.stdout), self.detect())
        status = run('status')
        self.assertEqual(json.loads(status.stdout)['project_kind'], self.detect())
        self.put('production/project-kind.txt', 'invalid')
        for command in ('project-kind', 'status'):
            result = run(command)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('conflict', result.stdout)
