"""Real CLI/filesystem/gh subprocess contracts. No network or live board claims."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from fixtures import story, file_hashes

REPO = Path(__file__).resolve().parents[2]
CLI = REPO / 'tools/ccgs_codex.py'


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve(); self.root = self.base / 'studio'; self.root.mkdir()
        self.source = story(self.root)
        self.remote = self.base / 'remote.json'
        self.bin = self.base / 'bin'; self.bin.mkdir()
        executable = self.bin / 'gh'
        executable.write_text('#!' + sys.executable + '\n' + (REPO / 'tests/board_sync/fake_gh.py').read_text().split('\n', 1)[1]); executable.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'], FAKE_GH_STATE=str(self.remote), PYTHONDONTWRITEBYTECODE='1')
        self.put({'projects': [], 'fields': [], 'items': []})

    def get(self):
        return json.loads(self.remote.read_text())

    def put(self, state):
        self.remote.write_text(json.dumps(state))

    def cli(self, *args, ok=True):
        p = subprocess.run([sys.executable, str(CLI), '--root', str(self.root), 'board-sync', *args], env=self.env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0 if ok else 1, p.stdout + p.stderr)
        self.assertNotIn('SUPER_SECRET', p.stdout + p.stderr)
        self.assertTrue(p.stdout.startswith('{'), 'CLI must emit JSON, not a traceback: ' + p.stderr)
        return json.loads(p.stdout)

    def setup_board(self):
        return self.cli('setup', '--owner', 'octocat', '--namespace', 'game', '--title', 'Studio', '--write')

    def calls(self, mutations=False):
        calls = self.get().get('calls', [])
        return [x for x in calls if x['query'].startswith('mutation')] if mutations else calls

    def failure(self, operation, after=False):
        s = self.get(); s['failure'] = {'operation':operation, 'after':after, 'remaining':1}; self.put(s)

    def test_setup_preview_has_no_local_or_remote_writes(self):
        before = file_hashes(self.root)
        r = self.cli('setup', '--owner','octocat','--namespace','game','--title','Studio')
        self.assertEqual(r['status'], 'PREVIEW'); self.assertEqual(file_hashes(self.root), before)
        self.assertEqual(self.calls(True), [])

    def test_setup_create_private_and_unchanged_reentry(self):
        self.setup_board(); n = len(self.calls(True)); self.setup_board()
        self.assertEqual(len(self.calls(True)), n)
        p = self.get()['projects'][0]; self.assertFalse(p['public']); self.assertEqual(p['title'],'Studio')
        config = json.loads((self.root/'.ccgs-board/board.config.json').read_text())
        self.assertEqual(config['project_id'],p['id']); self.assertEqual(config['owner_type'],'User')

    def test_setup_uncertain_create_reconciles_without_duplicate(self):
        self.failure('CreateProject', True); self.cli('setup','--owner','octocat','--namespace','game','--title','Studio','--write',ok=False)
        self.setup_board(); self.assertEqual(len(self.get()['projects']),1)
        self.assertEqual(sum(x['operation']=='CreateProject' for x in self.calls()),1)

    def test_setup_unresolved_create_never_retried(self):
        self.failure('CreateProject'); self.cli('setup','--owner','octocat','--namespace','game','--title','Studio','--write',ok=False)
        self.cli('setup','--owner','octocat','--namespace','game','--title','Studio','--write',ok=False)
        self.assertEqual(sum(x['operation']=='CreateProject' for x in self.calls()),1)

    def test_setup_paginated_organization_adoption_and_config_conflict(self):
        owner = {'id':'ORG_1','login':'studio','__typename':'Organization'}
        s = self.get(); s['owner'] = owner
        s['projects'] = [{'id':f'PROJECT_{n}','number':n,'title':f'P{n}','url':f'https://github.com/orgs/studio/projects/{n}','public':False,'readme':'','owner':owner} for n in (1,2,3)]; self.put(s)
        self.cli('setup','--owner','studio','--namespace','game','--number','3','--write')
        self.assertEqual(self.calls(True),[])
        self.cli('setup','--owner','studio','--namespace','game','--number','2','--write',ok=False)
        self.assertEqual(json.loads((self.root/'.ccgs-board/board.config.json').read_text())['project_number'],3)

    def test_sync_pagination_preserves_options_and_zero_change_repeat(self):
        self.setup_board(); s = self.get()
        s['fields'] = [{'id':'FIELD_1','name':'Stage','__typename':'ProjectV2SingleSelectField','dataType':'SINGLE_SELECT','options':[{'id':'KEEP','name':'Custom','color':'RED','description':'keep me'}]}]
        self.put(s); before = self.source.read_bytes(); self.cli('sync','--write')
        s = self.get(); self.assertEqual(s['fields'][0]['options'][0],{'id':'KEEP','name':'Custom','color':'RED','description':'keep me'})
        self.assertEqual(len(s['items']),1); self.assertEqual(len(s['items'][0]['values']),4)
        n = len(self.calls(True)); result = self.cli('sync','--write'); self.assertEqual(result['changes'],[])
        self.assertEqual(len(self.calls(True)),n); self.assertEqual(self.source.read_bytes(),before)
        self.assertGreater(sum(x['operation']=='Values' for x in self.calls()),4)

    def test_sync_dry_diff_does_not_write_state_or_board(self):
        self.setup_board(); before = file_hashes(self.root); n = len(self.calls(True))
        r = self.cli('sync','--dry'); self.assertTrue(r['changes'])
        self.assertEqual(file_hashes(self.root),before); self.assertEqual(len(self.calls(True)),n)

    def test_sync_repairs_remote_drift_and_preserves_unmanaged(self):
        self.setup_board(); self.cli('sync','--write'); s = self.get()
        s['items'][0]['content'].update(title='drift',body=s['items'][0]['content']['body']+'\ndrift')
        s['items'][0]['values'] = []
        unmanaged = {'id':'ITEM_2','isArchived':False,'type':'DRAFT_ISSUE','content':{'id':'DRAFT_2','__typename':'DraftIssue','title':'Personal','body':'leave alone'},'values':[]}
        s['items'].append(unmanaged); self.put(s); self.cli('sync','--write')
        self.assertEqual(self.get()['items'][1],unmanaged); self.assertNotEqual(self.get()['items'][0]['content']['title'],'drift')

    def test_sync_duplicate_and_redacted_stop_before_mutations(self):
        self.setup_board(); self.cli('sync','--write'); s = self.get(); original = copy.deepcopy(s)
        dupe = copy.deepcopy(s['items'][0]); dupe['id']='ITEM_2'; s['items'].append(dupe); self.put(s)
        n = len(self.calls(True)); self.cli('sync','--write',ok=False); self.assertEqual(len(self.calls(True)),n)
        original['items'].append({'id':'ITEM_2','isArchived':False,'type':'REDACTED','content':None,'values':[]}); self.put(original)
        n=len(self.calls(True)); self.cli('sync','--write',ok=False); self.assertEqual(len(self.calls(True)),n)

    def test_sync_archived_stale_and_epic_isolation(self):
        story(self.root,epic='other'); self.setup_board(); self.cli('sync','--write'); s=self.get()
        s['items'][0]['isArchived']=True; s['items'][1]['content']['title']='other epic drift'; self.put(s); n=len(self.calls(True))
        r=self.cli('sync','--epic','combat','--write'); self.assertEqual(len(self.calls(True)),n); self.assertEqual(len(r['archived']),1)
        self.source.unlink(); r=self.cli('sync','--epic','combat'); self.assertEqual(len(r['stale']),1); self.assertNotIn('other',str(r['stale']))

    def test_sync_uncertain_draft_creation_recovered_on_rerun(self):
        self.setup_board(); self.failure('CreateDraft',True); self.cli('sync','--write',ok=False)
        self.cli('sync','--write'); self.assertEqual(len(self.get()['items']),1)
        self.assertEqual(sum(x['operation']=='CreateDraft' for x in self.calls()),1)

    def test_sync_partial_field_and_value_failure_recovers(self):
        self.setup_board(); self.failure('CreateField',True); self.cli('sync','--write',ok=False)
        self.failure('SetValue',True); self.cli('sync','--write',ok=False)
        self.cli('sync','--write'); self.assertEqual(len(self.get()['fields']),4); self.assertEqual(len(self.get()['items']),1)

    def test_sync_conflicting_type_and_option_limit_preflight(self):
        self.setup_board(); s=self.get(); s['fields']=[{'id':'FIELD_1','name':'Stage','__typename':'ProjectV2Field','dataType':'TEXT'}]; self.put(s)
        n=len(self.calls(True)); self.cli('sync','--write',ok=False); self.assertEqual(len(self.calls(True)),n)
        s=self.get(); s['fields']=[{'id':'FIELD_1','name':'Epic','__typename':'ProjectV2SingleSelectField','dataType':'SINGLE_SELECT','options':[{'id':str(i),'name':str(i),'color':'GRAY','description':''} for i in range(50)]}]; self.put(s)
        self.cli('sync','--write',ok=False); self.assertEqual(len(self.calls(True)),n)

    def test_sync_snapshot_change_before_writes_fails(self):
        self.setup_board(); s=self.get(); s.update(change_source_on='Items',source_path=str(self.source)); self.put(s)
        n=len(self.calls(True)); self.cli('sync','--write',ok=False); self.assertEqual(len(self.calls(True)),n)

    def test_sync_lock_and_unsafe_config_fail_closed(self):
        self.setup_board(); lock=self.root/'.ccgs-board/lock'; lock.mkdir()
        n=len(self.calls(True)); r=self.cli('sync','--write',ok=False); self.assertIn('LOCKED',str(r)); self.assertEqual(len(self.calls(True)),n)
        lock.rmdir(); config=self.root/'.ccgs-board/board.config.json'; s=json.loads(config.read_text()); s['host']='evil.example'; config.write_text(json.dumps(s))
        self.cli('sync','--write',ok=False); self.assertEqual(len(self.calls(True)),n)

    def test_sync_auth_error_is_safe_and_no_mutation(self):
        self.setup_board(); self.failure('Project'); n=len(self.calls(True))
        r=self.cli('sync','--write',ok=False); self.assertIn('GitHub',r['error']); self.assertEqual(len(self.calls(True)),n)

    def test_sync_special_story_path_remains_stable(self):
        self.source.unlink(); story(self.root,name='story-002-跳跃 # <test>.md')
        self.setup_board(); self.cli('sync','--write'); n=len(self.calls(True)); self.cli('sync','--write')
        self.assertEqual(len(self.get()['items']),1); self.assertEqual(len(self.calls(True)),n)

    def test_sync_symlink_state_and_unowned_mapping_preserved(self):
        self.setup_board(); other=self.base/'other.json'; other.write_text('{"keep":true}')
        mapping=self.root/'.ccgs-board/mapping.json'; mapping.symlink_to(other)
        n=len(self.calls(True)); self.cli('sync','--write',ok=False)
        self.assertEqual(other.read_text(),'{"keep":true}'); self.assertEqual(len(self.calls(True)),n)
        mapping.unlink(); mapping.write_text('{"schema_version":1,"keep":true}')
        self.cli('sync','--write',ok=False); self.assertEqual(mapping.read_text(),'{"schema_version":1,"keep":true}')

    def test_transport_retries_reads_but_never_mutations_and_handles_timeout(self):
        sys.path.insert(0,str(REPO/'tools'))
        from ccgs.board_github import GitHub, GitHubError
        from unittest.mock import patch
        self.setup_board(); s=self.get(); s['failure']={'operation':'Project','remaining':2}; s['transient']=True; self.put(s)
        with patch.dict(os.environ,self.env):
            gh=GitHub(str(self.bin/'gh'),timeout=0.5)
            self.assertEqual(gh.project('PROJECT_1')['id'],'PROJECT_1')
            s=self.get(); s.update(sleep_on='Project',sleep_seconds=0.8); self.put(s)
            with self.assertRaisesRegex(GitHubError,'timed out'):
                gh.project('PROJECT_1')
            s=self.get(); s.pop('sleep_on'); s['failure']={'operation':'CreateField','remaining':3}; self.put(s)
            with self.assertRaisesRegex(GitHubError,'UNCERTAIN'):
                gh.mutate('CreateField',{'projectId':'PROJECT_1','name':'Stage','dataType':'SINGLE_SELECT','singleSelectOptions':[{'name':'Ready','color':'GRAY','description':''}]})
            self.assertEqual(self.get()['failure']['remaining'],2)

    def test_sync_unresolved_draft_create_never_retried(self):
        self.setup_board(); self.failure('CreateDraft'); self.cli('sync','--write',ok=False)
        self.cli('sync','--write',ok=False)
        self.assertEqual(sum(x['operation']=='CreateDraft' for x in self.calls()),1)

    def test_setup_dry_does_not_repair_pending_creation(self):
        self.failure('CreateProject',True)
        self.cli('setup','--owner','octocat','--namespace','game','--title','Studio','--write',ok=False)
        before=file_hashes(self.root); n=len(self.calls(True))
        self.cli('setup','--owner','octocat','--namespace','game','--title','Studio','--dry')
        self.assertEqual(file_hashes(self.root),before); self.assertEqual(len(self.calls(True)),n)

    def test_setup_existing_adoption_keeps_remote_metadata(self):
        self.setup_board(); s=self.get(); p=s['projects'][0]; p.update(title='Personal',readme='hand authored',public=True); self.put(s)
        shutil.rmtree(self.root/'.ccgs-board'); n=len(self.calls(True))
        self.cli('setup','--owner','octocat','--namespace','game','--number','1','--write')
        self.assertEqual(len(self.calls(True)),n); self.assertEqual(self.get()['projects'][0],p)

    def test_setup_missing_gh_reports_actionable_error(self):
        self.env['PATH']=str(self.base/'nonexistent')
        r=self.cli('setup','--owner','octocat','--namespace','game','--title','Studio',ok=False)
        self.assertIn('MISSING_GH',r['error']); self.assertFalse((self.root/'.ccgs-board').exists())

    def test_config_duplicate_keys_rejected_before_github(self):
        self.setup_board(); config=self.root/'.ccgs-board/board.config.json'
        content=config.read_text(); config.write_text(content.replace('"namespace": "game"','"namespace": "wrong", "namespace": "game"'))
        n=len(self.calls()); self.cli('sync','--write',ok=False); self.assertEqual(len(self.calls()),n)

    def test_sync_write_before_real_timeout_then_cli_rerun_adopts(self):
        self.setup_board(); s=self.get(); s['timeout_after']='CreateDraft'; self.put(s)
        r=self.cli('sync','--write',ok=False); self.assertIn('timed out',r['error'])
        self.cli('sync','--write'); self.assertEqual(len(self.get()['items']),1)
        self.assertEqual(sum(x['operation']=='CreateDraft' for x in self.calls()),1)

    def test_setup_explicit_recovery_adoption_does_not_rewrite_unrelated_project(self):
        self.setup_board(); s=self.get(); project=s['projects'][0]; project.update(title='Personal',readme='original',public=True); self.put(s)
        shutil.rmtree(self.root/'.ccgs-board'); self.failure('CreateProject')
        self.cli('setup','--owner','octocat','--namespace','game','--title','Studio','--write',ok=False)
        n=len(self.calls(True)); self.cli('setup','--owner','octocat','--namespace','game','--number','1','--write')
        self.assertEqual(self.get()['projects'][0],project); self.assertEqual(len(self.calls(True)),n)

    def test_sync_malformed_owned_state_has_safe_cli_failure(self):
        self.setup_board(); p=self.root/'.ccgs-board/state.json'
        p.write_text(json.dumps({'schema_version':1,'kind':'state','pending_create':'ghp_SUPER_SECRET_TOKEN'}))
        self.cli('sync','--write',ok=False)

    def test_sync_final_remote_verification_catches_concurrent_drift(self):
        self.setup_board(); s=self.get(); s['drift_on_second_project_read']=True; self.put(s)
        r=self.cli('sync','--write',ok=False); self.assertIn('BOARD_VERIFICATION_FAILED',r['error'])
        state=json.loads((self.root/'.ccgs-board/state.json').read_text())
        self.assertEqual(state['status'],'PARTIAL_OR_UNCERTAIN')

    def test_sync_filtered_first_export_uses_selected_stories_only(self):
        story(self.root,epic='other'); self.setup_board(); self.cli('sync','--epic','combat','--write')
        remote=self.get(); self.assertEqual(len(remote['items']),1)
        epic=next(f for f in remote['fields'] if f['name']=='Epic')
        self.assertEqual([o['name'] for o in epic['options']],['combat'])

    def test_setup_ambiguous_title_has_candidates_and_no_writes(self):
        self.setup_board(); s=self.get(); second=copy.deepcopy(s['projects'][0]); second.update(id='PROJECT_2',number=2,url='https://github.com/users/octocat/projects/2'); s['projects'].append(second); self.put(s)
        shutil.rmtree(self.root/'.ccgs-board'); n=len(self.calls(True))
        r=self.cli('setup','--owner','octocat','--namespace','game','--title','Studio','--write',ok=False)
        self.assertIn('SETUP_AMBIGUOUS',r['error']); self.assertEqual(len(self.calls(True)),n)
