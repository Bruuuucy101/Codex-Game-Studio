"""Converter behavior: pure parsing plus real CLI and create-only publication."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'examples/tooling/level-exporter/export_levels.py'
FIXTURE = ROOT / 'examples/tooling/level-exporter/fixtures/levels.csv'
CSV = 'id,x,y,type\nspawn-b,2.5,-3,enemy\nspawn-a,0,1,player\n'
EXPECTED = b'{"schema_version":1,"levels":[{"id":"spawn-a","x":0.0,"y":1.0,"type":"player"},{"id":"spawn-b","x":2.5,"y":-3.0,"type":"enemy"}]}\n'


class ExporterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.input = self.root / 'input.csv'
        self.input.write_text(CSV)
        self.output = self.root / 'out.json'

    def module(self):
        self.assertTrue(SCRIPT.is_file(), 'Missing executable level exporter')
        spec = importlib.util.spec_from_file_location('level_exporter', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run_cli(self, input=None, output=None):
        self.assertTrue(SCRIPT.is_file(), 'Missing executable level exporter')
        return subprocess.run([sys.executable, str(SCRIPT), str(input or self.input), str(output or self.output)],
                              text=True, capture_output=True)

    def test_real_fixture_deterministic_bytes_types_and_unchanged_input(self):
        self.assertTrue(FIXTURE.is_file(), 'Missing representative level CSV fixture')
        before = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        for name in ('first.json', 'second.json'):
            output = self.root / name
            result = self.run_cli(FIXTURE, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), EXPECTED)
            parsed = json.loads(output.read_text())
            self.assertEqual(len(parsed['levels']), 2)
            self.assertIs(type(parsed['levels'][0]['x']), float)
        self.assertEqual(before, hashlib.sha256(FIXTURE.read_bytes()).hexdigest())

    def test_parser_numeric_and_identity_contract(self):
        module = self.module()
        self.assertEqual(module.convert_csv(CSV), EXPECTED)
        for value in ('NaN', 'Infinity', '1e9999', 'bad'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'row 2'):
                module.convert_csv('id,x,y,type\na,' + value + ',1,enemy\n')

    def test_invalid_batches_produce_no_partial_output(self):
        cases = {
            'header': 'id,y,x,type\na,1,2,enemy\n',
            'missing column': 'id,x,y,type\na,1,2\n',
            'extra column': 'id,x,y,type\na,1,2,enemy,extra\n',
            'empty id': 'id,x,y,type\n,1,2,enemy\n',
            'empty type': 'id,x,y,type\na,1,2,\n',
            'duplicate': 'id,x,y,type\na,1,2,enemy\na,3,4,enemy\n',
            'partial valid batch': 'id,x,y,type\na,1,2,enemy\nb,wrong,4,enemy\n',
            'malformed quotes': 'id,x,y,type\na,1,2,"enemy\n',
            'empty batch': 'id,x,y,type\n',
        }
        for name, value in cases.items():
            with self.subTest(name=name):
                self.input.write_text(value)
                before = self.input.read_bytes()
                result = self.run_cli()
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stderr.strip())
                self.assertFalse(self.output.exists())
                self.assertEqual(self.input.read_bytes(), before)
                self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['input.csv'])

    def test_missing_input_and_bad_encoding_fail_without_output(self):
        result = self.run_cli(self.root / 'missing.csv')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing.csv', result.stderr)
        self.input.write_bytes(b'\xff')
        self.assertNotEqual(self.run_cli().returncode, 0)
        self.assertFalse(self.output.exists())

    def test_existing_output_same_input_and_symlink_are_preserved(self):
        self.output.write_bytes(b'keep existing output')
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exists', result.stderr)
        self.assertEqual(self.output.read_bytes(), b'keep existing output')
        before = self.input.read_bytes()
        self.assertNotEqual(self.run_cli(output=self.input).returncode, 0)
        self.assertEqual(self.input.read_bytes(), before)
        self.output.unlink()
        self.output.symlink_to(self.root / 'missing-destination')
        self.assertNotEqual(self.run_cli().returncode, 0)
        self.assertTrue(self.output.is_symlink())
        self.assertFalse((self.root / 'missing-destination').exists())

    def test_racing_writer_wins_without_replacement_or_temporary_leaks(self):
        module = self.module()
        def competing_publish(temp, target):
            target.write_bytes(b'other writer owns output')
            module.publish_create_only(temp, target)
        with self.assertRaises(FileExistsError):
            module.export_file(self.input, self.output, publish=competing_publish)
        self.assertEqual(self.output.read_bytes(), b'other writer owns output')
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['input.csv', 'out.json'])

    def test_publication_failure_cleans_temporary_output(self):
        module = self.module()
        def failed_publish(temp, target):
            raise OSError('publication unavailable')
        with self.assertRaisesRegex(OSError, 'publication unavailable'):
            module.export_file(self.input, self.output, publish=failed_publish)
        self.assertFalse(self.output.exists())
        self.assertEqual([p.name for p in self.root.iterdir()], ['input.csv'])
