import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for directory in ('.claude', 'docs/codex-adapter'):
            shutil.copytree(ROOT / directory, self.root / directory, ignore=shutil.ignore_patterns('capabilities.md'))
        self.addCleanup(self.tmp.cleanup)

    def run_cli(self, *args):
        try:
            from ccgs.cli import main
        except ImportError:
            self.fail('Missing diagnostics and status CLI')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(['--root', str(self.root), *args])
        return result, output.getvalue()

    def test_status_reports_unconfigured_and_then_real_state(self):
        rc, out = self.run_cli('status')
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)['stage'], 'not configured')
        path = self.root / 'production/stage.txt'
        path.parent.mkdir()
        path.write_text('production\n')
        rc, out = self.run_cli('status')
        self.assertEqual(json.loads(out)['stage'], 'production')

    def test_check_fails_before_generate_and_passes_after(self):
        self.assertNotEqual(self.run_cli('check')[0], 0)
        self.assertEqual(self.run_cli('generate')[0], 0)
        self.assertEqual(self.run_cli('check')[0], 0)

    def test_role_retrieval_rejects_path_traversal(self):
        rc, out = self.run_cli('role', '../outside')
        self.assertNotEqual(rc, 0)
        self.assertIn('Unknown role', out)

    def test_doctor_does_not_claim_hooks_are_trusted(self):
        self.run_cli('generate')
        rc, out = self.run_cli('doctor')
        self.assertEqual(json.loads(out)['runtime']['hook_trust'], 'not verified')

    def test_strict_baseline_check_detects_original_file_change(self):
        from ccgs.catalog import sha256
        self.run_cli('generate')
        lock = self.root / '.codex/upstream-lock.json'
        source = self.root / '.claude/agents/qa-tester.md'
        lock.write_text(json.dumps({'files': {'.claude/agents/qa-tester.md': sha256(source.read_bytes())}}))
        self.assertEqual(self.run_cli('check', '--strict-upstream')[0], 0)
        source.write_text(source.read_text() + '\nunaudited change')
        self.run_cli('generate')
        self.assertNotEqual(self.run_cli('check', '--strict-upstream')[0], 0)


if __name__ == '__main__':
    unittest.main()
