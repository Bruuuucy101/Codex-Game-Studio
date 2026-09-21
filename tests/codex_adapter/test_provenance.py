"""Temporary-filesystem integration tests for reviewed source provenance."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import test_cli


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / '.codex').mkdir()
        self.name = '.claude/example.md'
        self.source = self.root / self.name
        self.source.parent.mkdir()
        self.source.write_bytes(b'original\n')
        self.original = hashlib.sha256(b'original\n').hexdigest()
        self.patched = hashlib.sha256(b'reviewed\n').hexdigest()
        self.commit = 'a' * 40
        self.lock = {'commit': self.commit, 'files': {self.name: self.original}}
        self.ledger = {'schema_version': 1, 'baseline_commit': self.commit, 'patches': []}
        self.record = {'path': self.name, 'original_sha256': self.original,
                       'patched_sha256': self.patched,
                       'issue_urls': ['https://github.com/example/studio/issues/1'],
                       'rationale': 'Correct an inherited workflow defect.'}
        self.save()

    def save(self):
        (self.root / '.codex/upstream-lock.json').write_text(json.dumps(self.lock))
        (self.root / '.codex/upstream-patches.json').write_text(json.dumps(self.ledger))

    def verify(self, pristine=False):
        try:
            from ccgs.provenance import verify_upstream
        except ImportError:
            self.fail('Missing reviewed-source provenance verifier')
        return verify_upstream(self.root, pristine=pristine)

    def test_upstream_pristine_passes_with_empty_or_absent_ledger(self):
        self.assertEqual(self.verify(), [])
        self.assertEqual(self.verify(pristine=True), [])
        (self.root / '.codex/upstream-patches.json').unlink()
        self.assertEqual(self.verify(), [])

    def test_upstream_exact_reviewed_patch_passes_but_pristine_fails(self):
        self.source.write_bytes(b'reviewed\n')
        self.ledger['patches'] = [self.record]
        self.save()
        self.assertEqual(self.verify(), [])
        self.assertIn('UPSTREAM_CHANGED ' + self.name, self.verify(pristine=True))

    def test_upstream_unrecorded_and_stale_patch_hashes_fail(self):
        self.source.write_bytes(b'reviewed\n')
        self.assertIn('UPSTREAM_CHANGED ' + self.name, self.verify())
        self.ledger['patches'] = [self.record]
        self.record['patched_sha256'] = 'f' * 64
        self.save()
        self.assertIn('UPSTREAM_CHANGED ' + self.name, self.verify())

    def test_upstream_wrong_baseline_associations_fail_even_if_pristine(self):
        self.ledger['patches'] = [self.record]
        self.record['original_sha256'] = 'f' * 64
        self.save()
        self.assertTrue(self.verify())
        self.record['original_sha256'] = self.original
        self.ledger['baseline_commit'] = 'b' * 40
        self.save()
        self.assertTrue(self.verify())

    def test_upstream_duplicate_unknown_and_unsafe_paths_fail(self):
        self.ledger['patches'] = [self.record, copy.deepcopy(self.record)]
        self.save()
        self.assertTrue(self.verify())
        for name in ['unknown.md', '../outside', '/absolute', './same.md',
                     '.claude/../example.md', '.claude//example.md', 'C:\\outside', '', None]:
            with self.subTest(path=name):
                self.ledger['patches'] = [dict(self.record, path=name)]
                self.save()
                self.assertTrue(self.verify())

    def test_upstream_symlink_escape_fails(self):
        outside = self.root / 'outside.md'
        outside.write_bytes(b'original\n')
        self.source.unlink()
        self.source.symlink_to(outside)
        # A baseline source alias is not a reviewed file, even within root.
        self.assertTrue(self.verify())

    def test_upstream_missing_source_fails_even_with_reviewed_record(self):
        self.ledger['patches'] = [self.record]
        self.save()
        self.source.unlink()
        self.assertIn('UPSTREAM_MISSING ' + self.name, self.verify())

    def test_upstream_malformed_records_fail_even_if_pristine(self):
        invalid = {'original_sha256': [None, 12, 'z' * 64, 'a' * 63],
                   'patched_sha256': [None, 12, 'z' * 64, 'a' * 65],
                   'issue_urls': [None, [], '', [''], [1], ['   ']],
                   'rationale': [None, '', '  ', 42]}
        for key, values in invalid.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    self.ledger['patches'] = [dict(self.record, **{key: value})]
                    self.save()
                    self.assertTrue(self.verify())
        for key in self.record:
            with self.subTest(missing=key):
                record = dict(self.record)
                del record[key]
                self.ledger['patches'] = [record]
                self.save()
                self.assertTrue(self.verify())

    def test_upstream_malformed_ledger_fails_without_exception(self):
        for ledger in [None, [], {}, {'schema_version': True},
                       dict(self.ledger, schema_version=2),
                       dict(self.ledger, patches={}),
                       dict(self.ledger, patches=[None]),
                       dict(self.ledger, baseline_commit=42)]:
            with self.subTest(ledger=ledger):
                self.ledger = ledger
                self.save()
                self.assertTrue(self.verify())
        (self.root / '.codex/upstream-patches.json').write_text('{')
        self.assertTrue(self.verify())

    def test_upstream_malformed_lock_fails_without_exception(self):
        for lock in [None, [], {}, {'files': []},
                     {'files': {'../outside': self.original}},
                     {'files': {self.name: None}}]:
            with self.subTest(lock=lock):
                self.lock = lock
                self.save()
                self.assertTrue(self.verify())
        (self.root / '.codex/upstream-lock.json').unlink()
        self.assertTrue(self.verify())


class ProvenanceCliTests(unittest.TestCase):
    setUp = test_cli.CliTests.setUp
    run_cli = test_cli.CliTests.run_cli

    def test_cli_reviewed_and_pristine_checks_report_different_scopes(self):
        self.run_cli('generate')
        name = '.claude/agents/qa-tester.md'
        source = self.root / name
        original = hashlib.sha256(source.read_bytes()).hexdigest()
        source.write_text(source.read_text() + '\nreviewed correction\n')
        commit = 'a' * 40
        (self.root / '.codex/upstream-lock.json').write_text(json.dumps(
            {'commit': commit, 'files': {name: original}}))
        (self.root / '.codex/upstream-patches.json').write_text(json.dumps({
            'schema_version': 1, 'baseline_commit': commit,
            'patches': [{'path': name, 'original_sha256': original,
                         'patched_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                         'issue_urls': ['https://github.com/example/studio/issues/1'],
                         'rationale': 'Reviewed correction.'}]}))
        self.run_cli('generate')
        self.assertEqual(self.run_cli('check', '--strict-upstream')[0], 0)
        self.assertNotEqual(self.run_cli('check', '--pristine-upstream')[0], 0)
        _, out = self.run_cli('doctor')
        result = json.loads(out)
        self.assertEqual(result['upstream_drift'], [])
        self.assertIn('UPSTREAM_CHANGED ' + name, result['upstream_pristine_drift'])
        self.assertEqual(result['runtime']['hook_trust'], 'not verified')


if __name__ == '__main__':
    unittest.main()
