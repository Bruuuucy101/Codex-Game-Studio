"""Credential-free local socket and CLI fixtures; no provider accounts."""
import base64
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools'))


def png(width=64, height=64):
    from PIL import Image
    stream = io.BytesIO()
    Image.new('RGBA', (width, height), (70, 20, 100, 255)).save(stream, 'PNG')
    return stream.getvalue()


def image_response(width=64, height=64):
    return {'image': {'type': 'base64', 'format': 'png', 'base64': base64.b64encode(png(width, height)).decode()}}


def request(root, operation='create-image-pixen', **changes):
    value = {'schema_version': 1, 'provider': 'pixellab', 'operation': operation,
             'asset_id': 'fixture', 'standalone': True, 'source_files': [],
             'parameters': {'description': 'A stone guardian', 'image_size': {'width': 64, 'height': 64}},
             'outputs': [{'key': 'image', 'path': 'assets/art/guardian.png', 'format': 'png', 'width': 64, 'height': 64}],
             'rights_note': 'Synthetic fixture; no live account evidence'}
    value.update(changes)
    path = root / 'request.json'
    path.write_text(json.dumps(value))
    return path


class Server:
    def __init__(self):
        self.routes = {}
        self.calls = []
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                self.reply()
            def do_POST(self):
                self.reply()
            def reply(self):
                body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                owner.calls.append((self.command, self.path, dict(self.headers), body))
                route = owner.routes.get((self.command, self.path), (404, {'detail': 'secret raw body'}, {}))
                if isinstance(route, list):
                    route = route.pop(0)
                if callable(route):
                    route(self)
                    return
                status, value, headers = route
                raw = value if isinstance(value, bytes) else json.dumps(value).encode()
                self.send_response(status)
                for k, v in headers.items():
                    self.send_header(k, v)
                if 'Content-Length' not in headers:
                    self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                try:
                    self.wfile.write(raw)
                except (BrokenPipeError, ConnectionResetError):
                    pass
        self.http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.http.daemon_threads = True
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.origin = 'http://127.0.0.1:%d' % self.http.server_port
    def __enter__(self):
        self.thread.start()
        return self
    def __exit__(self, *args):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()
    def transport(self, **kwargs):
        from ccgs.assets.http import Transport
        return Transport(origin_map={'https://api.pixellab.ai': self.origin,
                                     'https://openapi.tripo3d.ai': self.origin,
                                     'https://fixture-cdn.example': self.origin}, **kwargs)


def cli(root, *args, server=None, extra_env=None):
    env = {k: v for k, v in os.environ.items() if k not in ('PIXELLAB_SECRET', 'MESHY_API_KEY', 'TRIPO_API_KEY')}
    env['PYTHONPATH'] = str(REPO / 'tools')
    if extra_env:
        env.update(extra_env)
    if server:
        # Library-only injection in this test launcher, never an executable production option.
        code = ('from ccgs.assets.http import Transport; from ccgs.assets.cli import main; '
                'from pathlib import Path; import sys; '
                'sys.exit(main(Path(sys.argv[1]), sys.argv[2:], transport=Transport(origin_map='
                + repr({'https://api.pixellab.ai': server.origin, 'https://fixture-cdn.example': server.origin}) + ')))')
        command = [sys.executable, '-c', code, str(root), *args]
    else:
        command = [sys.executable, str(REPO / 'tools/ccgs_codex.py'), '--root', str(root), 'assets', *args]
    return subprocess.run(command, env=env, text=True, capture_output=True, timeout=15)


class TypedAdapter:
    """Test-only provider proves shared upload/dependency/JSON/multi-output mechanics."""
    credential_env='TRIPO_API_KEY'
    def prepare(self,root,operation,parameters):
        from ccgs.assets.request import object_fields,fail
        if operation=='upload-fixture':
            object_fields(parameters,('image',))
            from ccgs.assets.pixellab import input_image
            input_image(root,parameters['image'])
            return parameters,[parameters['image']],{}
        if operation=='generation-fixture':
            object_fields(parameters,('input_job',))
            return parameters,[],{'first':{'formats':['png'],'width':64,'height':64},'second':{'formats':['png'],'width':64,'height':64}}
        if operation=='validation-fixture':
            object_fields(parameters,())
            return parameters,[],{'validation':{'formats':['json']}}
        fail('unsupported_fixture_operation')
    def dependency_ids(self,parameters):
        return [parameters['input_job']] if 'input_job' in parameters else []
    def validate_dependencies(self,plan,dependencies,transport,*,credential,deadline):
        if dependencies:
            dependency=dependencies[plan['request']['parameters']['input_job']]
            if dependency['receipt']['operation']!='upload-fixture' or dependency['result']['data_type']!='fixture.upload':raise ValueError('ineligible_upload')
        return {}
    def submit(self,root,plan,dependencies,transport,*,credential,deadline):
        from ccgs.assets.jobs import Result,Artifact
        op=plan['request']['operation']
        if op=='upload-fixture':
            from ccgs.assets.request import read_file,IMAGE_LIMIT
            raw=read_file(root,plan['request']['parameters']['image'],IMAGE_LIMIT)
            value=transport.multipart('tripo','/v3/files',filename='image.png',content=raw,content_type='image/png',credential=credential,deadline=deadline)
            return Result('completed',data_type='fixture.upload',data=value['data'])
        if op=='validation-fixture':
            value=transport.json('tripo','POST','/v3/validate',body={},credential=credential,deadline=deadline)
            return Result('completed',data_type='fixture.validation',data=value['data'])
        dep=dependencies[plan['request']['parameters']['input_job']]
        transport.json('tripo','POST','/v3/generate',body={'input':dep['result']['data']['file_token']},credential=credential,deadline=deadline)
        return Result('generated',task_id='task-generation-fixture',data_type='fixture.images',data={},artifacts={
            'first':Artifact(url='https://fixture-cdn.example/first?signature=private-secret'),
            'second':Artifact(url='https://fixture-cdn.example/second?signature=private-secret')})
    def poll(self,plan,job,transport,*,credential,deadline):
        from ccgs.assets.jobs import Result,Artifact
        value=transport.json('tripo','GET','/v3/tasks/'+job,credential=credential,deadline=deadline)
        return Result('generated',task_id=job,data_type='fixture.images',data={},artifacts={key:Artifact(url=url) for key,url in value['urls'].items()})
    def validate_data(self,operation,data_type,data):
        if data_type=='fixture.upload' and set(data)=={'file_token'} and isinstance(data['file_token'],str):return
        if data_type=='fixture.images' and data=={}:return
        if data_type=='fixture.validation':return self.validate_json(operation,data)
        raise ValueError('invalid_fixture_data')
    def validate_json(self,operation,data):
        if set(data)!={'riggable','rig_type'} or type(data['riggable']) is not bool or not isinstance(data['rig_type'],str):raise ValueError('invalid_fixture_validation')
