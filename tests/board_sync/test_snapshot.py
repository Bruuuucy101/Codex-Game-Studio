"""Local board snapshot integration tests; run separately with requirements-board."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from fixtures import file_hashes, sprint, story

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools'))
CLI = REPO / 'tools/ccgs_codex.py'


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def build(self, epic=None):
        return importlib.import_module('ccgs.board_snapshot').build_snapshot(self.root, epic)

    def validate(self, snapshot):
        return importlib.import_module('ccgs.board_snapshot').validate_snapshot(self.root, snapshot)

    def test_snapshot_cli_deterministic_without_gh_or_yaml(self):
        story(self.root)
        before = file_hashes(self.root)
        command = [sys.executable, '-S', str(CLI), '--root', str(self.root),
                   'board-sync', 'snapshot']
        runs = [subprocess.run(command, capture_output=True, text=True,
                               env={**os.environ, 'PATH': ''}) for _ in range(2)]
        self.assertEqual(runs[0].returncode, 0, runs[0].stdout + runs[0].stderr)
        self.assertEqual(runs[0].stdout, runs[1].stdout)
        self.assertEqual(json.loads(runs[0].stdout)['stories'][0]['normalized']['Stage'], 'Ready')
        self.assertEqual(file_hashes(self.root), before)

    def test_snapshot_canonical_header_preserves_evidence_and_hash(self):
        path = story(self.root, crlf=True, prefix='```markdown\n> **Status**: Done\n```\n')
        before = file_hashes(self.root)
        snap = self.build()
        row = snap['stories'][0]
        relative = 'production/epics/combat/story-001.md'
        self.assertEqual(row['path'], relative)
        self.assertEqual(row['identity_input'], relative)
        self.assertEqual(row['title'], 'Story 001: 跳跃 Jump')
        self.assertEqual(row['raw_metadata']['Epic'], '战斗 Combat')
        self.assertEqual(row['normalized'], {'Stage': 'Ready', 'Type': 'Logic', 'Size': 'S', 'Epic': 'combat'})
        self.assertEqual(row['status_source'], {'path': relative, 'field': 'Status', 'value': 'Ready'})
        self.assertEqual(snap['sources'][relative], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(snap['inventory'], [relative])
        self.assertEqual(self.build(), snap)
        self.assertIsNone(self.validate(snap))
        self.assertEqual(file_hashes(self.root), before)

    def test_snapshot_stage_mappings_are_explicit(self):
        cases = {'Not Started': 'Backlog', 'backlog': 'Backlog', 'Ready': 'Ready',
                 'ready-for-dev': 'Ready', 'In Progress': 'In Progress',
                 'in-progress': 'In Progress', 'in_progress': 'In Progress',
                 'In Review': 'In Review', 'review': 'In Review',
                 'Blocked': 'Blocked', 'Done': 'Done', 'Complete': 'Done', 'Deferred': 'Deferred'}
        for value, want in cases.items():
            with self.subTest(value=value):
                story(self.root, status=value)
                self.assertEqual(self.build()['stories'][0]['normalized']['Stage'], want)

    def test_snapshot_type_mappings_are_explicit(self):
        for value, want in [('Logic', 'Logic'), ('Integration', 'Integration'),
                            ('Visual/Feel', 'Visual'), ('Visual', 'Visual'),
                            ('UI', 'UI'), ('Config/Data', 'Config'), ('Config', 'Config')]:
            with self.subTest(value=value):
                story(self.root, kind=value)
                self.assertEqual(self.build()['stories'][0]['normalized']['Type'], want)

    def test_snapshot_size_boundaries_are_explicit(self):
        for value, want in [('XS', 'S'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'L'),
                            ('0.25h', 'S'), ('4 hours', 'S'), ('4.01 h', 'M'),
                            ('16h', 'M'), ('16.01 hours', 'L'), ('200 hour', 'L')]:
            with self.subTest(value=value):
                story(self.root, estimate=value)
                self.assertEqual(self.build()['stories'][0]['normalized']['Size'], want)

    def test_snapshot_ambiguous_estimates_fail_with_guidance(self):
        for value in ['2 days', '2-4h', 'TBD', '[hours or t-shirt size]', '0h', '-1h', 'NaN h', 'inf h', '4']:
            with self.subTest(value=value):
                story(self.root, estimate=value)
                with self.assertRaisesRegex(ValueError, 'hours|t-shirt'):
                    self.build()

    def test_snapshot_missing_duplicate_unknown_or_invalid_metadata_fails(self):
        for field in ['Epic', 'Status', 'Type', 'Estimate']:
            with self.subTest(field=field):
                path = story(self.root)
                path.write_text('\n'.join(line for line in path.read_text().splitlines() if f'**{field}**' not in line))
                with self.assertRaisesRegex(ValueError, field):
                    self.build()
                story(self.root, suffix=f'> **{field}**: Ready')
                with self.assertRaisesRegex(ValueError, 'duplicate|Duplicate'):
                    self.build()
        for kwargs in [{'status': 'Ready-ish'}, {'kind': 'Gameplay'}, {'label': '[epic name]'},
                       {'suffix': '> **Sttaus**: Done'}, {'label': ''}]:
            with self.subTest(kwargs=kwargs):
                story(self.root, **kwargs)
                with self.assertRaises(ValueError):
                    self.build()

    def test_snapshot_malformed_header_cannot_hide_duplicate_status(self):
        for suffix in ['> **Status:** Done', '> **Status** Done', '> **Sttaus** Done', '> Status Ready']:
            with self.subTest(suffix=suffix):
                story(self.root, suffix=suffix)
                with self.assertRaisesRegex(ValueError, 'METADATA'):
                    self.build()

    def test_snapshot_empty_project_and_independent_digest(self):
        snap = self.build()
        self.assertEqual(snap['stories'], [])
        self.assertEqual(snap['inventory'], [])
        self.assertEqual(snap['sources'], {})
        self.assertEqual(snap['schema_version'], 1)
        payload = {k: v for k, v in snap.items() if k != 'sha256'}
        expected = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                             separators=(',', ':')).encode()).hexdigest()
        self.assertEqual(snap['sha256'], expected)

    def test_snapshot_cli_yaml_and_exact_filter(self):
        story(self.root)
        story(self.root, epic='other')
        sprint(self.root, 'stories: [{file: production/epics/combat/story-001.md, status: review}]')
        before = file_hashes(self.root)
        result = subprocess.run([sys.executable, str(CLI), '--root', str(self.root),
                                 'board-sync', 'snapshot', '--epic', 'combat'],
                                text=True, capture_output=True, env={**os.environ, 'PATH': ''})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        snap = json.loads(result.stdout)
        self.assertEqual(snap['epic'], 'combat')
        self.assertEqual(len(snap['stories']), 1)
        self.assertEqual(snap['stories'][0]['normalized']['Stage'], 'In Review')
        self.assertEqual(file_hashes(self.root), before)

    def test_snapshot_title_missing_duplicate_placeholder_fails(self):
        for replacement in ['', '# [title]', '# Story 001: [title]', '# One\n# Two']:
            path = story(self.root)
            path.write_text(path.read_text().replace('# Story 001: 跳跃 Jump', replacement))
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                self.build()

    def test_snapshot_fences_and_body_are_not_metadata(self):
        for prefix in ['~~~md\n> **Status**: Done\n~~~\n', '> ```md\n> **Status**: Done\n> ```\n']:
            story(self.root, prefix=prefix, suffix='')
            self.assertEqual(self.build()['stories'][0]['normalized']['Stage'], 'Ready')

    def test_snapshot_repeated_numbers_and_exact_epic_filter(self):
        story(self.root)
        story(self.root, epic='combat-extra')
        snapshot = self.build('combat')
        self.assertEqual(len(snapshot['inventory']), 2)
        self.assertEqual([r['normalized']['Epic'] for r in snapshot['stories']], ['combat'])
        self.assertEqual(len({r['identity_input'] for r in self.build()['stories']}), 2)
        for epic in ['../combat', 'combat/../combat', '*', '', '/combat', 'combat\\x', 'COMBAT']:
            with self.subTest(epic=epic), self.assertRaises(ValueError):
                self.build(epic)

    def test_snapshot_yaml_actual_shape_overrides_header(self):
        story(self.root)
        yaml = sprint(self.root, 'sprint: 1\nupdated: 2026-09-21\nstories:\n'
                      '  - id: "1-1"\n    name: Jump\n    file: production/epics/combat/story-001.md\n'
                      '    priority: must-have\n    status: in_progress\n    owner: ""\n    estimate_days: 0\n')
        before = file_hashes(self.root)
        snap = self.build()
        row = snap['stories'][0]
        self.assertEqual(row['normalized']['Stage'], 'In Progress')
        self.assertEqual(row['raw_metadata']['Status'], 'Ready')
        self.assertEqual(row['status_source'], {'path': 'production/sprint-status.yaml', 'field': 'stories[0].status', 'value': 'in_progress'})
        self.assertTrue(row['warnings'])
        self.assertEqual(snap['sources']['production/sprint-status.yaml'], hashlib.sha256(yaml.read_bytes()).hexdigest())
        self.assertEqual(file_hashes(self.root), before)

    def test_snapshot_yaml_states_and_header_fallback(self):
        story(self.root)
        story(self.root, name='story-002.md', status='Blocked')
        for value, want in [('backlog', 'Backlog'), ('ready-for-dev', 'Ready'),
                            ('in-progress', 'In Progress'), ('review', 'In Review'),
                            ('done', 'Done'), ('blocked', 'Blocked'), ('deferred', 'Deferred')]:
            sprint(self.root, f'stories:\n- file: production/epics/combat/story-001.md\n  status: {value}\n')
            rows = self.build()['stories']
            self.assertEqual(rows[0]['normalized']['Stage'], want)
            self.assertEqual(rows[1]['normalized']['Stage'], 'Blocked')

    def test_snapshot_yaml_legacy_and_filtered_references_warn(self):
        story(self.root)
        story(self.root, epic='other')
        sprint(self.root, 'stories:\n- file: production/stories/old.md\n  status: done\n'
               '- file: production/epics/other/story-001.md\n  status: ready-for-dev\n')
        snap = self.build('combat')
        self.assertEqual(len(snap['stories']), 1)
        self.assertEqual(len(snap['warnings']), 2)

    def test_snapshot_yaml_malformed_unsafe_and_duplicate_input_fails(self):
        cases = ['[', '', 'stories: {}', 'stories: [null]', 'stories: [{}]',
                 'stories: []\nstories: []', 'stories: []\nx: &a [*a]',
                 'stories: []\nx: !!python/object/apply:os.system [echo unsafe]',
                 'stories: []\nx: !unknown value', 'stories: []\nx: {a: 1, a: 2}',
                 'stories: []\nx: ' + '[' * 80 + '0' + ']' * 80,
                 'stories: []\nx: ' + 'x' * 1_048_576]
        for file in ['../outside.md', '/etc/passwd', 'production/../x.md', 'production\\x.md', './production/x.md', 'production//x.md']:
            cases.append(f'stories:\n- file: {file}\n  status: done\n')
        for entry in ['file: production/epics/combat/story-001.md\n  status: unknown',
                      'file: production/epics/combat/story-001.md\n  status: done\n  status: ready',
                      'file: production/epics/combat/story-001.md\n  status: done\n- file: production/epics/combat/story-001.md\n  status: done']:
            cases.append('stories:\n- ' + entry + '\n')
        story(self.root)
        for value in cases:
            with self.subTest(value=value[:100]):
                sprint(self.root, value)
                with self.assertRaises(ValueError):
                    self.build()

    def test_snapshot_invalid_header_not_hidden_by_yaml(self):
        story(self.root, status='mystery')
        sprint(self.root, 'stories:\n- file: production/epics/combat/story-001.md\n  status: done\n')
        with self.assertRaises(ValueError):
            self.build()

    def test_snapshot_source_changes_invalidate(self):
        for operation in ['edit', 'add', 'remove', 'yaml-add', 'yaml-edit', 'yaml-remove', 'symlink', 'other-epic-edit']:
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as temp:
                self.root = Path(temp)
                path = story(self.root)
                other = story(self.root, epic='other')
                yaml = sprint(self.root, 'stories: []\n') if operation.startswith('yaml-') and operation != 'yaml-add' else None
                snap = self.build('combat')
                if operation == 'edit':
                    path.write_text(path.read_text() + 'more\n')
                elif operation == 'add':
                    story(self.root, name='story-002.md')
                elif operation == 'remove':
                    path.unlink()
                elif operation == 'yaml-add':
                    sprint(self.root, 'stories: []\n')
                elif operation == 'yaml-edit':
                    yaml.write_text('stories: []\nupdated: 2026-09-22\n')
                elif operation == 'yaml-remove':
                    yaml.unlink()
                elif operation == 'other-epic-edit':
                    other.write_text(other.read_text() + 'changed\n')
                else:
                    copy = self.root / 'copy.md'
                    copy.write_bytes(path.read_bytes())
                    path.unlink()
                    path.symlink_to(copy)
                with self.assertRaises(ValueError):
                    self.validate(snap)

    def test_snapshot_tampering_is_not_validated(self):
        story(self.root)
        snap = self.build()
        snap['stories'][0]['normalized']['Stage'] = 'Done'
        with self.assertRaises(ValueError):
            self.validate(snap)

    def test_snapshot_symlink_components_and_sources_rejected(self):
        for component in ['story', 'epic', 'epics', 'production', 'yaml']:
            with self.subTest(component=component), tempfile.TemporaryDirectory() as temp:
                self.root = Path(temp)
                path = story(self.root)
                selected = {'story': path, 'epic': path.parent, 'epics': path.parent.parent,
                            'production': path.parent.parent.parent,
                            'yaml': sprint(self.root, 'stories: []\n')}[component]
                moved = self.root / 'moved'
                selected.rename(moved)
                selected.symlink_to(moved, target_is_directory=moved.is_dir())
                with self.assertRaises(ValueError):
                    self.build()

    def test_snapshot_unreadable_enumeration_fails_instead_of_omitting_stories(self):
        path = story(self.root)
        snapshot = self.build()
        original_iterdir, original_scandir = Path.iterdir, os.scandir
        for denied in [path.parent.resolve(), path.parent.parent.resolve()]:
            with self.subTest(directory=denied.name):
                def checked_iterdir(directory):
                    if directory == denied:
                        raise PermissionError('fixture enumeration denied')
                    return original_iterdir(directory)

                def checked_scandir(directory):
                    if Path(directory) == denied:
                        raise PermissionError('fixture enumeration denied')
                    return original_scandir(directory)

                # Cover the filesystem enumeration boundary on Python versions
                # where pathlib uses either listdir or scandir internally.
                with patch.object(Path, 'iterdir', checked_iterdir), patch('os.scandir', checked_scandir):
                    with self.assertRaisesRegex(ValueError, 'UNREADABLE_BOARD_INVENTORY'):
                        self.build()
                    with self.assertRaisesRegex(ValueError, 'UNREADABLE_BOARD_INVENTORY'):
                        self.validate(snapshot)
        self.assertEqual(self.build(), snapshot)

    @unittest.skipUnless(os.name == 'posix' and os.geteuid() != 0,
                         'Real chmod denial needs an unprivileged POSIX process; injected coverage always runs')
    def test_snapshot_unreadable_real_directories_fail_instead_of_omitting_stories(self):
        path = story(self.root)
        snapshot = self.build()
        for denied in [path.parent.resolve(), path.parent.parent.resolve()]:
            with self.subTest(directory=denied.name):
                original_mode = denied.stat().st_mode
                try:
                    denied.chmod(0)
                    # Establish real denial; this must not count as a passing
                    # permission test when the host still allows enumeration.
                    with self.assertRaises(PermissionError):
                        list(denied.iterdir())
                    with self.assertRaisesRegex(ValueError, 'UNREADABLE_BOARD_INVENTORY'):
                        self.build()
                    with self.assertRaisesRegex(ValueError, 'UNREADABLE_BOARD_INVENTORY'):
                        self.validate(snapshot)
                finally:
                    denied.chmod(original_mode)
        self.assertEqual(self.build(), snapshot)

    def test_snapshot_enumeration_keeps_exact_canonical_filename_filter(self):
        path = story(self.root)
        for filename in ['notes.md', 'story.md', 'story-002.txt', 'story-003.MD']:
            (path.parent / filename).write_text('not a story header')
        nested = path.parent / 'nested'
        nested.mkdir()
        (nested / 'story-004.md').write_text('not a canonical direct-child story')
        self.assertEqual(self.build()['inventory'], ['production/epics/combat/story-001.md'])

    def test_snapshot_non_directory_ancestor_is_not_empty_project(self):
        (self.root / 'production').write_text('not a directory')
        with self.assertRaises(ValueError):
            self.build()

    def test_snapshot_bounds_and_encoding_fail_safely(self):
        path = story(self.root)
        for value in [b'\xff', b'x' * 1_048_577]:
            path.write_bytes(value)
            with self.assertRaises(ValueError):
                self.build()

    def test_snapshot_cli_missing_yaml_dependency_actionable(self):
        story(self.root)
        sprint(self.root, 'stories: []\n')
        result = subprocess.run([sys.executable, '-S', str(CLI), '--root', str(self.root),
                                 'board-sync', 'snapshot'], text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('requirements-board.txt', json.loads(result.stdout)['error'])
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
