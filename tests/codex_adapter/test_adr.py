"""Behavioral tests for bounded, current ADR context."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))


class AdrTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'docs/architecture/adr.md'
        self.path.parent.mkdir(parents=True)
        self.name = 'docs/architecture/adr.md'

    def read(self, text=None, **kwargs):
        if text is not None:
            self.path.write_text(text, encoding='utf-8')
        try:
            from ccgs.adr import read_context
        except ImportError:
            self.fail('Missing bounded ADR context reader')
        return read_context(self.root, self.name, **kwargs)

    def test_huge_single_line_pages_reconstruct_unicode_without_loss(self):
        decision = '## 2. Decision\n' + '界🙂abc' * 17000 + '\n### 2.1 Nested\nconstraint\n'
        text = '# ADR\n## 1. Status\nAccepted\n' + decision + '## Consequences\nother\n'
        page = self.read(text, sections=['Decision'], limit=791)
        chunks = []
        while True:
            self.assertLessEqual(len(page['content']), 791)
            chunks.append(page['content'])
            if not page['more']:
                break
            page = self.read(sections=['Decision'], limit=791, offset=page['next_offset'],
                             expected_sha256=page['sha256'])
        self.assertEqual(''.join(chunks), decision)
        self.assertEqual(page['sha256'], hashlib.sha256(text.encode()).hexdigest())
        self.assertIsNone(page['next_offset'])

    def test_fenced_examples_do_not_change_headings_or_status(self):
        page = self.read('# ADR\n> **Status**: **Accepted**\n## Decision\n'
                         '````md\n## Fake\nStatus: Proposed\n```\n````\n'
                         '~~~\nStatus: Rejected\n## Fake two\n~~~\nreal\n')
        self.assertEqual(page['status'], 'Accepted')
        self.assertNotIn('Fake', [s['title'] for s in page['sections']])
        self.assertEqual(len(page['status_declarations']), 1)

    def test_missing_conflicting_and_unknown_status_never_default_to_accepted(self):
        for text, state in [('# ADR\n## Decision\nx', 'missing'),
                            ('Status: Accepted\n## Status\nProposed\n', 'ambiguous'),
                            ('Status: Something else\n', 'unrecognized'),
                            ('## Status\n', 'unrecognized')]:
            with self.subTest(state=state):
                page = self.read(text)
                self.assertIsNone(page['status'])
                self.assertEqual(page['status_state'], state)

    def test_numbered_status_and_formatted_inline_variants(self):
        for text in ('## 1. Status\n**Accepted**\n', '**Status:** Accepted\n',
                     '## 1) Status\nAccepted\n', 'Status: Accepted\nStatus: Accepted\n'):
            self.assertEqual(self.read(text)['status'], 'Accepted')

    def test_nonaccepted_source_status_is_preserved(self):
        for value in ('Proposed', 'Deprecated', 'Superseded by ADR-0042'):
            page = self.read('## Status\n' + value)
            self.assertEqual(page['status'], value)
            self.assertEqual(page['status_state'], 'known')

    def test_metadata_does_not_return_unbounded_status_prose(self):
        page = self.read('Status: Accepted on ' + 'x' * 90000, metadata_only=True)
        self.assertLess(len(json.dumps(page)), 2000)
        self.assertIsNone(page['status'])

    def test_blockquoted_fenced_examples_are_ignored(self):
        page = self.read('Status: Accepted\n> ```md\n> Status: Proposed\n> ```\n')
        self.assertEqual(page['status'], 'Accepted')

    def test_literal_quote_fence_cannot_close_a_top_level_fence(self):
        page = self.read('# ADR\n```markdown\n> ```\nStatus: Accepted\n'
                         '## Fake Decision\n> ```\n```\n'
                         '## Decision\nnot yet approved\n')
        self.assertEqual(page['status_declarations'], [])
        self.assertIsNone(page['status'])
        self.assertEqual(page['status_state'], 'missing')
        self.assertEqual([s['title'] for s in page['sections']], ['ADR', 'Decision'])

    def test_requested_sections_include_all_later_amendments_and_nested_children(self):
        text = ('Status: Accepted\n## Decision\nbase\n### Nested\nchild\n'
                '## Other\nnot selected\n## Amendment 1\n### Status\nAccepted\n'
                '### Rules\nnew constraint\n## Appendix\nskip\n'
                '## 7. Amendments\nStatus: Proposed\nmore constraints\n')
        page = self.read(text, sections=['Decision', 'Missing', 'Nested'])
        self.assertEqual(page['status'], 'Accepted')
        self.assertEqual(page['missing_sections'], ['Missing'])
        self.assertIn('new constraint', page['content'])
        self.assertIn('more constraints', page['content'])
        self.assertEqual(page['content'].count('child'), 1)
        self.assertNotIn('not selected', page['content'])
        self.assertNotIn('skip', page['content'])

    def test_metadata_returns_hash_and_ranges_without_body(self):
        page = self.read('Status: Accepted\n## Decision\nbody\n', metadata_only=True)
        self.assertEqual(page['content'], '')
        self.assertEqual(page['sections'][0]['title'], 'Decision')
        self.assertEqual(page['sections'][0]['start_line'], 2)
        self.assertEqual(page['sections'][0]['end_line'], 3)
        self.assertEqual(page['source'], self.name)

    def test_changed_hash_invalidates_next_page(self):
        first = self.read('Status: Accepted\n## Decision\n' + 'x' * 100, limit=10)
        self.path.write_text('Status: Proposed\n## Decision\nchanged')
        with self.assertRaisesRegex(ValueError, 'ADR_CHANGED'):
            self.read(offset=10, expected_sha256=first['sha256'])

    def test_invalid_pagination_is_rejected(self):
        for args in ({'limit': 0}, {'limit': -1}, {'limit': 12001}, {'offset': -1},
                     {'offset': 999}, {'limit': True}, {'offset': 0.5},
                     {'expected_sha256': 'not-a-digest'}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.read('Status: Accepted\n', **args)

    def test_unsafe_missing_and_symlink_paths_are_rejected(self):
        self.read('Status: Accepted\n')
        from ccgs.adr import read_context
        for path in ('../outside.md', '/etc/passwd', 'docs//architecture/adr.md',
                     './docs/architecture/adr.md', 'docs\\adr.md'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                read_context(self.root, path)
        with self.assertRaises(OSError):
            read_context(self.root, 'missing.md')
        link = self.root / 'link.md'
        link.symlink_to(self.path)
        with self.assertRaises(ValueError):
            read_context(self.root, 'link.md')

    def test_cli_json_and_errors(self):
        from ccgs.cli import main
        self.path.write_text('Status: Accepted\n## Decision\nkeep\n')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(['--root', str(self.root), 'adr-context', self.name,
                           '--section', 'Decision', '--limit', '4'])
        self.assertEqual(result, 0)
        page = json.loads(output.getvalue())
        self.assertEqual(len(page['content']), 4)
        self.assertTrue(page['more'])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(['--root', str(self.root), 'adr-context', '../bad'])
        self.assertEqual(result, 1)
        self.assertEqual(json.loads(output.getvalue())['status'], 'FAIL')

    def test_story_workflows_require_per_adr_current_evidence(self):
        for name in ('create-stories', 'dev-story', 'story-readiness'):
            with self.subTest(workflow=name):
                source = (ROOT / f'.claude/skills/{name}/SKILL.md').read_text()
                self.assertIn('adr-context', source)
                self.assertIn('ADR Source SHA256', source)
                self.assertIn('--metadata-only', source)
                self.assertIn('--expected-sha256', source)
                self.assertIn('No ADR applies', source)
        dev = (ROOT / '.claude/skills/dev-story/SKILL.md').read_text()
        child_brief = dev.split('## Phase 4: Implement')[1].split('## Phase 5:')[0]
        self.assertIn('hash-validated embedded', child_brief)
        self.assertIn('Do not reread the whole ADR', child_brief)
        readiness = (ROOT / '.claude/skills/story-readiness/SKILL.md').read_text()
        self.assertIn('Missing provenance or a hash mismatch', readiness)
        self.assertIn('never rewrite', readiness)


if __name__ == '__main__':
    unittest.main()
