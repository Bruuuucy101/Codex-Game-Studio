import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch
from fixtures import Server, request, image_response, png, cli


class JobsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve(); self.state=self.root/'.ccgs-assets'; request(self.root)
    def submit(self,server,**kwargs):
        from ccgs.assets.jobs import submit
        with patch.dict(os.environ,{'PIXELLAB_SECRET':'fixture-secret'}):
            return submit(self.root,self.state,'request.json','one',write=True,transport=server.transport(),**kwargs)
    def test_jobs_sync_journal_repeat_conflict_and_private_permissions(self):
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(200,image_response(),{})
            one=self.submit(server); two=self.submit(server)
            self.assertEqual(one['status'],'generated'); self.assertEqual(two['status'],'generated')
            self.assertEqual(len(server.calls),1)
            request(self.root,parameters={'description':'changed','image_size':{'width':64,'height':64}})
            with self.assertRaisesRegex(ValueError,'conflict'): self.submit(server)
            for p in self.state.rglob('*'):
                self.assertEqual(p.stat().st_mode & 0o077,0)
                if p.is_file(): self.assertNotIn(b'fixture-secret',p.read_bytes())
    def test_jobs_response_loss_is_unknown_and_never_resubmits(self):
        from ccgs.assets.jobs import resume
        def dropped(handler):
            handler.connection.shutdown(socket.SHUT_RDWR); handler.connection.close()
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=dropped
            result=self.submit(server)
            self.assertEqual(result['status'],'submission_unknown')
            self.assertEqual(self.submit(server)['status'],'submission_unknown')
            self.assertEqual(resume(self.root,self.state,'one',write=True,transport=server.transport())['status'],'submission_unknown')
            self.assertEqual(len(server.calls),1)
    def test_jobs_async_status_is_read_only_resume_never_posts(self):
        from ccgs.assets.jobs import status,resume
        request(self.root,'create-image-pixflux-background')
        with Server() as server:
            server.routes['POST','/v2/create-image-pixflux-background']=(202,{'background_job_id':'job-123','status':'processing'},{})
            server.routes['GET','/v2/background-jobs/job-123']=(200,{'id':'job-123','created_at':'now','status':'completed','last_response':image_response()},{})
            self.submit(server)
            before={p:p.read_bytes() for p in self.state.rglob('*') if p.is_file()}
            with patch.dict(os.environ,{'PIXELLAB_SECRET':'fixture-secret'}):
                self.assertEqual(status(self.root,self.state,'one',transport=server.transport())['remote_status'],'generated')
                self.assertEqual(before,{p:p.read_bytes() for p in before})
                result=resume(self.root,self.state,'one',write=True,wait_seconds=0,transport=server.transport())
                self.assertEqual(result['status'],'generated')
            self.assertEqual(sum(c[0]=='POST' for c in server.calls),1)
    def test_jobs_unknown_completed_shape_keeps_private_evidence_and_task(self):
        from ccgs.assets.jobs import resume
        request(self.root,'generate-ui-v2')
        with Server() as server:
            server.routes['POST','/v2/generate-ui-v2']=(202,{'background_job_id':'job-123'},{})
            server.routes['GET','/v2/background-jobs/job-123']=(200,{'id':'job-123','created_at':'now','status':'completed','last_response':{'url':'https://example.com/a?signature=private-secret'}},{})
            self.submit(server)
            with patch.dict(os.environ,{'PIXELLAB_SECRET':'fixture-secret'}):
                result=resume(self.root,self.state,'one',write=True,transport=server.transport())
            self.assertEqual(result['status'],'unsupported_provider_result')
            self.assertEqual(result['task_id'],'job-123')
            self.assertNotIn('private-secret',json.dumps(result))
            self.assertTrue(any(b'private-secret' in p.read_bytes() for p in self.state.rglob('*') if p.is_file()))
            self.assertEqual(sum(c[0]=='POST' for c in server.calls),1)
    def test_jobs_collision_and_changed_sources_stop_before_post(self):
        (self.root/'assets/art').mkdir(parents=True); (self.root/'assets/art/guardian.png').write_bytes(png())
        with Server() as server:
            with self.assertRaisesRegex(ValueError,'collision'): self.submit(server)
            self.assertEqual(server.calls,[])
    def test_jobs_lock_contention_and_corrupt_receipt_never_post(self):
        from ccgs.assets.jobs import operation_lock
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(200,image_response(),{})
            with operation_lock(self.root,self.state,'one'):
                with self.assertRaisesRegex(ValueError,'locked'): self.submit(server)
            self.submit(server)
            receipt=self.state/'jobs/one/receipt.json'; receipt.write_text('{broken')
            with self.assertRaises(ValueError): self.submit(server)
            self.assertEqual(len(server.calls),1)
    def test_jobs_collect_is_create_only_owned_repeat_and_detects_modification(self):
        from ccgs.assets.jobs import collect
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(200,image_response(),{})
            self.submit(server)
            one=collect(self.root,self.state,'one',write=True,transport=server.transport())
            self.assertEqual(one['status'],'collected')
            inode=(self.root/'assets/art/guardian.png').stat().st_ino
            self.assertEqual(collect(self.root,self.state,'one',write=True)['status'],'collected')
            self.assertEqual(inode,(self.root/'assets/art/guardian.png').stat().st_ino)
            (self.root/'assets/art/guardian.png').write_bytes(b'modified by artist')
            with self.assertRaises(ValueError): collect(self.root,self.state,'one',write=True)
            self.assertEqual((self.root/'assets/art/guardian.png').read_bytes(),b'modified by artist')
    def test_jobs_link_before_receipt_crash_recovers_by_inode_not_hash(self):
        from ccgs.assets.jobs import collect
        from ccgs.assets import artifacts
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(200,image_response(),{})
            self.submit(server)
            original=artifacts.publish
            def crash(*args,**kwargs):
                original(*args,**kwargs)
                raise SystemExit('simulated process death after link')
            with patch.object(artifacts,'publish',side_effect=crash):
                with self.assertRaises(SystemExit): collect(self.root,self.state,'one',write=True)
            self.assertTrue((self.root/'assets/art/guardian.png').exists())
            self.assertEqual(collect(self.root,self.state,'one',write=True)['status'],'collected')
    def test_jobs_identical_bytes_competitor_never_adopted_or_deleted(self):
        from ccgs.assets.jobs import collect
        from ccgs.assets import artifacts
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(200,image_response(),{})
            self.submit(server)
            def competitor(root,dest,stage,digest):
                target=root/dest; target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(Path(stage).read_bytes())
                raise ValueError('output_collision')
            with patch.object(artifacts,'publish',side_effect=competitor):
                with self.assertRaises(ValueError): collect(self.root,self.state,'one',write=True)
            with self.assertRaises(ValueError): collect(self.root,self.state,'one',write=True)
            self.assertEqual((self.root/'assets/art/guardian.png').read_bytes(),png())
    def test_jobs_result_persisted_before_receipt_crash_is_recoverable_no_post(self):
        from ccgs.assets import jobs
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(200,image_response(),{})
            original=jobs.save_receipt
            def crash(root,state,id,receipt):
                if receipt['status']=='generated': raise SystemExit('after durable result')
                return original(root,state,id,receipt)
            with patch.object(jobs,'save_receipt',side_effect=crash):
                with self.assertRaises(SystemExit): self.submit(server)
            self.assertEqual(self.submit(server)['status'],'generated')
            self.assertEqual(len(server.calls),1)
    def test_jobs_ingest_validates_copies_and_keeps_owned_receipt(self):
        from ccgs.assets.jobs import ingest
        (self.root/'native.png').write_bytes(png())
        preview=ingest(self.root,self.state,'native.png','assets/art/native.png','ASSET-101')
        self.assertFalse(self.state.exists())
        result=ingest(self.root,self.state,'native.png','assets/art/native.png','ASSET-101',write=True)
        self.assertEqual(result['status'],'collected')
        self.assertEqual(result['review']['engine_import'],'pending')
        self.assertEqual(ingest(self.root,self.state,'native.png','assets/art/native.png','ASSET-101',write=True)['status'],'collected')

    def test_jobs_result_receipt_io_failure_preserves_recoverable_result(self):
        from ccgs.assets import jobs
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(200,image_response(),{})
            original=jobs.save_receipt
            def disk_error(root,state,id,receipt):
                if receipt['status']=='generated':raise OSError('fixture disk failure after durable result')
                return original(root,state,id,receipt)
            with patch.object(jobs,'save_receipt',side_effect=disk_error):
                try:self.submit(server)
                except (OSError,ValueError):pass
            self.assertEqual(self.submit(server)['status'],'generated')
            self.assertEqual(len(server.calls),1)
    def test_jobs_source_change_after_submission_blocks_collection(self):
        from ccgs.assets.jobs import collect
        (self.root/'style.md').write_text('original style')
        request(self.root,source_files=['style.md'])
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(200,image_response(),{})
            self.submit(server)
            (self.root/'style.md').write_text('revised style')
            with self.assertRaisesRegex(ValueError,'changed'):collect(self.root,self.state,'one',write=True)
            self.assertFalse((self.root/'assets').exists())
    def test_jobs_unsupported_hardlink_filesystem_stops_before_post(self):
        with Server() as server:
            with patch('os.link',side_effect=OSError('unsupported filesystem')):
                with self.assertRaisesRegex(ValueError,'hardlink_unsupported'):self.submit(server)
            self.assertEqual(server.calls,[])
    def test_jobs_pending_wait_deadline_keeps_pending_and_no_extra_post(self):
        from ccgs.assets.jobs import resume
        request(self.root,'create-image-pixflux-background')
        with Server() as server:
            server.routes['POST','/v2/create-image-pixflux-background']=(202,{'background_job_id':'job-123'},{})
            server.routes['GET','/v2/background-jobs/job-123']=(200,{'id':'job-123','created_at':'now','status':'processing'},{})
            self.submit(server)
            with patch.dict(os.environ,{'PIXELLAB_SECRET':'x'}):
                result=resume(self.root,self.state,'one',write=True,wait_seconds=.02,transport=server.transport())
            self.assertEqual(result['status'],'pending');self.assertEqual(result['local_wait'],'deadline_exhausted')
            self.assertEqual(sum(c[0]=='POST' for c in server.calls),1)
    def test_jobs_foreign_lock_is_never_removed_by_previous_owner(self):
        from ccgs.assets.jobs import operation_lock
        with operation_lock(self.root,self.state,'one'):
            lock=self.state/'jobs/one/lock'
            lock.unlink();lock.write_text('foreign owner');lock.chmod(0o600)
        self.assertEqual(lock.read_text(),'foreign owner')

    def typed_upload(self,server):
        from ccgs.assets import jobs
        from fixtures import TypedAdapter
        (self.root/'input.png').write_bytes(png())
        request(self.root,'upload-fixture',provider='tripo',parameters={'image':'input.png'},outputs=[])
        server.routes['POST','/v3/files']=(200,{'code':0,'data':{'file_token':'file_private-token'}},{})
        adapters={'tripo':TypedAdapter()}
        with patch.dict(os.environ,{'TRIPO_API_KEY':'fixture-secret'}):
            result=jobs.submit(self.root,self.state,'request.json','upload',write=True,transport=server.transport(),adapters=adapters)
        return adapters,result
    def typed_generation(self,server,adapters):
        from ccgs.assets import jobs
        request(self.root,'generation-fixture',provider='tripo',parameters={'input_job':'upload'},outputs=[
            {'key':'first','path':'assets/art/first.png','format':'png','width':64,'height':64},
            {'key':'second','path':'assets/art/second.png','format':'png','width':64,'height':64}])
        server.routes['POST','/v3/generate']=(200,{'accepted':True},{})
        server.routes['GET','/first?signature=private-secret']=(200,png(),{})
        server.routes['GET','/second?signature=private-secret']=(200,png(),{})
        with patch.dict(os.environ,{'TRIPO_API_KEY':'fixture-secret'}):
            return jobs.submit(self.root,self.state,'request.json','generation',write=True,transport=server.transport(),adapters=adapters)
    def test_jobs_separate_upload_generation_and_private_dependency_pins(self):
        from ccgs.assets import jobs
        with Server() as server:
            adapters,uploaded=self.typed_upload(server)
            self.assertEqual(uploaded['status'],'completed');self.assertIsNone(uploaded['task_id'])
            before=len(server.calls)
            self.assertEqual(jobs.status(self.root,self.state,'upload',transport=server.transport(),adapters=adapters)['status'],'completed')
            self.assertEqual(len(server.calls),before)
            self.assertNotIn('file_private-token',json.dumps(uploaded))
            generated=self.typed_generation(server,adapters)
            self.assertEqual(generated['status'],'generated')
            op=jobs.load_operation(self.root,self.state,'generation',adapters=adapters)
            self.assertEqual(op['plan']['dependencies'][0]['id'],'upload')
            self.assertEqual(json.loads(server.calls[-1][3]),{'input':'file_private-token'})
            self.assertEqual(jobs.submit(self.root,self.state,'request.json','generation',write=True,transport=server.transport(),adapters=adapters)['status'],'generated')
            self.assertEqual(sum(c[0]=='POST' for c in server.calls),2)
            collected=jobs.collect(self.root,self.state,'generation',write=True,transport=server.transport(),adapters=adapters)
            self.assertEqual(collected['status'],'collected');self.assertEqual(len(collected['published']),2)
            self.assertNotIn('private-secret',json.dumps(collected))
            for c in server.calls:
                if c[0]=='GET':self.assertNotIn('Authorization',c[2])
    def test_jobs_all_targets_preflight_before_any_download(self):
        from ccgs.assets import jobs
        with Server() as server:
            adapters,_=self.typed_upload(server);self.typed_generation(server,adapters)
            (self.root/'assets/art').mkdir(parents=True)
            (self.root/'assets/art/second.png').write_bytes(png())
            before=len(server.calls)
            with self.assertRaisesRegex(ValueError,'collision'):jobs.collect(self.root,self.state,'generation',write=True,transport=server.transport(),adapters=adapters)
            self.assertEqual(len(server.calls),before);self.assertFalse((self.root/'assets/art/first.png').exists())
    def test_jobs_interrupted_multi_output_retains_artist_edits_for_inspection(self):
        from ccgs.assets import jobs,artifacts
        with Server() as server:
            adapters,_=self.typed_upload(server);self.typed_generation(server,adapters)
            original=artifacts.publish
            def interrupted(root,dest,stage,digest):
                if dest.endswith('second.png'):
                    (root/'assets/art/first.png').write_bytes(b'artist edit during collection')
                    raise ValueError('fixture second publication failure')
                return original(root,dest,stage,digest)
            with patch.object(artifacts,'publish',side_effect=interrupted):
                with self.assertRaises(ValueError):jobs.collect(self.root,self.state,'generation',write=True,transport=server.transport(),adapters=adapters)
            self.assertEqual((self.root/'assets/art/first.png').read_bytes(),b'artist edit during collection')
            self.assertFalse((self.root/'assets/art/second.png').exists())
            with self.assertRaises(ValueError):jobs.collect(self.root,self.state,'generation',write=True,transport=server.transport(),adapters=adapters)
    def test_jobs_typed_validation_json_is_collectable_without_mesh_claim(self):
        from ccgs.assets import jobs
        from fixtures import TypedAdapter
        adapters={'tripo':TypedAdapter()}
        request(self.root,'validation-fixture',provider='tripo',parameters={},outputs=[{'key':'validation','path':'assets/data/check.json','format':'json'}])
        with Server() as server:
            server.routes['POST','/v3/validate']=(200,{'data':{'riggable':False,'rig_type':'unknown'}},{})
            with patch.dict(os.environ,{'TRIPO_API_KEY':'fixture-secret'}):
                result=jobs.submit(self.root,self.state,'request.json','validate',write=True,transport=server.transport(),adapters=adapters)
            self.assertEqual(result['status'],'completed')
            collected=jobs.collect(self.root,self.state,'validate',write=True,transport=server.transport(),adapters=adapters)
            self.assertEqual(collected['status'],'collected')
            self.assertEqual(json.loads((self.root/'assets/data/check.json').read_text()),{'riggable':False,'rig_type':'unknown'})

    def test_jobs_http_credit_failure_exposes_only_safe_status_category(self):
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(402,{'detail':'fixture-secret and https://example.com/?private=1'},{})
            result=self.submit(server)
            self.assertEqual(result['diagnostic'],{'category':'provider_http_error','http_status':402})
            self.assertNotIn('fixture-secret',json.dumps(result));self.assertNotIn('private=1',json.dumps(result))
            self.assertEqual(len(server.calls),1)

    def crash_process(self,server,phase):
        import subprocess,sys
        from fixtures import REPO
        env=dict(os.environ,PIXELLAB_SECRET='fixture-secret')
        child=subprocess.run([sys.executable,str(REPO/'tests/asset_tools/crash_worker.py'),str(self.root),phase,server.origin],env=env,capture_output=True,text=True,timeout=15)
        self.assertEqual(child.returncode,73,child.stdout+child.stderr)
        # Explicit fixture operator inspection: child is dead, known test-owned lock remains.
        lock=self.state/'jobs/one/lock'
        self.assertTrue(lock.is_file())
        with self.assertRaisesRegex(ValueError,'locked'):
            from ccgs.assets.jobs import operation_lock
            with operation_lock(self.root,self.state,'one'):pass
        lock.unlink()  # This inspection/removal exists only in the test, never in production.
    def test_jobs_real_process_death_before_post_never_retries_uncertain_intent(self):
        with Server() as server:
            self.crash_process(server,'before-post')
            self.assertEqual(self.submit(server)['status'],'submission_unknown')
            self.assertEqual(server.calls,[])
    def test_jobs_real_process_death_after_result_keeps_saved_image_without_post(self):
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(200,image_response(),{})
            self.crash_process(server,'after-result')
            self.assertEqual(self.submit(server)['status'],'generated')
            self.assertEqual(len(server.calls),1)
    def test_jobs_real_process_death_after_link_recovers_retained_inode(self):
        from ccgs.assets.jobs import collect
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(200,image_response(),{})
            self.submit(server)
            self.crash_process(server,'after-link')
            inode=(self.root/'assets/art/guardian.png').stat().st_ino
            self.assertEqual(collect(self.root,self.state,'one',write=True)['status'],'collected')
            self.assertEqual((self.root/'assets/art/guardian.png').stat().st_ino,inode)
            self.assertEqual(len(server.calls),1)

    def test_jobs_ingestion_receipt_supports_readonly_status_and_owned_collection(self):
        from ccgs.assets.jobs import ingest,status,collect
        (self.root/'native.png').write_bytes(png())
        result=ingest(self.root,self.state,'native.png','assets/art/native.png','native',write=True)
        before={p:p.read_bytes() for p in self.state.rglob('*') if p.is_file()}
        self.assertEqual(status(self.root,self.state,result['id'])['status'],'collected')
        self.assertEqual(before,{p:p.read_bytes() for p in before})
        self.assertEqual(collect(self.root,self.state,result['id'],write=True)['status'],'collected')

    def test_jobs_upload_persistence_crash_and_separate_generation_do_not_repeat_post(self):
        from ccgs.assets import jobs
        from fixtures import TypedAdapter
        adapters={'tripo':TypedAdapter()}
        with Server() as server:
            original=jobs.save_receipt
            def crash(root,state,id,receipt):
                if receipt['status']=='completed':raise SystemExit('after private upload result persistence')
                return original(root,state,id,receipt)
            with patch.object(jobs,'save_receipt',side_effect=crash):
                with self.assertRaises(SystemExit):self.typed_upload(server)
            with patch.dict(os.environ,{'TRIPO_API_KEY':'x'}):
                uploaded=jobs.submit(self.root,self.state,'request.json','upload',write=True,transport=server.transport(),adapters=adapters)
            self.assertEqual(uploaded['status'],'completed')
            self.assertEqual(len(server.calls),1)
            generated=self.typed_generation(server,adapters)
            self.assertEqual(generated['status'],'generated')
            self.assertEqual([c[1] for c in server.calls],['/v3/files','/v3/generate'])

    def test_jobs_expired_signed_artifact_url_can_refresh_known_task_without_post(self):
        from ccgs.assets import jobs
        with Server() as server:
            adapters,_=self.typed_upload(server);self.typed_generation(server,adapters)
            server.routes['GET','/first?signature=private-secret']=(403,{'secret':'expired'}, {})
            with self.assertRaises(ValueError):jobs.collect(self.root,self.state,'generation',write=True,transport=server.transport(),adapters=adapters)
            server.routes['GET','/v3/tasks/task-generation-fixture']=(200,{'urls':{'first':'https://fixture-cdn.example/new-first?signature=new-secret','second':'https://fixture-cdn.example/new-second?signature=new-secret'}},{})
            server.routes['GET','/new-first?signature=new-secret']=(200,png(),{})
            server.routes['GET','/new-second?signature=new-secret']=(200,png(),{})
            with patch.dict(os.environ,{'TRIPO_API_KEY':'x'}):
                jobs.resume(self.root,self.state,'generation',write=True,wait_seconds=0,transport=server.transport(),adapters=adapters)
            self.assertTrue(any(c[1]=='/v3/tasks/task-generation-fixture' for c in server.calls))
            result=jobs.collect(self.root,self.state,'generation',write=True,transport=server.transport(),adapters=adapters)
            self.assertEqual(result['status'],'collected')
            self.assertEqual(sum(c[0]=='POST' for c in server.calls),2)

    def test_jobs_unknown_evidence_never_persists_echoed_api_authorization(self):
        with Server() as server:
            server.routes['POST','/v2/create-image-pixen']=(200,{'authorization':'Bearer fixture-secret','detail':'echo fixture-secret','result_url':'https://example.com/a?signature=allowed-private-token'},{})
            result=self.submit(server)
            self.assertEqual(result['status'],'unsupported_provider_result')
            for path in self.state.rglob('*'):
                if path.is_file():self.assertNotIn(b'fixture-secret',path.read_bytes())
            self.assertTrue(any(b'allowed-private-token' in path.read_bytes() for path in self.state.rglob('*') if path.is_file()))

    def test_jobs_collected_repeat_rejects_deleted_target(self):
        from ccgs.assets.jobs import ingest, collect
        (self.root/'native.png').write_bytes(png())
        result=ingest(self.root,self.state,'native.png','assets/art/native.png','native',write=True)
        target=self.root/'assets/art/native.png'
        target.unlink()
        with self.assertRaisesRegex(ValueError,'collected_output_missing_or_changed'):
            collect(self.root,self.state,result['id'],write=True)
        self.assertFalse(target.exists())

    def test_jobs_failed_publication_retains_target_staging_and_journal(self):
        from ccgs.assets import jobs, artifacts
        (self.root/'native.png').write_bytes(png())
        original=artifacts.publish
        def failure_after_link(*args,**kwargs):
            original(*args,**kwargs)
            raise ValueError('fixture failure after publication')
        with patch.object(artifacts,'publish',side_effect=failure_after_link):
            with self.assertRaisesRegex(ValueError,'fixture failure after publication'):
                jobs.ingest(self.root,self.state,'native.png','assets/art/native.png','native',write=True)
        target=self.root/'assets/art/native.png'
        self.assertTrue(target.is_file(), 'failure cleanup must retain a published target')
        inode=target.stat().st_ino
        receipts=list(self.state.glob('jobs/*/receipt.json'))
        self.assertEqual(len(receipts),1)
        receipt=json.loads(receipts[0].read_text())
        self.assertEqual(receipt['status'],'generated')
        stage=receipts[0].parent/receipt['staged']['artifact']['file']
        self.assertEqual(stage.stat().st_ino,inode)
        result=jobs.collect(self.root,self.state,receipt['id'],write=True)
        self.assertEqual(result['status'],'collected')
        self.assertEqual(target.stat().st_ino,inode)

    def test_jobs_partial_collection_retains_first_and_recovers_missing_second(self):
        from ccgs.assets import jobs, artifacts
        with Server() as server:
            adapters,_=self.typed_upload(server)
            self.typed_generation(server,adapters)
            original=artifacts.publish
            def fail_second(root,destination,staged,digest):
                if destination.endswith('second.png'):
                    raise ValueError('fixture second link failure')
                return original(root,destination,staged,digest)
            with patch.object(artifacts,'publish',side_effect=fail_second):
                with self.assertRaisesRegex(ValueError,'fixture second link failure'):
                    jobs.collect(self.root,self.state,'generation',write=True,transport=server.transport(),adapters=adapters)
            first=self.root/'assets/art/first.png'
            self.assertTrue(first.is_file())
            inode=first.stat().st_ino
            self.assertFalse((self.root/'assets/art/second.png').exists())
            operation=jobs.load_operation(self.root,self.state,'generation',adapters=adapters)
            self.assertEqual(operation['receipt']['status'],'generated')
            self.assertEqual(set(operation['receipt']['published']),{'first'})
            self.assertEqual(set(operation['receipt']['staged']),{'first','second'})
            calls=len(server.calls)
            result=jobs.collect(self.root,self.state,'generation',write=True,transport=server.transport(),adapters=adapters)
            self.assertEqual(result['status'],'collected')
            self.assertEqual(first.stat().st_ino,inode)
            self.assertTrue((self.root/'assets/art/second.png').is_file())
            self.assertEqual(len(server.calls),calls)
