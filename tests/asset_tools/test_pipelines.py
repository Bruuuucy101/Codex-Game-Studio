import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from fixtures import Server, glb, png


def write_request(root, provider, operation, parameters, output, *, validation=False):
    value = {'schema_version': 1, 'provider': provider, 'operation': operation,
             'asset_id': 'fixture', 'standalone': True, 'source_files': [],
             'parameters': parameters,
             'outputs': ([{'key': 'validation', 'path': output, 'format': 'json'}]
                         if validation else ([] if output is None else
                         [{'key': 'model', 'path': output, 'format': 'glb'}]))}
    (root / 'request.json').write_text(json.dumps(value))


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.state = self.root / '.ccgs-assets'

    def submit_resume(self, server, operation_id):
        from ccgs.assets import jobs
        submitted = jobs.submit(self.root, self.state, 'request.json', operation_id,
                                write=True, transport=server.transport())
        self.assertEqual(submitted['status'], 'pending')
        return jobs.resume(self.root, self.state, operation_id, write=True, wait_seconds=0,
                           transport=server.transport())

    def state_bytes(self):
        return {str(path.relative_to(self.state)): path.read_bytes()
                for path in self.state.rglob('*') if path.is_file()}

    def test_meshy_preview_refine_rig_animation_restart_posts_each_stage_once(self):
        from ccgs.assets import jobs
        with Server() as server, patch.dict(os.environ, {'MESHY_API_KEY': 'fixture-secret'}):
            write_request(self.root, 'meshy', 'text-to-3d-preview',
                          {'prompt': 'Stone guardian', 'ai_model': 'meshy-6'}, 'assets/models/preview.glb')
            server.routes['POST', '/openapi/v2/text-to-3d'] = (200, {'result': 'preview-1'}, {})
            server.routes['GET', '/openapi/v2/text-to-3d/preview-1'] = (200, {'id': 'preview-1', 'status': 'SUCCEEDED',
                'model_urls': {'glb': 'https://fixture-cdn.example/preview.glb'}}, {})
            self.assertEqual(self.submit_resume(server, 'preview')['status'], 'generated')

            write_request(self.root, 'meshy', 'text-to-3d-refine',
                          {'preview_job': 'preview', 'enable_pbr': True}, 'assets/models/refine.glb')
            server.routes['POST', '/openapi/v2/text-to-3d'] = (200, {'result': 'refine-1'}, {})
            server.routes['GET', '/openapi/v2/text-to-3d/refine-1'] = (200, {'id': 'refine-1', 'status': 'SUCCEEDED',
                'model_urls': {'glb': 'https://fixture-cdn.example/refine.glb'}}, {})
            self.assertEqual(self.submit_resume(server, 'refine')['status'], 'generated')

            write_request(self.root, 'meshy', 'rigging',
                          {'input_job': 'refine', 'humanoid': True, 'textured': True, 'face_count': 12000},
                          'assets/models/rig.glb')
            server.routes['POST', '/openapi/v1/rigging'] = (200, {'result': 'rig-1'}, {})
            server.routes['GET', '/openapi/v1/rigging/rig-1'] = (200, {'id': 'rig-1', 'status': 'SUCCEEDED',
                'result': {'rigged_character_glb_url': 'https://fixture-cdn.example/rig.glb'}}, {})
            self.assertEqual(self.submit_resume(server, 'rig')['status'], 'generated')

            write_request(self.root, 'meshy', 'animation', {'rig_job': 'rig', 'action_id': 42},
                          'assets/models/walk.glb')
            server.routes['GET', '/openapi/v1/animations/library?action_ids=42'] = (200, [
                {'action_id': 42, 'name': 'Walk', 'key': 'walk', 'category': 'move',
                 'sub_category': 'walk', 'preview_url': 'https://fixture-cdn.example/walk'}], {})
            server.routes['POST', '/openapi/v1/animations'] = (200, {'result': 'animation-1'}, {})
            server.routes['GET', '/openapi/v1/animations/animation-1'] = (200, {'id': 'animation-1', 'status': 'SUCCEEDED',
                'result': {'animation_glb_url': 'https://fixture-cdn.example/walk.glb'}}, {})
            self.assertEqual(self.submit_resume(server, 'animation')['status'], 'generated')
            before = sum(call[0] == 'POST' for call in server.calls)
            self.assertEqual(jobs.submit(self.root, self.state, 'request.json', 'animation', write=True,
                                         transport=server.transport())['status'], 'generated')
            self.assertEqual(sum(call[0] == 'POST' for call in server.calls), before)
            self.assertEqual(before, 4)

    def test_tripo_upload_generation_rig_check_rig_retarget_are_independent_jobs(self):
        from ccgs.assets import jobs
        (self.root / 'input.png').write_bytes(png())
        with Server() as server, patch.dict(os.environ, {'TRIPO_API_KEY': 'fixture-secret'}):
            write_request(self.root, 'tripo', 'upload-image', {'image': 'input.png'}, None)
            server.routes['POST', '/v3/files'] = (200, {'code': 0, 'data': {'file_token': 'file_private'}}, {})
            self.assertEqual(jobs.submit(self.root, self.state, 'request.json', 'upload', write=True,
                                         transport=server.transport())['status'], 'completed')

            write_request(self.root, 'tripo', 'image-to-model',
                          {'input_job': 'upload', 'model': 'v3.1-20260211', 'texture': True},
                          'assets/models/model.glb')
            server.routes['POST', '/v3/generation/image-to-model'] = (200, {'code': 0, 'data': {'task_id': 'task_model'}}, {})
            server.routes['GET', '/v3/tasks/task_model'] = (200, {'code': 0, 'data': {'task_id': 'task_model',
                'type': 'image_to_model', 'status': 'success', 'progress': 100, 'created_at': 1,
                'output': {'model_url': 'https://fixture-cdn.example/model.glb'}}}, {})
            self.assertEqual(self.submit_resume(server, 'model')['status'], 'generated')

            write_request(self.root, 'tripo', 'rig-check', {'input_job': 'model'},
                          'assets/data/rig-check.json', validation=True)
            server.routes['POST', '/v3/animations/rig-check'] = (200, {'code': 0, 'data': {'task_id': 'task_check'}}, {})
            server.routes['GET', '/v3/tasks/task_check'] = (200, {'code': 0, 'data': {'task_id': 'task_check',
                'type': 'rig_check', 'status': 'success', 'progress': 100, 'created_at': 1,
                'output': {'riggable': True, 'rig_type': 'biped'}}}, {})
            self.assertEqual(self.submit_resume(server, 'check')['status'], 'completed')
            self.assertEqual(jobs.collect(self.root, self.state, 'check', write=True,
                                          transport=server.transport())['status'], 'collected')
            self.assertEqual(json.loads((self.root / 'assets/data/rig-check.json').read_text()),
                             {'riggable': True, 'rig_type': 'biped', 'input_task_id': 'task_model'})

            write_request(self.root, 'tripo', 'rig', {'input_job': 'model', 'rig_check_job': 'check',
                'model': 'v1.0-20240301', 'rig_type': 'biped', 'spec': 'tripo', 'out_format': 'glb'},
                'assets/models/rig.glb')
            server.routes['POST', '/v3/animations/rig'] = (200, {'code': 0, 'data': {'task_id': 'task_rig'}}, {})
            server.routes['GET', '/v3/tasks/task_rig'] = (200, {'code': 0, 'data': {'task_id': 'task_rig',
                'type': 'rig', 'status': 'success', 'progress': 100, 'created_at': 1,
                'output': {'model_url': 'https://fixture-cdn.example/rig.glb'}}}, {})
            self.assertEqual(self.submit_resume(server, 'rig')['status'], 'generated')

            write_request(self.root, 'tripo', 'retarget', {'rig_job': 'rig',
                'animation': 'preset:biped:walk', 'out_format': 'glb'}, 'assets/models/walk.glb')
            server.routes['POST', '/v3/animations/retarget'] = (200, {'code': 0, 'data': {'task_id': 'task_walk'}}, {})
            server.routes['GET', '/v3/tasks/task_walk'] = (200, {'code': 0, 'data': {'task_id': 'task_walk',
                'type': 'retarget', 'status': 'success', 'progress': 100, 'created_at': 1,
                'output': {'model_url': 'https://fixture-cdn.example/walk.glb'}}}, {})
            self.assertEqual(self.submit_resume(server, 'walk')['status'], 'generated')
            self.assertEqual([call[1] for call in server.calls if call[0] == 'POST'], [
                '/v3/files', '/v3/generation/image-to-model', '/v3/animations/rig-check',
                '/v3/animations/rig', '/v3/animations/retarget'])

    def test_tripo_upload_result_persistence_crash_does_not_repeat_upload(self):
        from ccgs.assets import jobs
        (self.root / 'input.png').write_bytes(png())
        write_request(self.root, 'tripo', 'upload-image', {'image': 'input.png'}, None)
        with Server() as server, patch.dict(os.environ, {'TRIPO_API_KEY': 'fixture-secret'}):
            server.routes['POST', '/v3/files'] = (200, {'code': 0, 'data': {'file_token': 'file_private'}}, {})
            original = jobs.save_receipt
            def crash(root, state, operation_id, receipt):
                if receipt['status'] == 'completed':
                    raise SystemExit('after durable upload result')
                return original(root, state, operation_id, receipt)
            with patch.object(jobs, 'save_receipt', side_effect=crash):
                with self.assertRaises(SystemExit):
                    jobs.submit(self.root, self.state, 'request.json', 'upload', write=True,
                                transport=server.transport())
            self.assertEqual(jobs.submit(self.root, self.state, 'request.json', 'upload', write=True,
                                         transport=server.transport())['status'], 'completed')
            self.assertEqual(sum(call[1] == '/v3/files' for call in server.calls), 1)
            write_request(self.root, 'tripo', 'image-to-model',
                          {'input_job': 'upload', 'model': 'v3.1-20260211'},
                          'assets/models/recovered.glb')
            server.routes['POST', '/v3/generation/image-to-model'] = (
                200, {'code': 0, 'data': {'task_id': 'task_recovered'}}, {})
            self.assertEqual(jobs.submit(self.root, self.state, 'request.json', 'generation', write=True,
                                         transport=server.transport())['status'], 'pending')
            self.assertEqual([call[1] for call in server.calls if call[0] == 'POST'],
                             ['/v3/files', '/v3/generation/image-to-model'])

    def test_tripo_actual_upload_and_generation_response_loss_never_repeat_post(self):
        from ccgs.assets import jobs
        def dropped(handler):
            handler.connection.shutdown(socket.SHUT_RDWR)
            handler.connection.close()
        (self.root / 'input.png').write_bytes(png())
        with Server() as server, patch.dict(os.environ, {'TRIPO_API_KEY': 'fixture-secret'}):
            write_request(self.root, 'tripo', 'upload-image', {'image': 'input.png'}, None)
            server.routes['POST', '/v3/files'] = dropped
            self.assertEqual(jobs.submit(self.root, self.state, 'request.json', 'lost-upload', write=True,
                                         transport=server.transport())['status'], 'submission_unknown')
            self.assertEqual(jobs.submit(self.root, self.state, 'request.json', 'lost-upload', write=True,
                                         transport=server.transport())['status'], 'submission_unknown')
            self.assertEqual(sum(call[1] == '/v3/files' for call in server.calls), 1)

        # A separately recovered successful upload feeds one uncertain generation.
        other = Path(self.tmp.name, 'generation-case').resolve()
        other.mkdir(); state = other / '.ccgs-assets'; (other / 'input.png').write_bytes(png())
        with Server() as server, patch.dict(os.environ, {'TRIPO_API_KEY': 'fixture-secret'}):
            write_request(other, 'tripo', 'upload-image', {'image': 'input.png'}, None)
            server.routes['POST', '/v3/files'] = (200, {'code': 0, 'data': {'file_token': 'file_private'}}, {})
            self.assertEqual(jobs.submit(other, state, 'request.json', 'upload', write=True,
                                         transport=server.transport())['status'], 'completed')
            write_request(other, 'tripo', 'image-to-model',
                          {'input_job': 'upload', 'model': 'v3.1-20260211'}, 'assets/models/lost.glb')
            server.routes['POST', '/v3/generation/image-to-model'] = dropped
            self.assertEqual(jobs.submit(other, state, 'request.json', 'lost-generation', write=True,
                                         transport=server.transport())['status'], 'submission_unknown')
            self.assertEqual(jobs.submit(other, state, 'request.json', 'lost-generation', write=True,
                                         transport=server.transport())['status'], 'submission_unknown')
            self.assertEqual([call[1] for call in server.calls if call[0] == 'POST'],
                             ['/v3/files', '/v3/generation/image-to-model'])

    def test_public_prepare_rejects_meshy_local_dependency_contradictions_offline(self):
        from ccgs.assets import jobs
        from ccgs.assets.request import prepare_request
        (self.root / 'input.png').write_bytes(png())
        with Server() as server, patch.dict(os.environ, {
                'MESHY_API_KEY': 'fixture-secret', 'TRIPO_API_KEY': 'fixture-secret'}):
            write_request(self.root, 'meshy', 'image-to-3d',
                          {'image': 'input.png', 'ai_model': 'meshy-6', 'should_texture': False},
                          'assets/models/untextured.glb')
            server.routes['POST', '/openapi/v1/image-to-3d'] = (200, {'result': 'image-untextured'}, {})
            server.routes['GET', '/openapi/v1/image-to-3d/image-untextured'] = (200, {
                'id': 'image-untextured', 'status': 'SUCCEEDED',
                'model_urls': {'glb': 'https://fixture-cdn.example/untextured.glb'}}, {})
            self.submit_resume(server, 'untextured')

            write_request(self.root, 'meshy', 'text-to-3d-preview',
                          {'prompt': 'preview', 'ai_model': 'meshy-6'}, 'assets/models/preview-source.glb')
            server.routes['POST', '/openapi/v2/text-to-3d'] = (200, {'result': 'preview-source'}, {})
            server.routes['GET', '/openapi/v2/text-to-3d/preview-source'] = (200, {
                'id': 'preview-source', 'status': 'SUCCEEDED',
                'model_urls': {'glb': 'https://fixture-cdn.example/preview.glb'}}, {})
            self.submit_resume(server, 'preview-source')

            write_request(self.root, 'tripo', 'text-to-model',
                          {'prompt': 'other provider', 'model': 'v3.1-20260211'},
                          'assets/models/tripo-source.glb')
            server.routes['POST', '/v3/generation/text-to-model'] = (
                200, {'code': 0, 'data': {'task_id': 'task_tripo'}}, {})
            server.routes['GET', '/v3/tasks/task_tripo'] = (200, {'code': 0, 'data': {
                'task_id': 'task_tripo', 'type': 'text_to_model', 'status': 'success',
                'progress': 100, 'created_at': 1,
                'output': {'model_url': 'https://fixture-cdn.example/tripo.glb'}}}, {})
            self.submit_resume(server, 'tripo-source')

            for source, message in [('untextured', 'textured'), ('preview-source', 'ineligible'),
                                    ('tripo-source', 'ineligible')]:
                with self.subTest(source=source):
                    write_request(self.root, 'meshy', 'rigging', {
                        'input_job': source, 'humanoid': True, 'textured': True, 'face_count': 1000},
                        'assets/models/offline-rig.glb')
                    before_calls = len(server.calls); before_state = self.state_bytes()
                    with self.assertRaisesRegex(ValueError, message):
                        prepare_request(self.root, self.state, 'request.json')
                    self.assertEqual(len(server.calls), before_calls)
                    self.assertEqual(self.state_bytes(), before_state)

    def test_public_prepare_rejects_false_and_mismatched_tripo_rig_check_offline(self):
        from ccgs.assets import jobs
        from ccgs.assets.request import prepare_request
        with Server() as server, patch.dict(os.environ, {'TRIPO_API_KEY': 'fixture-secret'}):
            for suffix in ('a', 'b'):
                write_request(self.root, 'tripo', 'text-to-model',
                              {'prompt': suffix, 'model': 'v3.1-20260211'},
                              'assets/models/model-' + suffix + '.glb')
                server.routes['POST', '/v3/generation/text-to-model'] = (
                    200, {'code': 0, 'data': {'task_id': 'task_' + suffix}}, {})
                server.routes['GET', '/v3/tasks/task_' + suffix] = (200, {'code': 0, 'data': {
                    'task_id': 'task_' + suffix, 'type': 'text_to_model', 'status': 'success',
                    'progress': 100, 'created_at': 1,
                    'output': {'model_url': 'https://fixture-cdn.example/' + suffix + '.glb'}}}, {})
                self.submit_resume(server, 'model-' + suffix)

            for model, check_id, riggable in [('model-a', 'check-false', False),
                                               ('model-b', 'check-b', True)]:
                write_request(self.root, 'tripo', 'rig-check', {'input_job': model},
                              'assets/data/' + check_id + '.json', validation=True)
                server.routes['POST', '/v3/animations/rig-check'] = (
                    200, {'code': 0, 'data': {'task_id': 'task_' + check_id}}, {})
                server.routes['GET', '/v3/tasks/task_' + check_id] = (200, {'code': 0, 'data': {
                    'task_id': 'task_' + check_id, 'type': 'rig_check', 'status': 'success',
                    'progress': 100, 'created_at': 1,
                    'output': {'riggable': riggable, 'rig_type': 'biped'}}}, {})
                self.submit_resume(server, check_id)

            cases = [('model-a', 'check-false', 'riggable'), ('model-a', 'check-b', 'same_input')]
            for model, check, message in cases:
                with self.subTest(model=model, check=check):
                    write_request(self.root, 'tripo', 'rig', {
                        'input_job': model, 'rig_check_job': check, 'model': 'v1.0-20240301',
                        'rig_type': 'biped', 'spec': 'tripo', 'out_format': 'glb'},
                        'assets/models/offline-tripo-rig.glb')
                    before_calls = len(server.calls); before_state = self.state_bytes()
                    with self.assertRaisesRegex(ValueError, message):
                        prepare_request(self.root, self.state, 'request.json')
                    self.assertEqual(len(server.calls), before_calls)
                    self.assertEqual(self.state_bytes(), before_state)

    def test_tripo_collector_accepts_structural_glb_and_rejects_corrupt_download(self):
        from ccgs.assets import jobs
        with Server() as server, patch.dict(os.environ, {'TRIPO_API_KEY': 'fixture-secret'}):
            write_request(self.root, 'tripo', 'text-to-model',
                          {'prompt': 'Stone guardian', 'model': 'v3.1-20260211'},
                          'assets/models/valid.glb')
            server.routes['POST', '/v3/generation/text-to-model'] = (200, {'code': 0, 'data': {'task_id': 'task_valid'}}, {})
            server.routes['GET', '/v3/tasks/task_valid'] = (200, {'code': 0, 'data': {'task_id': 'task_valid',
                'type': 'text_to_model', 'status': 'success', 'progress': 100, 'created_at': 1,
                'output': {'model_url': 'https://fixture-cdn.example/valid.glb',
                           'preview_image': 'https://fixture-cdn.example/preview.png'}}}, {})
            server.routes['GET', '/valid.glb'] = (200, glb(), {})
            self.submit_resume(server, 'valid')
            self.assertEqual(jobs.collect(self.root, self.state, 'valid', write=True,
                                          transport=server.transport())['status'], 'collected')

            write_request(self.root, 'tripo', 'text-to-model',
                          {'prompt': 'Broken guardian', 'model': 'v3.1-20260211'},
                          'assets/models/corrupt.glb')
            server.routes['POST', '/v3/generation/text-to-model'] = (200, {'code': 0, 'data': {'task_id': 'task_corrupt'}}, {})
            server.routes['GET', '/v3/tasks/task_corrupt'] = (200, {'code': 0, 'data': {'task_id': 'task_corrupt',
                'type': 'text_to_model', 'status': 'success', 'progress': 100, 'created_at': 1,
                'output': {'model_url': 'https://fixture-cdn.example/corrupt.glb'}}}, {})
            server.routes['GET', '/corrupt.glb'] = (200, b'glTF-not-a-container', {})
            self.submit_resume(server, 'corrupt')
            with self.assertRaises(ValueError):
                jobs.collect(self.root, self.state, 'corrupt', write=True,
                             transport=server.transport())
            self.assertFalse((self.root / 'assets/models/corrupt.glb').exists())


if __name__ == '__main__':
    unittest.main()
