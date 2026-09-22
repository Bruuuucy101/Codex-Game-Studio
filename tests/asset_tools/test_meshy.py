import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fixtures import Server, png, request


def dependency(operation, task, *, data=None):
    return {
        'receipt': {'provider': 'meshy', 'operation': operation, 'task_id': task,
                    'status': 'generated', 'data_type': 'meshy.glb'},
        'result': {'data_type': 'meshy.glb', 'data': data or {}, 'status': 'generated'},
    }


class MeshyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def plan(self, operation, parameters, outputs=None):
        from ccgs.assets.meshy import Meshy
        from ccgs.assets.request import sha256
        normalized, images, _ = Meshy().prepare(self.root, operation, parameters)
        inputs = []
        for image in images:
            raw = (self.root / image).read_bytes()
            inputs.append({'path': image, 'kind': 'image', 'sha256': sha256(raw), 'size': len(raw)})
        return {'request': {'operation': operation, 'parameters': normalized,
                            'outputs': outputs if outputs is not None else [
                                {'key': 'model', 'path': 'assets/models/model.glb', 'format': 'glb'}]},
                'inputs': inputs, 'dependencies': []}

    def test_meshy_preview_uses_exact_v2_payload_and_status_shape(self):
        from ccgs.assets.meshy import Meshy
        adapter = Meshy()
        plan = self.plan('text-to-3d-preview',
                         {'prompt': 'Stone guardian', 'ai_model': 'meshy-6', 'pose_mode': 'a-pose'})
        with Server() as server, patch.dict(os.environ, {'MESHY_API_KEY': 'secret'}):
            server.routes['POST', '/openapi/v2/text-to-3d'] = (200, {'result': 'preview-1'}, {})
            server.routes['GET', '/openapi/v2/text-to-3d/preview-1'] = [
                (200, {'id': 'preview-1', 'status': 'IN_PROGRESS'}, {}),
                (200, {'id': 'preview-1', 'status': 'SUCCEEDED',
                       'model_urls': {'glb': 'https://fixture-cdn.example/preview.glb'}}, {})]
            submitted = adapter.submit(self.root, plan, {}, server.transport(), credential='secret', deadline=None)
            self.assertEqual((submitted.status, submitted.task_id), ('pending', 'preview-1'))
            self.assertEqual(json.loads(server.calls[0][3]), {
                'mode': 'preview', 'prompt': 'Stone guardian', 'ai_model': 'meshy-6',
                'target_formats': ['glb'], 'pose_mode': 'a-pose'})
            self.assertEqual(adapter.poll(plan, 'preview-1', server.transport(), credential='secret', deadline=None).status, 'pending')
            result = adapter.poll(plan, 'preview-1', server.transport(), credential='secret', deadline=None)
            self.assertEqual(result.artifacts['model'].url, 'https://fixture-cdn.example/preview.glb')

    def test_meshy_all_operation_payloads_and_dependency_eligibility(self):
        from ccgs.assets.meshy import Meshy
        cases = [
            ('text-to-3d-refine', {'preview_job': 'preview', 'enable_pbr': True, 'texture_prompt': 'weathered'},
             {'preview': dependency('text-to-3d-preview', 'preview-1', data={'ai_model': 'meshy-6'})},
             '/openapi/v2/text-to-3d', {'mode': 'refine', 'preview_task_id': 'preview-1',
                                      'target_formats': ['glb'], 'enable_pbr': True, 'texture_prompt': 'weathered'}),
            ('rigging', {'input_job': 'refine', 'humanoid': True, 'textured': True,
                         'face_count': 250000, 'height_meters': 1.8},
             {'refine': dependency('text-to-3d-refine', 'refine-1', data={'textured': True})},
             '/openapi/v1/rigging', {'input_task_id': 'refine-1', 'height_meters': 1.8}),
            ('animation', {'rig_job': 'rig', 'action_id': 42},
             {'rig': dependency('rigging', 'rig-1')},
             '/openapi/v1/animations', {'rig_task_id': 'rig-1', 'action_id': 42}),
            ('retexture', {'input_job': 'image', 'text_style_prompt': 'painted',
                           'ai_model': 'meshy-6', 'enable_pbr': False},
             {'image': dependency('image-to-3d', 'image-1')},
             '/openapi/v1/retexture', {'input_task_id': 'image-1', 'text_style_prompt': 'painted',
                                      'ai_model': 'meshy-6', 'target_formats': ['glb'], 'enable_pbr': False}),
            ('remesh', {'input_job': 'retexture', 'target_polycount': 12000},
             {'retexture': dependency('retexture', 'retexture-1')},
             '/openapi/v1/remesh', {'input_task_id': 'retexture-1', 'target_formats': ['glb'],
                                   'topology': 'triangle', 'target_polycount': 12000}),
        ]
        for operation, parameters, dependencies, route, body in cases:
            with self.subTest(operation=operation), Server() as server:
                adapter = Meshy()
                plan = self.plan(operation, parameters)
                source_route = adapter.task_route(dependencies[next(iter(dependencies))]['receipt']['operation'])
                source_task = dependencies[next(iter(dependencies))]['receipt']['task_id']
                server.routes['GET', source_route + '/' + source_task] = (200, {'id': source_task, 'status': 'SUCCEEDED'}, {})
                if operation == 'animation':
                    server.routes['GET', '/openapi/v1/animations/library?action_ids=42'] = (
                        200, [{'action_id': 42, 'name': 'Walk', 'key': 'walk', 'category': 'move',
                               'sub_category': 'walk', 'preview_url': 'https://fixture-cdn.example/walk'}], {})
                server.routes['POST', route] = (200, {'result': operation + '-task'}, {})
                evidence = adapter.validate_dependencies(plan, dependencies, server.transport(), credential='secret', deadline=None)
                result = adapter.submit(self.root, plan, dependencies, server.transport(), credential='secret', deadline=None)
                self.assertEqual(result.task_id, operation + '-task')
                self.assertEqual(json.loads(server.calls[-1][3]), body)
                self.assertEqual(result.evidence['dependencies'], evidence)

    def test_meshy_image_local_bytes_are_pinned_and_sent_as_png_data_uri(self):
        from ccgs.assets.meshy import Meshy
        (self.root / 'source.png').write_bytes(png())
        plan = self.plan('image-to-3d', {'image': 'source.png', 'ai_model': 'meshy-6', 'should_texture': True})
        with Server() as server:
            server.routes['POST', '/openapi/v1/image-to-3d'] = (200, {'result': 'image-1'}, {})
            Meshy().submit(self.root, plan, {}, server.transport(), credential='secret', deadline=None)
            body = json.loads(server.calls[0][3])
            self.assertEqual(set(body), {'image_url', 'ai_model', 'target_formats', 'should_texture'})
            self.assertTrue(body['image_url'].startswith('data:image/png;base64,'))

    def test_meshy_image_rechecks_the_pinned_local_bytes_before_post(self):
        from ccgs.assets.meshy import Meshy
        (self.root / 'source.png').write_bytes(png())
        plan = self.plan('image-to-3d', {'image': 'source.png', 'ai_model': 'meshy-6', 'should_texture': True})
        (self.root / 'source.png').write_bytes(png(32, 32))
        with Server() as server:
            with self.assertRaisesRegex(ValueError, 'source_changed'):
                Meshy().submit(self.root, plan, {}, server.transport(), credential='secret', deadline=None)
            self.assertEqual(server.calls, [])

    def test_meshy_rejects_unknown_models_invalid_actions_and_ineligible_rig_before_post(self):
        from ccgs.assets.meshy import Meshy
        bad = [
            ('text-to-3d-preview', {'prompt': 'x', 'ai_model': 'latest'}),
            ('image-to-3d', {'image': 'https://127.0.0.1/source.png', 'ai_model': 'meshy-6', 'should_texture': True}),
            ('animation', {'rig_job': 'rig', 'action_id': True}),
            ('rigging', {'input_job': 'refine', 'humanoid': False, 'textured': True, 'face_count': 100}),
            ('remesh', {'input_job': 'image', 'target_polycount': 99}),
        ]
        for operation, parameters in bad:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.plan(operation, parameters)
        plan = self.plan('animation', {'rig_job': 'rig', 'action_id': 999})
        deps = {'rig': dependency('rigging', 'rig-1')}
        with Server() as server:
            server.routes['GET', '/openapi/v1/rigging/rig-1'] = (200, {'id': 'rig-1', 'status': 'SUCCEEDED'}, {})
            server.routes['GET', '/openapi/v1/animations/library?action_ids=999'] = (200, [], {})
            with self.assertRaisesRegex(ValueError, 'action'):
                Meshy().validate_dependencies(plan, deps, server.transport(), credential='secret', deadline=None)
            self.assertFalse(any(call[0] == 'POST' for call in server.calls))
            server.routes['GET', '/openapi/v1/animations/library?action_ids=999'] = (
                200, [{'action_id': 999}], {})
            with self.assertRaisesRegex(ValueError, 'action'):
                Meshy().validate_dependencies(plan, deps, server.transport(), credential='secret', deadline=None)

    def test_meshy_terminal_statuses_and_exact_output_fields(self):
        from ccgs.assets.meshy import Meshy
        adapter = Meshy()
        for operation, field, key in [
            ('rigging', ('result', 'rigged_character_glb_url'), 'model'),
            ('animation', ('result', 'animation_glb_url'), 'model'),
            ('remesh', ('model_urls', 'glb'), 'model')]:
            plan = self.plan(operation,
                {'input_job': 'source', 'humanoid': True, 'textured': True, 'face_count': 1}
                if operation == 'rigging' else
                {'rig_job': 'source', 'action_id': 1} if operation == 'animation' else
                {'input_job': 'source', 'target_polycount': 100})
            with self.subTest(operation=operation), Server() as server:
                route = adapter.task_route(operation) + '/task-1'
                complete = {'id': 'task-1', 'status': 'SUCCEEDED', field[0]: {field[1]: 'https://fixture-cdn.example/a.glb'}}
                server.routes['GET', route] = (200, complete, {})
                self.assertEqual(adapter.poll(plan, 'task-1', server.transport(), credential='secret', deadline=None).artifacts[key].url,
                                 'https://fixture-cdn.example/a.glb')
                server.routes['GET', route] = (200, {'id': 'task-1', 'status': 'CANCELED'}, {})
                self.assertEqual(adapter.poll(plan, 'task-1', server.transport(), credential='secret', deadline=None).status, 'cancelled')
                server.routes['GET', route] = (200, {'id': 'task-1', 'status': 'MYSTERY'}, {})
                self.assertEqual(adapter.poll(plan, 'task-1', server.transport(), credential='secret', deadline=None).status,
                                 'unsupported_provider_result')


if __name__ == '__main__':
    unittest.main()
