import json
import os
from pathlib import Path
import tempfile
import unittest

from fixtures import Server, png, request


def dependency(operation, task, data_type='tripo.model', data=None):
    return {
        'receipt': {'provider': 'tripo', 'operation': operation, 'task_id': task,
                    'status': 'completed' if operation == 'upload-image' else 'generated',
                    'data_type': data_type},
        'result': {'status': 'completed' if operation in ('upload-image', 'rig-check') else 'generated',
                   'data_type': data_type, 'data': data or {}},
    }


class TripoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def plan(self, operation, parameters, outputs=None):
        from ccgs.assets.request import sha256
        from ccgs.assets.tripo import Tripo
        normalized, images, _ = Tripo().prepare(self.root, operation, parameters)
        inputs = []
        for image in images:
            raw = (self.root / image).read_bytes()
            inputs.append({'path': image, 'kind': 'image', 'sha256': sha256(raw), 'size': len(raw)})
        return {'request': {'operation': operation, 'parameters': normalized,
                            'outputs': outputs if outputs is not None else [
                                {'key': 'model', 'path': 'assets/models/model.glb', 'format': 'glb'}]},
                'inputs': inputs, 'dependencies': []}

    def test_tripo_upload_is_separate_multipart_completed_result(self):
        from ccgs.assets.tripo import Tripo
        (self.root / 'input.png').write_bytes(png())
        plan = self.plan('upload-image', {'image': 'input.png'}, outputs=[])
        with Server() as server:
            server.routes['POST', '/v3/files'] = (200, {'code': 0, 'data': {'file_token': 'file_private'}}, {})
            result = Tripo().submit(self.root, plan, {}, server.transport(), credential='secret', deadline=None)
            self.assertEqual((result.status, result.task_id, result.data_type), ('completed', None, 'tripo.upload'))
            self.assertEqual(result.data, {'file_token': 'file_private', 'sha256': plan['inputs'][0]['sha256'],
                                           'size': plan['inputs'][0]['size'], 'mime': 'image/png'})
            method, path, headers, body = server.calls[0]
            self.assertEqual((method, path), ('POST', '/v3/files'))
            self.assertIn('name="file"; filename="image.png"', body.decode('latin1'))
            self.assertTrue(headers['Authorization'].startswith('Bearer '))

    def test_tripo_upload_rechecks_pinned_bytes_and_public_image_url(self):
        from ccgs.assets.tripo import Tripo
        (self.root / 'input.png').write_bytes(png())
        plan = self.plan('upload-image', {'image': 'input.png'}, outputs=[])
        (self.root / 'input.png').write_bytes(png(32, 32))
        with Server() as server:
            with self.assertRaisesRegex(ValueError, 'source_changed'):
                Tripo().submit(self.root, plan, {}, server.transport(), credential='secret', deadline=None)
            self.assertEqual(server.calls, [])
        with self.assertRaises(ValueError):
            self.plan('image-to-model', {'input': 'https://127.0.0.1/image.png', 'model': 'v3.1-20260211'})

    def test_tripo_generation_routes_use_current_v3_input_and_exact_models(self):
        from ccgs.assets.tripo import Tripo
        cases = [
            ('text-to-model', {'prompt': 'Stone guardian', 'model': 'v3.1-20260211', 'texture': True, 'pbr': True}, {},
             '/v3/generation/text-to-model', {'prompt': 'Stone guardian', 'model': 'v3.1-20260211', 'texture': True, 'pbr': True}),
            ('image-to-model', {'input_job': 'upload', 'model': 'v3.1-20260211', 'texture': False, 'pbr': False},
             {'upload': dependency('upload-image', None, 'tripo.upload', {'file_token': 'file_1', 'sha256': 'a'*64,
                                                                         'size': 10, 'mime': 'image/png'})},
             '/v3/generation/image-to-model', {'input': 'file_1', 'model': 'v3.1-20260211', 'texture': False, 'pbr': False}),
            ('rig-check', {'input_job': 'model'}, {'model': dependency('text-to-model', 'task_model')},
             '/v3/animations/rig-check', {'input': 'task_model'}),
            ('rig', {'input_job': 'model', 'rig_check_job': 'check', 'model': 'v1.0-20240301',
                     'rig_type': 'biped', 'spec': 'mixamo', 'out_format': 'glb'},
             {'model': dependency('text-to-model', 'task_model'),
              'check': dependency('rig-check', 'task_check', 'tripo.rig-check',
                                  {'riggable': True, 'rig_type': 'biped', 'input_task_id': 'task_model'})},
             '/v3/animations/rig', {'input': 'task_model', 'model': 'v1.0-20240301', 'rig_type': 'biped',
                                    'spec': 'mixamo', 'out_format': 'glb'}),
            ('retarget', {'rig_job': 'rig', 'animation': 'preset:biped:walk', 'out_format': 'glb',
                          'bake_animation': True, 'export_with_geometry': True, 'animate_in_place': False},
             {'rig': dependency('rig', 'task_rig', data={'operation': 'rig', 'model': 'v1.0-20240301', 'rig_type': 'biped'})}, '/v3/animations/retarget',
             {'input': 'task_rig', 'animation': 'preset:biped:walk', 'out_format': 'glb',
              'bake_animation': True, 'export_with_geometry': True, 'animate_in_place': False}),
        ]
        for operation, parameters, deps, route, body in cases:
            with self.subTest(operation=operation), Server() as server:
                adapter = Tripo()
                outputs = [{'key': 'validation', 'path': 'assets/data/rig-check.json', 'format': 'json'}] if operation == 'rig-check' else None
                plan = self.plan(operation, parameters, outputs=outputs)
                for dep in deps.values():
                    if dep['receipt']['task_id'] and dep['receipt']['operation'] != 'rig-check':
                        task = dep['receipt']['task_id']
                        server.routes['GET', '/v3/tasks/' + task] = (200, {'code': 0, 'data': {'task_id': task, 'type': 'fixture', 'status': 'success', 'progress': 100, 'created_at': 1, 'output': {'model_url': 'https://fixture-cdn.example/a.glb'}}}, {})
                evidence = adapter.validate_dependencies(plan, deps, server.transport(), credential='secret', deadline=None)
                server.routes['POST', route] = (200, {'code': 0, 'data': {'task_id': 'task_new'}}, {})
                result = adapter.submit(self.root, plan, deps, server.transport(), credential='secret', deadline=None)
                self.assertEqual(result.task_id, 'task_new')
                self.assertEqual(json.loads(server.calls[-1][3]), body)
                self.assertEqual(result.evidence['dependencies'], evidence)

    def test_tripo_poll_maps_lifecycle_and_rig_check_typed_json(self):
        from ccgs.assets.tripo import Tripo
        adapter = Tripo()
        model_plan = self.plan('text-to-model', {'prompt': 'x', 'model': 'v3.1-20260211'})
        with Server() as server:
            route = '/v3/tasks/task_1'
            server.routes['GET', route] = (200, {'code': 0, 'data': {'task_id': 'task_1', 'type': 'text_to_model',
                'status': 'success', 'progress': 100, 'created_at': 1,
                'output': {'model_url': 'https://fixture-cdn.example/model.glb'}}}, {})
            result = adapter.poll(model_plan, 'task_1', server.transport(), credential='secret', deadline=None)
            self.assertEqual(result.artifacts['model'].url, 'https://fixture-cdn.example/model.glb')
            for remote, local in [('queued', 'pending'), ('running', 'pending'), ('failed', 'failed'),
                                  ('cancelled', 'cancelled'), ('expired', 'expired'), ('banned', 'banned')]:
                server.routes['GET', route] = (200, {'code': 0, 'data': {'task_id': 'task_1', 'type': 'x',
                    'status': remote, 'progress': 1, 'created_at': 1}}, {})
                self.assertEqual(adapter.poll(model_plan, 'task_1', server.transport(), credential='secret', deadline=None).status, local)
            server.routes['GET', route] = (200, {'code': 0, 'data': {'task_id': 'task_1', 'type': 'x',
                'status': 'mystery', 'progress': 1, 'created_at': 1}}, {})
            self.assertEqual(adapter.poll(model_plan, 'task_1', server.transport(), credential='secret', deadline=None).status,
                             'unsupported_provider_result')

        check_plan = self.plan('rig-check', {'input_job': 'model'}, outputs=[
            {'key': 'validation', 'path': 'assets/data/check.json', 'format': 'json'}])
        check_plan['dependencies'] = [{'operation': 'text-to-model', 'task_id': 'task_model'}]
        with Server() as server:
            server.routes['GET', '/v3/tasks/task_check'] = (200, {'code': 0, 'data': {'task_id': 'task_check',
                'type': 'rig_check', 'status': 'success', 'progress': 100, 'created_at': 1,
                'output': {'riggable': False, 'rig_type': 'unknown'}}}, {})
            result = adapter.poll(check_plan, 'task_check', server.transport(), credential='secret', deadline=None)
            self.assertEqual((result.status, result.data_type, result.artifacts), ('completed', 'tripo.rig-check', {}))
            self.assertEqual(result.data['riggable'], False)

    def test_tripo_rejects_old_payloads_models_actions_and_mismatched_rig_evidence(self):
        bad = [
            ('text-to-model', {'prompt': 'x', 'model': 'latest'}),
            ('text-to-model', {'prompt': 'x', 'model': 'v3.1-20260211', 'texture': False, 'pbr': True}),
            ('image-to-model', {'file': {'type': 'png', 'file_token': 'file_1'}, 'model': 'v3.1-20260211'}),
            ('rig', {'input_job': 'm', 'rig_check_job': 'c', 'model': 'v2.5', 'rig_type': 'biped', 'spec': 'tripo', 'out_format': 'glb'}),
            ('retarget', {'rig_job': 'r', 'animation': 'preset:biped:fly', 'out_format': 'glb'}),
        ]
        for operation, parameters in bad:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.plan(operation, parameters)

        from ccgs.assets.tripo import Tripo
        plan = self.plan('rig', {'input_job': 'model', 'rig_check_job': 'check', 'model': 'v1.0-20240301',
                                 'rig_type': 'biped', 'spec': 'tripo', 'out_format': 'glb'})
        deps = {'model': dependency('text-to-model', 'task_a'),
                'check': dependency('rig-check', 'task_c', 'tripo.rig-check',
                                    {'riggable': True, 'rig_type': 'biped', 'input_task_id': 'task_b'})}
        with Server() as server:
            with self.assertRaisesRegex(ValueError, 'same_input'):
                Tripo().validate_dependencies(plan, deps, server.transport(), credential='secret', deadline=None)
            self.assertEqual(server.calls, [])

    def test_tripo_http_200_error_envelope_never_becomes_a_task(self):
        from ccgs.assets.tripo import Tripo
        plan = self.plan('text-to-model', {'prompt': 'x', 'model': 'v3.1-20260211'})
        with Server() as server:
            server.routes['POST', '/v3/generation/text-to-model'] = (200, {'code': 2010, 'data': {}}, {})
            with self.assertRaisesRegex(ValueError, 'provider_error_envelope'):
                Tripo().submit(self.root, plan, {}, server.transport(), credential='secret', deadline=None)

    def test_tripo_private_data_and_task_shapes_are_strictly_typed(self):
        from ccgs.assets.tripo import Tripo
        adapter = Tripo()
        with self.assertRaisesRegex(ValueError, 'upload_data'):
            adapter.validate_data('upload-image', 'tripo.upload',
                                  {'file_token': 'file_1', 'sha256': 'z' * 64,
                                   'size': 10, 'mime': 'image/png'})
        plan = self.plan('text-to-model', {'prompt': 'x', 'model': 'v3.1-20260211'})
        with Server() as server:
            server.routes['GET', '/v3/tasks/task_1'] = (200, {'code': 0, 'data': {
                'task_id': 'task_1', 'type': 'text_to_model', 'status': 'success',
                'progress': '100', 'created_at': 1,
                'output': {'model_url': 'https://fixture-cdn.example/model.glb'}}}, {})
            self.assertEqual(adapter.poll(plan, 'task_1', server.transport(), credential='secret', deadline=None).status,
                             'unsupported_provider_result')


if __name__ == '__main__':
    unittest.main()
