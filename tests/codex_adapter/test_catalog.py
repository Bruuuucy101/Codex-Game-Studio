import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for directory in ('.claude', 'docs/codex-adapter'):
            shutil.copytree(ROOT / directory, self.root / directory, ignore=shutil.ignore_patterns('capabilities.md'))
        self.addCleanup(self.tmp.cleanup)

    def api(self):
        try:
            from ccgs import catalog, generate
        except ImportError:
            self.fail('Missing the full-source adapter generator and parity checker')
        return catalog, generate

    def test_all_workflows_load_the_actual_full_source(self):
        catalog, generate = self.api()
        rows = catalog.inventory(self.root)
        files = generate.render(self.root)
        baseline = json.loads((ROOT / '.codex/upstream-lock.json').read_text())['files']
        original = {Path(p).parent.name for p in baseline if p.startswith('.claude/skills/') and p.endswith('/SKILL.md')}
        actual = {row['name'] for row in rows['skills']}
        self.assertEqual(len(original), 73)
        self.assertTrue(original <= actual)
        self.assertEqual(actual - original, {'setup-tool'})
        for row in rows['skills']:
            target = f".agents/skills/ccgs-{row['name']}/SKILL.md"
            self.assertIn(target, files)
            self.assertIn(row['source'], files[target])
            self.assertIn(row['sha256'], files[target])
        # A routing entry must never silently point to a different workflow.
        dev = files['.agents/skills/ccgs-dev-story/SKILL.md']
        self.assertIn('.claude/skills/dev-story/SKILL.md', dev)

    def test_every_role_retains_its_entire_instructions(self):
        catalog, generate = self.api()
        files = generate.render(self.root)
        roles = catalog.inventory(self.root)['agents']
        baseline = json.loads((ROOT / '.codex/upstream-lock.json').read_text())['files']
        original = {Path(p).stem for p in baseline if p.startswith('.claude/agents/') and p.endswith('.md')}
        actual = {role['name'] for role in roles}
        self.assertTrue(original <= actual)
        self.assertEqual(actual - original, {'phaser-specialist', 'threejs-specialist', 'game-pipeline-developer'})
        for role in roles:
            text = files[f".codex/agents/ccgs-{role['name']}.toml"]
            line = next(x for x in text.splitlines() if x.startswith('developer_instructions = '))
            instructions = json.loads(line.partition(' = ')[2])
            _, body = catalog.frontmatter((self.root / role['source']).read_text())
            self.assertIn(body, instructions)
            self.assertIn(f".claude/agent-memory/{role['name']}/MEMORY.md", instructions)
            self.assertNotIn('model = "opus"', text)

    def test_metadata_roles_are_explicitly_dispatched_with_question_handoff(self):
        catalog, generate = self.api()
        files = generate.render(self.root)
        for row in catalog.inventory(self.root)['skills']:
            if row['metadata'].get('agent'):
                role = row['metadata']['agent']
                entry = files[f".agents/skills/ccgs-{row['name']}/SKILL.md"]
                self.assertIn(f'Dispatch a real `ccgs-{role}` child', entry)
                self.assertIn(f'.claude/agents/{role}.md', entry)
                self.assertIn('coordinator retains user decisions', entry)
                self.assertIn('Do not copy the full conversation', entry)
                self.assertNotIn('context: fork', entry)
        self.assertNotIn('Dispatch a real', files['.agents/skills/ccgs-dev-story/SKILL.md'])

    def test_unknown_metadata_role_cannot_silently_be_simulated(self):
        _, generate = self.api()
        source = self.root / '.claude/skills/create-stories/SKILL.md'
        source.write_text(source.read_text().replace('agent: lead-programmer', 'agent: nonexistent-role'))
        with self.assertRaisesRegex(ValueError, 'Unknown workflow agent'):
            generate.render(self.root)

    def test_missing_runtime_contract_cannot_be_regenerated_as_success(self):
        _, generate = self.api()
        generate.write(self.root)
        (self.root / generate.RUNTIME).unlink()
        with self.assertRaises(ValueError):
            generate.write(self.root)

    def test_owned_generated_symlink_never_overwrites_user_file(self):
        _, generate = self.api()
        generate.write(self.root)
        notes = self.root / 'private-notes.md'
        notes.write_text('keep these notes')
        target = self.root / '.agents/skills/ccgs-start/SKILL.md'
        target.unlink()
        target.symlink_to(notes)
        with self.assertRaises(ValueError):
            generate.write(self.root)
        self.assertEqual(notes.read_text(), 'keep these notes')

    def test_generated_parent_symlink_cannot_escape_project(self):
        _, generate = self.api()
        generate.write(self.root)
        with tempfile.TemporaryDirectory() as elsewhere:
            moved = Path(elsewhere) / 'skills'
            folder = self.root / '.agents/skills'
            shutil.move(str(folder), moved)
            folder.symlink_to(moved, target_is_directory=True)
            target = moved / 'ccgs-start/SKILL.md'
            target.write_text('outside notes')
            with self.assertRaises(ValueError):
                generate.write(self.root)
            self.assertEqual(target.read_text(), 'outside notes')

    def test_manifest_symlink_cannot_overwrite_other_file(self):
        _, generate = self.api()
        generate.write(self.root)
        manifest = self.root / generate.MANIFEST
        notes = self.root / 'other-manifest.json'
        original = manifest.read_text()
        notes.write_text(original)
        manifest.unlink()
        manifest.symlink_to(notes)
        with self.assertRaises(ValueError):
            generate.write(self.root)
        self.assertEqual(notes.read_text(), original)

    def test_deleted_workflow_and_generated_tampering_are_detected(self):
        catalog, generate = self.api()
        generate.write(self.root)
        self.assertEqual(generate.check(self.root), [])
        path = self.root / '.agents/skills/ccgs-dev-story/SKILL.md'
        path.write_text('pretend implementation is just planning')
        self.assertTrue(any(str(path.relative_to(self.root)) in e for e in generate.check(self.root)))
        generate.write(self.root)
        (self.root / '.claude/skills/dev-story/SKILL.md').unlink()
        self.assertTrue(any('dev-story' in e for e in generate.check(self.root)))

    def test_generator_refuses_unowned_collisions(self):
        _, generate = self.api()
        target = self.root / '.agents/skills/ccgs-start/SKILL.md'
        target.parent.mkdir(parents=True)
        target.write_text('my existing skill')
        with self.assertRaises(ValueError):
            generate.write(self.root)
        self.assertEqual(target.read_text(), 'my existing skill')

    def test_changed_source_is_reflected_and_stale_output_detected(self):
        _, generate = self.api()
        generate.write(self.root)
        source = self.root / '.claude/agents/qa-tester.md'
        source.write_text(source.read_text() + '\nA new upstream acceptance requirement.\n')
        self.assertTrue(any('qa-tester' in e for e in generate.check(self.root)))
        generate.write(self.root)
        self.assertEqual(generate.check(self.root), [])

    def test_rule_matching_does_not_confuse_sibling_directories(self):
        catalog, _ = self.api()
        selected = catalog.rules_for(self.root, ['src/gameplay/combat/player.gd'])
        self.assertIn('gameplay-code', [r['name'] for r in selected])
        other = catalog.rules_for(self.root, ['src/gameplay_backup/player.gd'])
        self.assertNotIn('gameplay-code', [r['name'] for r in other])

    def test_optional_tier_mapping_is_explicit_and_validated(self):
        _, generate = self.api()
        config = self.root / '.codex/ccgs-models.json'
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({'opus': {'model': 'example-available-model', 'model_reasoning_effort': 'high'}}))
        files = generate.render(self.root)
        self.assertIn('model = "example-available-model"', files['.codex/agents/ccgs-creative-director.toml'])
        config.write_text(json.dumps({'opus': {'model': '', 'model_reasoning_effort': 'impossible'}}))
        with self.assertRaises(ValueError):
            generate.render(self.root)

    def test_nested_templates_are_included_in_inventory(self):
        catalog, _ = self.api()
        sources = [row['source'] for row in catalog.inventory(self.root)['templates']]
        nested = self.root / '.claude/docs/templates/custom/deep-template.md'
        nested.parent.mkdir(parents=True)
        nested.write_text('# A nested template')
        self.assertIn('.claude/docs/templates/custom/deep-template.md',
                      [row['source'] for row in catalog.inventory(self.root)['templates']])


if __name__ == '__main__':
    unittest.main()
