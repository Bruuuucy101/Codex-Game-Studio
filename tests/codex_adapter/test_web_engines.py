"""Source-contract integration checks, not executed agent or browser certification."""
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from ccgs import catalog, generate

NEW_ROLES = {'phaser-specialist', 'threejs-specialist'}


class WebEngineTests(unittest.TestCase):
    def test_web_inventory_preserves_original_identities_and_exact_additions(self):
        # Dropping an old identity must fail even if a new role keeps counts equal.
        baseline = json.loads((ROOT / '.codex/upstream-lock.json').read_text())['files']
        rows = catalog.inventory(ROOT)
        original_roles = {Path(p).stem for p in baseline if p.startswith('.claude/agents/') and p.endswith('.md')}
        original_skills = {Path(p).parent.name for p in baseline if p.startswith('.claude/skills/') and p.endswith('/SKILL.md')}
        actual_roles = {r['name'] for r in rows['agents']}
        self.assertEqual(len(original_roles), 49)
        self.assertEqual(len(original_skills), 73)
        self.assertEqual(actual_roles, original_roles | NEW_ROLES | {'game-pipeline-developer', 'libgdx-specialist', 'libgdx-scene2d-specialist', 'libgdx-graphics-specialist', 'libgdx-ashley-specialist', 'libgdx-core-specialist'})
        self.assertEqual({r['name'] for r in rows['skills']}, original_skills | {'setup-tool', 'board-sync', 'npc-voice'})
        profiles = generate.render(ROOT)
        self.assertEqual({Path(p).stem.removeprefix('ccgs-') for p in profiles if p.startswith('.codex/agents/')}, actual_roles)

    def test_web_roles_generate_complete_bodies_and_restricted_metadata(self):
        rows = {r['name']: r for r in catalog.inventory(ROOT)['agents']}
        self.assertTrue(NEW_ROLES <= rows.keys(), 'Both canonical web specialists are required')
        files = generate.render(ROOT)
        for name in sorted(NEW_ROLES):
            with self.subTest(role=name):
                row = rows[name]
                meta, body = catalog.frontmatter((ROOT / row['source']).read_text())
                generated = files[f'.codex/agents/ccgs-{name}.toml']
                encoded = next(line.partition(' = ')[2] for line in generated.splitlines() if line.startswith('developer_instructions = '))
                instructions = json.loads(encoded)
                self.assertIn(body, instructions)
                self.assertIn(row['sha256'], instructions)
                self.assertNotIn(f'original CCGS {name}', instructions)
                self.assertEqual(int(meta['maxTurns']), 20)
                self.assertNotIn('WebSearch', meta['tools'])
                self.assertNotIn('WebFetch', meta['tools'])

    def test_web_setup_routes_resolve_to_real_roles_and_keep_existing_branches(self):
        text = (ROOT / '.claude/skills/setup-engine/SKILL.md').read_text()
        roles = {r['name'] for r in catalog.inventory(ROOT)['agents']}
        for engine, specialist, ui in [('phaser', 'phaser-specialist', 'phaser-specialist'), ('threejs', 'threejs-specialist', 'ui-programmer')]:
            # These are the actual copyable preferences blocks consumed by setup.
            marker = f'### {engine} routing'
            self.assertIn(marker, text)
            block = text.split(marker, 1)[1].split('```markdown', 1)[1].split('```', 1)[0]
            fields = dict(re.findall(r'^- \*\*([^*]+)\*\*: ([a-z][a-z-]+)$', block, re.M))
            self.assertEqual(fields['Primary'], specialist)
            self.assertEqual(fields['Language/Code Specialist'], specialist)
            self.assertEqual(fields['Shader Specialist'], 'technical-artist')
            self.assertEqual(fields['UI Specialist'], ui)
            for field in ('Primary', 'Language/Code Specialist', 'Shader Specialist', 'UI Specialist'):
                self.assertIn(fields[field], roles)
            for route in re.findall(r'^\|[^|]+\| ([a-z][a-z-]+) \|$', block, re.M):
                self.assertIn(route, roles)
        for retained in ('### A1.', '### A2.', '### A3.', 'unity-specialist', 'unreal-specialist', 'godot-gdscript-specialist', 'godot-csharp-specialist'):
            self.assertIn(retained, text)

    def test_web_role_references_and_behavior_specs_resolve(self):
        behavior = (ROOT / 'CCGS Skill Testing Framework/catalog.yaml').read_text()
        for engine in ('phaser', 'threejs'):
            role = ROOT / f'.claude/agents/{engine}-specialist.md'
            self.assertTrue(role.is_file(), f'Missing {role.name}')
            roles = {row['name'] for row in catalog.inventory(ROOT)['agents']}
            referenced_roles = set(re.findall(r'`([a-z]+(?:-[a-z]+)+)`', role.read_text()))
            self.assertTrue(referenced_roles <= roles, referenced_roles - roles)
            for path in re.findall(r'`(docs/engine-reference/[^`]+\.md)`', role.read_text()):
                self.assertTrue((ROOT / path).is_file(), path)
            spec = f'CCGS Skill Testing Framework/agents/engine/{engine}/{engine}-specialist.md'
            self.assertIn('spec: ' + spec, behavior)
            self.assertTrue((ROOT / spec).is_file())
        pins = {engine: ROOT / f'docs/engine-reference/{engine}/VERSION.md' for engine in ('phaser', 'threejs')}
        for path in pins.values():
            self.assertTrue(path.is_file(), str(path))
        self.assertIn('3.90.0', pins['phaser'].read_text())
        self.assertIn('0.186.0', pins['threejs'].read_text())
        self.assertIn('r186', pins['threejs'].read_text())


if __name__ == '__main__':
    unittest.main()
