"""Meshy V1/V2 narrow REST contracts, researched 2026-09-21."""
import base64
import binascii
import math

from .jobs import Artifact, Result
from .request import IMAGE_LIMIT, fail, integer, object_fields, sha256, string, task_id


ROUTES = {
    'text-to-3d-preview': '/openapi/v2/text-to-3d',
    'text-to-3d-refine': '/openapi/v2/text-to-3d',
    'image-to-3d': '/openapi/v1/image-to-3d',
    'rigging': '/openapi/v1/rigging',
    'animation': '/openapi/v1/animations',
    'retexture': '/openapi/v1/retexture',
    'remesh': '/openapi/v1/remesh',
}
PENDING = {'PENDING', 'IN_PROGRESS'}
TERMINAL = {'FAILED': 'failed', 'CANCELED': 'cancelled'}


def _boolean(value):
    if type(value) is not bool:
        fail('parameter_must_be_boolean')
    return value


def _positive_number(value):
    if isinstance(value, bool) or type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        fail('invalid_positive_number')
    return value


def _image_reference(root, value):
    """Validate an HTTPS/data URI or a decoded project-local image path."""
    from .artifacts import decode_image
    from .request import IMAGE_LIMIT, read_file
    if not isinstance(value, str):
        fail('invalid_image_input')
    if value.startswith('https://'):
        from .http import Transport, TransportError
        try:
            Transport()._validate_url(value)
        except TransportError:
            fail('invalid_image_url')
        return value, None, None
    for prefix, format_name in (('data:image/png;base64,', 'png'),
                                ('data:image/jpeg;base64,', 'jpeg')):
        if value.startswith(prefix):
            try:
                raw = base64.b64decode(value[len(prefix):], validate=True)
            except (ValueError, binascii.Error):
                fail('invalid_image_data_uri')
            if not raw or len(raw) > IMAGE_LIMIT or decode_image(raw)['format'] != format_name:
                fail('invalid_image_data_uri')
            return value, None, raw
    raw = read_file(root, value, IMAGE_LIMIT)
    info = decode_image(raw)
    mime = 'image/png' if info['format'] == 'png' else 'image/jpeg'
    return 'data:' + mime + ';base64,' + base64.b64encode(raw).decode(), value, raw


class Meshy:
    credential_env = 'MESHY_API_KEY'

    def __init__(self):
        self._dependency_evidence = {}

    def task_route(self, operation):
        try:
            return ROUTES[operation]
        except KeyError:
            fail('unsupported_meshy_operation')

    def prepare(self, root, operation, parameters):
        if operation not in ROUTES:
            fail('unsupported_meshy_operation')
        result = dict(parameters) if isinstance(parameters, dict) else parameters
        paths = []
        if operation == 'text-to-3d-preview':
            object_fields(result, ('prompt', 'ai_model'), ('pose_mode',))
            string(result['prompt'], 800)
            if result['ai_model'] != 'meshy-6': fail('unsupported_meshy_model')
            if 'pose_mode' in result and result['pose_mode'] not in ('a-pose', 't-pose', ''):
                fail('unsupported_pose_mode')
        elif operation == 'text-to-3d-refine':
            object_fields(result, ('preview_job',), ('enable_pbr', 'texture_prompt'))
            string(result['preview_job'], 96)
            if 'enable_pbr' in result: _boolean(result['enable_pbr'])
            if 'texture_prompt' in result: string(result['texture_prompt'], 800)
        elif operation == 'image-to-3d':
            object_fields(result, ('image', 'ai_model', 'should_texture'), ('enable_pbr',))
            if result['ai_model'] != 'meshy-6': fail('unsupported_meshy_model')
            _boolean(result['should_texture'])
            if 'enable_pbr' in result:
                _boolean(result['enable_pbr'])
                if result['enable_pbr'] and not result['should_texture']:
                    fail('pbr_requires_texture')
            _, path, _ = _image_reference(root, result['image'])
            if path is not None: paths.append(path)
        elif operation == 'rigging':
            object_fields(result, ('input_job', 'humanoid', 'textured', 'face_count'), ('height_meters',))
            string(result['input_job'], 96)
            if result['humanoid'] is not True or result['textured'] is not True:
                fail('rigging_requires_inspected_textured_humanoid')
            integer(result['face_count'], 1, 300000)
            if 'height_meters' in result: _positive_number(result['height_meters'])
        elif operation == 'animation':
            object_fields(result, ('rig_job', 'action_id'))
            string(result['rig_job'], 96)
            integer(result['action_id'], 0, 2**31 - 1)
        elif operation == 'retexture':
            object_fields(result, ('input_job', 'text_style_prompt', 'ai_model'), ('enable_pbr',))
            string(result['input_job'], 96); string(result['text_style_prompt'], 800)
            if result['ai_model'] != 'meshy-6': fail('unsupported_meshy_model')
            if 'enable_pbr' in result: _boolean(result['enable_pbr'])
        else:
            object_fields(result, ('input_job', 'target_polycount'))
            string(result['input_job'], 96); integer(result['target_polycount'], 100, 300000)
        return result, paths, {'model': {'formats': ['glb']}}

    def dependency_ids(self, parameters):
        for key in ('preview_job', 'input_job', 'rig_job'):
            if key in parameters:
                return [parameters[key]]
        return []

    def _source(self, dependency, allowed):
        receipt = dependency.get('receipt', {})
        result = dependency.get('result', {})
        if receipt.get('provider') != 'meshy' or receipt.get('operation') not in allowed or not receipt.get('task_id'):
            fail('ineligible_meshy_dependency')
        if receipt.get('status') not in ('generated', 'collected') or result.get('data_type') != 'meshy.glb':
            fail('ineligible_meshy_dependency')
        return receipt

    def _remote_success(self, receipt, transport, credential, deadline):
        task = task_id(receipt['task_id'])
        value = transport.json('meshy', 'GET', self.task_route(receipt['operation']) + '/' + task,
                               credential=credential, deadline=deadline)
        if not isinstance(value, dict) or value.get('status') != 'SUCCEEDED' or ('id' in value and value['id'] != task):
            fail('mesh_dependency_not_succeeded')
        return {'operation': receipt['operation'], 'task_id': task, 'status': 'SUCCEEDED'}

    def validate_local_dependencies(self, operation, parameters, dependencies):
        """Validate only persisted local evidence; preparation calls this offline."""
        if not dependencies:
            if operation in ('text-to-3d-preview', 'image-to-3d'):
                return
            fail('missing_meshy_dependency')
        if operation == 'text-to-3d-refine':
            key = parameters['preview_job']
            self._source(dependencies[key], {'text-to-3d-preview'})
            if dependencies[key]['result'].get('data', {}).get('ai_model') != 'meshy-6':
                fail('refine_preview_model_mismatch')
        elif operation == 'rigging':
            key = parameters['input_job']
            self._source(dependencies[key], {'text-to-3d-refine', 'image-to-3d', 'retexture'})
            if dependencies[key]['result'].get('data', {}).get('textured') is not True:
                fail('rigging_requires_recorded_textured_source')
        elif operation == 'animation':
            key = parameters['rig_job']
            self._source(dependencies[key], {'rigging'})
        elif operation == 'retexture':
            key = parameters['input_job']
            self._source(dependencies[key], {'text-to-3d-preview', 'text-to-3d-refine', 'image-to-3d', 'remesh'})
        elif operation == 'remesh':
            key = parameters['input_job']
            self._source(dependencies[key], {'text-to-3d-preview', 'text-to-3d-refine', 'image-to-3d', 'retexture'})
        else:
            fail('unexpected_meshy_dependency')

    def validate_dependencies(self, plan, dependencies, transport, *, credential, deadline):
        operation = plan['request']['operation']; parameters = plan['request']['parameters']
        if not dependencies:
            self._dependency_evidence = {}
            return {}
        self.validate_local_dependencies(operation, parameters, dependencies)
        key = parameters.get('preview_job', parameters.get('input_job', parameters.get('rig_job')))
        receipt = dependencies[key]['receipt']
        evidence = {'source': self._remote_success(receipt, transport, credential, deadline)}
        if operation == 'text-to-3d-refine':
            evidence['model'] = {'ai_model': 'meshy-6'}
        if operation == 'rigging':
            evidence['inspection'] = {key: parameters[key] for key in ('humanoid', 'textured', 'face_count')}
        if operation == 'animation':
            action = parameters['action_id']
            library = transport.json('meshy', 'GET', '/openapi/v1/animations/library?action_ids=' + str(action),
                                     credential=credential, deadline=deadline)
            required = {'action_id', 'name', 'key', 'category', 'sub_category', 'preview_url'}
            if not isinstance(library, list):
                fail('meshy_action_unavailable')
            selected = None
            from .http import Transport, TransportError
            for item in library:
                if not isinstance(item, dict) or not required <= item.keys() or type(item['action_id']) is not int:
                    fail('meshy_action_unavailable')
                for field in ('name', 'key', 'category', 'sub_category'):
                    string(item[field], 200)
                try:
                    Transport()._validate_url(item['preview_url'])
                except TransportError:
                    fail('meshy_action_unavailable')
                if item['action_id'] == action:
                    selected = item
            if selected is None:
                fail('meshy_action_unavailable')
            evidence['action'] = {field: selected[field] for field in
                                  ('action_id', 'name', 'key', 'category', 'sub_category')}
        self._dependency_evidence = evidence
        return evidence

    def _payload(self, root, plan, dependencies):
        operation = plan['request']['operation']; p = plan['request']['parameters']
        if operation == 'text-to-3d-preview':
            body = {'mode': 'preview', 'prompt': p['prompt'], 'ai_model': 'meshy-6', 'target_formats': ['glb']}
            if 'pose_mode' in p: body['pose_mode'] = p['pose_mode']
            return body
        if operation == 'text-to-3d-refine':
            body = {'mode': 'refine', 'preview_task_id': dependencies[p['preview_job']]['receipt']['task_id'],
                    'target_formats': ['glb']}
            for key in ('enable_pbr', 'texture_prompt'):
                if key in p: body[key] = p[key]
            return body
        if operation == 'image-to-3d':
            image, path, raw = _image_reference(root, p['image'])
            if path is not None:
                pin = next((item for item in plan.get('inputs', []) if item['path'] == path), None)
                if pin is None or sha256(raw) != pin['sha256'] or len(raw) != pin['size']:
                    fail('source_changed_since_plan')
            body = {'image_url': image, 'ai_model': 'meshy-6', 'target_formats': ['glb'],
                    'should_texture': p['should_texture']}
            if 'enable_pbr' in p: body['enable_pbr'] = p['enable_pbr']
            return body
        source_key = p.get('input_job', p.get('rig_job'))
        source_task = dependencies[source_key]['receipt']['task_id']
        if operation == 'rigging':
            body = {'input_task_id': source_task}
            if 'height_meters' in p: body['height_meters'] = p['height_meters']
            return body
        if operation == 'animation':
            return {'rig_task_id': source_task, 'action_id': p['action_id']}
        if operation == 'retexture':
            body = {'input_task_id': source_task, 'text_style_prompt': p['text_style_prompt'],
                    'ai_model': 'meshy-6', 'target_formats': ['glb']}
            if 'enable_pbr' in p: body['enable_pbr'] = p['enable_pbr']
            return body
        return {'input_task_id': source_task, 'target_formats': ['glb'], 'topology': 'triangle',
                'target_polycount': p['target_polycount']}

    def submit(self, root, plan, dependencies, transport, *, credential, deadline):
        operation = plan['request']['operation']
        value = transport.json('meshy', 'POST', self.task_route(operation),
                               body=self._payload(root, plan, dependencies), credential=credential, deadline=deadline)
        if not isinstance(value, dict) or set(value) != {'result'}:
            fail('unsupported_provider_result')
        job = task_id(value['result'])
        return Result('pending', job, evidence={'dependencies': self._dependency_evidence})

    def poll(self, plan, job, transport, *, credential, deadline):
        operation = plan['request']['operation']; task_id(job)
        value = transport.json('meshy', 'GET', self.task_route(operation) + '/' + job,
                               credential=credential, deadline=deadline)
        if not isinstance(value, dict) or ('id' in value and value['id'] != job) or not isinstance(value.get('status'), str):
            return Result('unsupported_provider_result', job, evidence={'shape': 'unrecognized'})
        state = value['status']
        if state in PENDING: return Result('pending', job)
        if state in TERMINAL: return Result(TERMINAL[state], job, evidence={'provider_status': state})
        if state != 'SUCCEEDED': return Result('unsupported_provider_result', job, evidence={'provider_status': state})
        try:
            if operation == 'rigging': url = value['result']['rigged_character_glb_url']
            elif operation == 'animation': url = value['result']['animation_glb_url']
            else: url = value['model_urls']['glb']
            if not isinstance(url, str): fail('unsupported_provider_result')
        except (KeyError, TypeError):
            return Result('unsupported_provider_result', job, evidence={'provider_status': state, 'missing': 'documented_glb'})
        data = {'operation': operation}
        if operation in ('text-to-3d-preview', 'image-to-3d', 'retexture'):
            data['ai_model'] = 'meshy-6'
        if operation in ('text-to-3d-refine', 'image-to-3d', 'retexture'):
            data['textured'] = operation != 'image-to-3d' or plan['request']['parameters']['should_texture']
        return Result('generated', job, data_type='meshy.glb', data=data,
                      artifacts={'model': Artifact(url=url)})

    def validate_data(self, operation, data_type, data):
        if data_type is None and data == {}: return
        if data_type != 'meshy.glb' or not isinstance(data, dict) or data.get('operation') != operation:
            fail('invalid_meshy_result_data')
        allowed = {'operation', 'ai_model', 'textured'}
        if set(data) - allowed or ('ai_model' in data and data['ai_model'] != 'meshy-6') or ('textured' in data and type(data['textured']) is not bool):
            fail('invalid_meshy_result_data')

    def validate_json(self, operation, value):
        fail('meshy_has_no_collectable_json_operation')
