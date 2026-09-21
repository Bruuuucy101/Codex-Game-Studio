"""Source-contract regressions for inherited workflow instructions.

These integration checks validate explicit phase ordering and branch contracts;
they do not claim to prove that an LLM follows the instructions at runtime.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


def source(name):
    return (ROOT / '.claude' / 'skills' / name / 'SKILL.md').read_text(encoding='utf-8')


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


class UpstreamWorkflowTests(unittest.TestCase):
    def test_hotfix_implementation_requires_prior_scope_approval(self):
        text = source('hotfix')
        headings = re.findall(r'^## Phase [^\n]+', text, re.M)
        for heading in ('## Phase 4: Investigate and Propose',
                        '## Phase 4a: Authorize Implementation',
                        '## Phase 4b: Implement and Test'):
            self.assertIn(heading, headings)
        self.assertLess(headings.index('## Phase 4: Investigate and Propose'),
                        headings.index('## Phase 4a: Authorize Implementation'))
        self.assertLess(headings.index('## Phase 4a: Authorize Implementation'),
                        headings.index('## Phase 4b: Implement and Test'))
        investigation = section(text, '## Phase 4:', '## Phase 4a:')
        self.assertIn('read-only', investigation)
        self.assertIn('Do not edit code or spawn implementation agents', investigation)
        approval = section(text, '## Phase 4a:', '## Phase 4b:')
        self.assertIn('AskUserQuestion', approval)
        for outcome in ('[A] Approve', '[B] Revise', '[C] Stop'):
            self.assertIn(outcome, approval)
        self.assertIn('files', investigation)
        self.assertIn('rollback', investigation)
        self.assertIn('before any code edits or implementation agent spawns', approval)
        self.assertIn('cancels', approval)
        self.assertIn('stop dependent work', approval)
        self.assertIn('Prior explicit user authorization', approval)
        self.assertIn('does not replace', approval)

    def test_hotfix_release_retains_real_signoffs_and_qa_reentry(self):
        text = source('hotfix')
        approvals = section(text, '## Phase 5:', '## Phase 5b:')
        for role in ('lead-programmer', 'qa-tester', 'producer'):
            self.assertIn('subagent_type: ' + role, approvals)
        self.assertIn('All three must return APPROVE', approvals)
        self.assertIn('do not deploy or merge', approvals)
        self.assertIn('Never invent', approvals)
        qa = section(text, '## Phase 5b:', '## Phase 6:')
        for branch in ('qa-lead', '/smoke-check', '/team-qa [affected-system]',
                       '/team-qa sprint', 'Do not skip this gate'):
            self.assertIn(branch, qa)
        self.assertIn('## Phase 7: Post-Deploy Verification', text)
        self.assertIn('release branch AND development branch', text)

    def test_narrative_phase_two_requires_decision_before_level_delegate(self):
        text = source('team-narrative')
        phase_two = section(text, '### Phase 2:', '### Phase 3:')
        self.assertIn('AskUserQuestion', phase_two)
        for proposal in ('lore', 'dialogue', 'visual'):
            self.assertIn(proposal, phase_two)
        for outcome in ('[A] Approve', '[B] Revise', '[C] Stop'):
            self.assertIn(outcome, phase_two)
        self.assertIn('Do not spawn the level-designer', phase_two)
        self.assertIn('present the revised outputs', phase_two)
        self.assertIn('partial report', phase_two)

    def test_sprint_phase_zero_resolves_explicit_flag_once(self):
        text = source('sprint-plan')
        phase_zero = section(text, '## Phase 0:', '## Phase 1:')
        self.assertNotIn('**Review mode check**', phase_zero)
        self.assertIn('Do not re-read or overwrite the resolved mode', phase_zero)
        self.assertIn('do not prompt or change the saved setting', phase_zero)
        self.assertLess(phase_zero.index('If `--review'),
                        phase_zero.index('Else if `production/review-mode.txt` exists'))
        self.assertIn('Else if this is a `new` sprint', phase_zero)
        self.assertIn('AskUserQuestion', phase_zero)
        self.assertIn('Else (`update` or `status`)', phase_zero)

    def test_sprint_new_update_and_yaml_use_mode_aware_feasibility(self):
        text = source('sprint-plan')
        phase_two = section(text, '## Phase 2:', '## Phase 3:')
        self.assertNotIn('producer feasibility gate (Phase 4) runs first', phase_two)
        self.assertIn('`full`', phase_two)
        self.assertIn('`lean`/`solo`', phase_two)
        self.assertIn('coordinator', phase_two)
        self.assertIn('Re-run the mode-appropriate feasibility review', phase_two)
        phase_three = section(text, '## Phase 3:', '## Phase 4:')
        self.assertIn('mode-appropriate feasibility review', phase_three)

    def test_sprint_skipped_producer_still_checks_feasibility_and_writes(self):
        text = source('sprint-plan')
        phase_four = section(text, '## Phase 4:', '## Phase 5:')
        for mode in ('solo', 'lean'):
            line = next(line for line in phase_four.splitlines() if line.startswith('- `' + mode + '`'))
            self.assertIn('coordinator feasibility review below', line)
            self.assertNotIn('Proceed to Phase 5', line)
        self.assertIn('`full` → spawn', phase_four)
        self.assertIn('coordinator must check', phase_four)
        for item in ('capacity', 'estimates', 'dependencies', 'carryover', 'milestone'):
            self.assertIn(item, phase_four)
        self.assertIn('all review modes', phase_four)
        self.assertIn('May I write the sprint plan', phase_four)
        self.assertIn('production/sprint-status.yaml', phase_four)

    def test_sprint_audits_runnable_prerequisites_before_selecting_stories(self):
        text = source('sprint-plan')
        self.assertIn('## Phase 1a: Runnable Goal Prerequisite Audit', text)
        audit = section(text, '## Phase 1a:', '## Phase 2:')
        self.assertIn('before selecting stories', audit)
        for prerequisite in ('scenes', 'assets', 'services', 'tests'):
            self.assertIn(prerequisite, audit)
        for state in ('existing', 'scheduled', 'missing', 'deferred', 'blocked'):
            self.assertIn(state, audit)
        self.assertIn('reduced goal', audit)
        self.assertIn('Do not claim the goal is runnable', audit)
        plan = section(text, '## Phase 2:', '## Phase 3:')
        self.assertIn('## Runnable Goal Prerequisites', plan)
        self.assertIn('Re-run the prerequisite audit', plan)
        feasibility = section(text, '## Phase 4:', '## Phase 5:')
        self.assertIn('prerequisite audit', feasibility)
        self.assertIn('missing prerequisite', feasibility)

    def test_sprint_next_steps_preserve_gate_scope_and_non_director_duties(self):
        text = section(source('sprint-plan'), '## Phase 6:', 'NEVER_MATCH_END')
        self.assertNotIn('skip all gates unconditionally', text)
        self.assertNotIn('skip automated director gates', text)
        for contract in ('PHASE-GATE', 'coordinator feasibility', 'user decisions',
                         'QA plan', 'non-director requirements'):
            self.assertIn(contract, text)

    def test_hotfix_spec_requires_authorization_signoffs_and_qa_reentry(self):
        text = (ROOT / 'CCGS Skill Testing Framework/skills/utility/hotfix.md').read_text()
        self.assertNotIn('merge with\n   known regression', text)
        self.assertNotIn('No gate is invoked within this skill', text)
        for contract in ('lead-programmer', 'qa-tester', 'producer', 'qa-lead',
                         'All three must return APPROVE', 'QA re-entry',
                         'before implementation', 'explicit denial',
                         'does not authorize code changes'):
            self.assertIn(contract, text)
        self.assertIn('do not deploy or merge', text)
        self.assertIn('Prior explicit user authorization', text)

    def test_dev_story_spec_keeps_closure_separate_and_freshness_bounded(self):
        text = (ROOT / 'CCGS Skill Testing Framework/skills/pipeline/dev-story.md').read_text()
        self.assertNotIn('Story is marked Complete after user confirmation', text)
        self.assertNotIn('LP-CODE-REVIEW gate spawns after implementation', text)
        for contract in ('does not close the story', '/code-review', '/story-done',
                         'Config/Data', 'inline', 'per-ADR', 'SHA256',
                         'fresh', 'stale', 'bounded', 'Proposed', 'Missing ADR',
                         'amendment', 'next_offset'):
            self.assertIn(contract, text)
        self.assertIn('production/review-mode.txt', text)

    def test_architecture_skill_heading_precedes_unchanged_template(self):
        text = source('architecture-decision')
        outside_h1 = []
        fenced = False
        for line in text.splitlines():
            if line.lstrip().startswith('```'):
                fenced = not fenced
            elif not fenced and line.startswith('# '):
                outside_h1.append(line)
        self.assertEqual(outside_h1, ['# architecture-decision: write an Architecture Decision Record (ADR)'])
        self.assertIn('```markdown\n# ADR-[NNNN]: [Title]', text)
        self.assertLess(text.index(outside_h1[0]), text.index('## 0. Parse Arguments'))


if __name__ == '__main__':
    unittest.main()
