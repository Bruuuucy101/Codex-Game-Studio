"""Tripo V3 narrow REST contracts, researched 2026-09-21."""

from .artifacts import decode_image
from .jobs import Artifact, Result
from .request import HASH, IMAGE_LIMIT, fail, object_fields, read_file, sha256, string, task_id


ROUTES = {
    'text-to-model': '/v3/generation/text-to-model',
    'image-to-model': '/v3/generation/image-to-model',
    'rig-check': '/v3/animations/rig-check',
    'rig': '/v3/animations/rig',
    'retarget': '/v3/animations/retarget',
}
ACTIONS = {'preset:biped:idle', 'preset:biped:walk', 'preset:biped:run'}
RIG_TYPES = {'biped', 'quadruped', 'hexapod', 'octopod', 'avian', 'serpentine', 'aquatic'}
TERMINAL = {'failed': 'failed', 'cancelled': 'cancelled', 'expired': 'expired', 'banned': 'banned'}


def _boolean(value):
    if type(value) is not bool: fail('parameter_must_be_boolean')
    return value


def _web_input(value):
    if not isinstance(value, str) or len(value) > 4096:
        fail('invalid_tripo_input')
    from .http import Transport, TransportError
    try:
        Transport()._validate_url(value)
    except TransportError:
        fail('invalid_tripo_input')
    return value


class Tripo:
    credential_env = 'TRIPO_API_KEY'

    def __init__(self):
        self._dependency_evidence = {}

    def prepare(self, root, operation, parameters):
        if not isinstance(parameters, dict): fail('unsupported_or_missing_fields')
        p = dict(parameters); paths = []
        if operation == 'upload-image':
            object_fields(p, ('image',)); string(p['image'], 512)
            raw = read_file(root, p['image'], IMAGE_LIMIT); decode_image(raw); paths.append(p['image'])
            return p, paths, {}
        if operation == 'text-to-model':
            object_fields(p, ('prompt', 'model'), ('texture', 'pbr'))
            string(p['prompt'], 1024)
            self._generation_flags(p)
        elif operation == 'image-to-model':
            has_input, has_job = 'input' in p, 'input_job' in p
            required = ('model', 'input') if has_input and not has_job else ('model', 'input_job') if has_job and not has_input else ()
            if not required: fail('exactly_one_tripo_image_input_required')
            object_fields(p, required, ('texture', 'pbr'))
            if has_input: _web_input(p['input'])
            else: string(p['input_job'], 96)
            self._generation_flags(p)
        elif operation == 'rig-check':
            object_fields(p, ('input_job',)); string(p['input_job'], 96)
        elif operation == 'rig':
            object_fields(p, ('input_job', 'rig_check_job', 'model', 'rig_type', 'spec', 'out_format'))
            string(p['input_job'], 96); string(p['rig_check_job'], 96)
            if p['model'] != 'v1.0-20240301' or p['rig_type'] != 'biped' or p['spec'] not in ('tripo', 'mixamo') or p['out_format'] != 'glb':
                fail('unsupported_tripo_rig_contract')
        elif operation == 'retarget':
            object_fields(p, ('rig_job', 'animation', 'out_format'),
                          ('bake_animation', 'export_with_geometry', 'animate_in_place'))
            string(p['rig_job'], 96)
            if p['animation'] not in ACTIONS or p['out_format'] != 'glb': fail('unsupported_tripo_action')
            for key in ('bake_animation', 'export_with_geometry', 'animate_in_place'):
                if key in p: _boolean(p[key])
        else:
            fail('unsupported_tripo_operation')
        expected = {'validation': {'formats': ['json']}} if operation == 'rig-check' else {'model': {'formats': ['glb']}}
        return p, paths, expected

    def _generation_flags(self, p):
        if p['model'] != 'v3.1-20260211': fail('unsupported_tripo_model')
        for key in ('texture', 'pbr'):
            if key in p: _boolean(p[key])
        if p.get('pbr') is True and p.get('texture') is not True:
            fail('pbr_requires_texture')

    def dependency_ids(self, parameters):
        result = []
        for key in ('input_job', 'rig_check_job', 'rig_job'):
            if key in parameters and parameters[key] not in result: result.append(parameters[key])
        return result

    def _dependency(self, dependencies, name, operations, data_type='tripo.model'):
        dep = dependencies.get(name, {}); receipt = dep.get('receipt', {}); result = dep.get('result', {})
        if receipt.get('provider') != 'tripo' or receipt.get('operation') not in operations or receipt.get('status') not in ('completed', 'generated', 'collected') or result.get('data_type') != data_type:
            fail('ineligible_tripo_dependency')
        return dep

    def _query_success(self, dep, transport, credential, deadline):
        job = task_id(dep['receipt']['task_id'])
        value = transport.json('tripo', 'GET', '/v3/tasks/' + job, credential=credential, deadline=deadline)
        data = self._envelope(value)
        if data.get('task_id') != job or data.get('status') != 'success': fail('tripo_dependency_not_succeeded')
        return {'operation': dep['receipt']['operation'], 'task_id': job, 'status': 'success'}

    def validate_local_dependencies(self, operation, p, dependencies):
        """Validate persisted provider/operation/type facts without network or writes."""
        if operation == 'image-to-model' and 'input_job' in p:
            dep = self._dependency(dependencies, p['input_job'], {'upload-image'}, 'tripo.upload')
            self.validate_data('upload-image', 'tripo.upload', dep['result'].get('data', {}))
        elif operation == 'rig-check':
            self._dependency(dependencies, p['input_job'], {'text-to-model', 'image-to-model'})
        elif operation == 'rig':
            source = self._dependency(dependencies, p['input_job'], {'text-to-model', 'image-to-model'})
            check = self._dependency(dependencies, p['rig_check_job'], {'rig-check'}, 'tripo.rig-check')
            checked = check['result'].get('data', {})
            self.validate_data('rig-check', 'tripo.rig-check', checked)
            if checked['input_task_id'] != source['receipt'].get('task_id'):
                fail('rig_check_must_reference_same_input')
            if checked['riggable'] is not True or checked['rig_type'] != 'biped':
                fail('model_not_biped_riggable')
        elif operation == 'retarget':
            dep = self._dependency(dependencies, p['rig_job'], {'rig'})
            if dep['result'].get('data', {}).get('model') != 'v1.0-20240301':
                fail('retarget_requires_tripo_v1_rig')
        elif dependencies:
            fail('unexpected_tripo_dependency')

    def validate_dependencies(self, plan, dependencies, transport, *, credential, deadline):
        operation = plan['request']['operation']; p = plan['request']['parameters']; evidence = {}
        self.validate_local_dependencies(operation, p, dependencies)
        if operation == 'image-to-model' and 'input_job' in p:
            dep = self._dependency(dependencies, p['input_job'], {'upload-image'}, 'tripo.upload')
            data = dep['result'].get('data', {})
            evidence['upload'] = {'operation': 'upload-image', 'sha256': data['sha256'], 'size': data['size'], 'mime': data['mime']}
        elif operation == 'rig-check':
            dep = self._dependency(dependencies, p['input_job'], {'text-to-model', 'image-to-model'})
            evidence['source'] = self._query_success(dep, transport, credential, deadline)
        elif operation == 'rig':
            source = self._dependency(dependencies, p['input_job'], {'text-to-model', 'image-to-model'})
            check = self._dependency(dependencies, p['rig_check_job'], {'rig-check'}, 'tripo.rig-check')
            checked = check['result'].get('data', {})
            evidence['source'] = self._query_success(source, transport, credential, deadline)
            evidence['rig_check'] = {'task_id': check['receipt'].get('task_id'), 'riggable': True,
                                     'rig_type': 'biped', 'input_task_id': checked['input_task_id']}
        elif operation == 'retarget':
            dep = self._dependency(dependencies, p['rig_job'], {'rig'})
            evidence['rig'] = self._query_success(dep, transport, credential, deadline)
        self._dependency_evidence = evidence
        return evidence

    def _envelope(self, value):
        if not isinstance(value, dict) or type(value.get('code')) is not int or value['code'] != 0 or not isinstance(value.get('data'), dict):
            fail('tripo_provider_error_envelope')
        return value['data']

    def _task(self, value):
        data = self._envelope(value)
        if set(data) != {'task_id'}: fail('unsupported_provider_result')
        return task_id(data['task_id'])

    def _payload(self, plan, dependencies):
        operation = plan['request']['operation']; p = plan['request']['parameters']
        if operation == 'text-to-model':
            return dict(p)
        if operation == 'image-to-model':
            body = {key: p[key] for key in ('model', 'texture', 'pbr') if key in p}
            body['input'] = p['input'] if 'input' in p else dependencies[p['input_job']]['result']['data']['file_token']
            return body
        if operation == 'rig-check':
            return {'input': dependencies[p['input_job']]['receipt']['task_id']}
        if operation == 'rig':
            return {'input': dependencies[p['input_job']]['receipt']['task_id'],
                    'model': p['model'], 'rig_type': p['rig_type'], 'spec': p['spec'], 'out_format': p['out_format']}
        return {'input': dependencies[p['rig_job']]['receipt']['task_id'],
                **{key: value for key, value in p.items() if key != 'rig_job'}}

    def submit(self, root, plan, dependencies, transport, *, credential, deadline):
        operation = plan['request']['operation']
        if operation == 'upload-image':
            path = plan['request']['parameters']['image']; raw = read_file(root, path, IMAGE_LIMIT)
            info = decode_image(raw); mime = 'image/png' if info['format'] == 'png' else 'image/jpeg'
            pin = next((item for item in plan.get('inputs', []) if item['path'] == path), None)
            if pin is None or sha256(raw) != pin['sha256'] or len(raw) != pin['size']:
                fail('source_changed_since_plan')
            filename = 'image.png' if info['format'] == 'png' else 'image.jpg'
            value = transport.multipart('tripo', '/v3/files', filename=filename, content=raw,
                                        content_type=mime, credential=credential, deadline=deadline)
            data = self._envelope(value)
            if set(data) != {'file_token'} or not isinstance(data['file_token'], str) or not 1 <= len(data['file_token']) <= 512:
                fail('unsupported_provider_result')
            return Result('completed', data_type='tripo.upload',
                          data={'file_token': data['file_token'], 'sha256': sha256(raw), 'size': len(raw), 'mime': mime})
        value = transport.json('tripo', 'POST', ROUTES[operation], body=self._payload(plan, dependencies),
                               credential=credential, deadline=deadline)
        return Result('pending', self._task(value), evidence={'dependencies': self._dependency_evidence})

    def poll(self, plan, job, transport, *, credential, deadline):
        task_id(job); operation = plan['request']['operation']
        value = transport.json('tripo', 'GET', '/v3/tasks/' + job, credential=credential, deadline=deadline)
        try:
            data = self._envelope(value)
        except ValueError:
            return Result('unsupported_provider_result', job, evidence={'shape': 'invalid_envelope'})
        required = {'task_id', 'type', 'status', 'progress', 'created_at'}
        progress = data.get('progress')
        if (not required <= data.keys() or data.get('task_id') != job
                or not isinstance(data.get('type'), str) or not isinstance(data.get('status'), str)
                or isinstance(progress, bool) or type(progress) not in (int, float)
                or not 0 <= progress <= 100 or type(data.get('created_at')) is not int):
            return Result('unsupported_provider_result', job, evidence={'shape': 'invalid_task'})
        state = data['status']
        if state in ('queued', 'running'): return Result('pending', job)
        if state in TERMINAL: return Result(TERMINAL[state], job, evidence={'provider_status': state})
        if state != 'success': return Result('unsupported_provider_result', job, evidence={'provider_status': state})
        output = data.get('output')
        if not isinstance(output, dict): return Result('unsupported_provider_result', job, evidence={'missing': 'output'})
        if operation == 'rig-check':
            source = next((pin['task_id'] for pin in plan['dependencies'] if pin['operation'] in ('text-to-model', 'image-to-model')), None)
            check = {'riggable': output.get('riggable'), 'rig_type': output.get('rig_type'), 'input_task_id': source}
            try: self.validate_json(operation, check)
            except ValueError: return Result('unsupported_provider_result', job, evidence={'shape': 'invalid_rig_check'})
            return Result('completed', job, data_type='tripo.rig-check', data=check)
        url = output.get('model_url')
        if not isinstance(url, str): return Result('unsupported_provider_result', job, evidence={'missing': 'model_url'})
        result_data = {'operation': operation}
        if operation in ('text-to-model', 'image-to-model'): result_data['model'] = 'v3.1-20260211'
        if operation == 'rig': result_data.update(model='v1.0-20240301', rig_type='biped')
        if operation == 'retarget': result_data['animation'] = plan['request']['parameters']['animation']
        return Result('generated', job, data_type='tripo.model', data=result_data,
                      artifacts={'model': Artifact(url=url)})

    def validate_data(self, operation, data_type, data):
        if data_type is None and data == {}: return
        if operation == 'upload-image':
            if data_type != 'tripo.upload' or not isinstance(data, dict) or set(data) != {'file_token', 'sha256', 'size', 'mime'}:
                fail('invalid_tripo_upload_data')
            if (not isinstance(data['file_token'], str) or not 1 <= len(data['file_token']) <= 512
                    or any(ord(char) < 32 for char in data['file_token'])
                    or not isinstance(data['sha256'], str) or not HASH.fullmatch(data['sha256'])
                    or type(data['size']) is not int or data['size'] <= 0
                    or data['mime'] not in ('image/png', 'image/jpeg')):
                fail('invalid_tripo_upload_data')
            return
        if operation == 'rig-check':
            if data_type != 'tripo.rig-check': fail('invalid_tripo_rig_check_data')
            return self.validate_json(operation, data)
        if data_type != 'tripo.model' or not isinstance(data, dict) or data.get('operation') != operation:
            fail('invalid_tripo_model_data')
        allowed = {'operation', 'model', 'rig_type', 'animation'}
        if set(data) - allowed: fail('invalid_tripo_model_data')
        if operation in ('text-to-model', 'image-to-model') and data.get('model') != 'v3.1-20260211': fail('invalid_tripo_model_data')
        if operation == 'rig' and (data.get('model'), data.get('rig_type')) != ('v1.0-20240301', 'biped'): fail('invalid_tripo_model_data')
        if operation == 'retarget' and data.get('animation') not in ACTIONS: fail('invalid_tripo_model_data')

    def validate_json(self, operation, value):
        if operation != 'rig-check' or not isinstance(value, dict) or set(value) != {'riggable', 'rig_type', 'input_task_id'}:
            fail('invalid_tripo_rig_check_data')
        if type(value['riggable']) is not bool or not isinstance(value['rig_type'], str) or not 0 <= len(value['rig_type']) <= 100 or value['input_task_id'] is None:
            fail('invalid_tripo_rig_check_data')
        task_id(value['input_task_id'])
        if value['riggable'] and value['rig_type'] not in RIG_TYPES:
            fail('invalid_tripo_rig_check_data')
