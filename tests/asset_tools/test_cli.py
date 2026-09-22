import json
from pathlib import Path
import tempfile
import unittest
from fixtures import cli, request, Server, image_response


class CLIIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        request(self.root)

    def test_plan_valid_request_is_offline_and_creates_no_state(self):
        result = cli(self.root, 'plan', '--request', 'request.json')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout)['request']['operation'], 'create-image-pixen')
        self.assertFalse((self.root / '.ccgs-assets').exists())

    def test_submit_without_write_is_only_preview(self):
        result = cli(self.root, 'submit', '--request', 'request.json', '--id', 'guardian')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertFalse((self.root / '.ccgs-assets').exists())

    def test_real_cli_single_post_repeat_collect_and_readonly_status(self):
        with Server() as server:
            server.routes['POST', '/v2/create-image-pixen'] = (200, image_response(), {})
            args = ('submit', '--request', 'request.json', '--id', 'guardian', '--write')
            one = cli(self.root, *args, server=server, extra_env={'PIXELLAB_SECRET': 'fixture-secret'})
            self.assertEqual(one.returncode, 0, one.stderr + one.stdout)
            two = cli(self.root, *args, server=server, extra_env={'PIXELLAB_SECRET': 'fixture-secret'})
            self.assertEqual(two.returncode, 0, two.stderr + two.stdout)
            self.assertEqual(len(server.calls), 1)
            collected = cli(self.root, 'collect', '--id', 'guardian', '--write', server=server)
            self.assertEqual(collected.returncode, 0, collected.stderr + collected.stdout)
            self.assertTrue((self.root / 'assets/art/guardian.png').is_file())
            files = {p: p.read_bytes() for p in (self.root / '.ccgs-assets').rglob('*') if p.is_file()}
            state = cli(self.root, 'status', '--id', 'guardian', server=server)
            self.assertEqual(json.loads(state.stdout)['status'], 'collected')
            self.assertEqual(files, {p: p.read_bytes() for p in files})
            self.assertNotIn('fixture-secret', one.stdout + two.stdout + collected.stdout + state.stdout)

    def test_cli_arbitrary_origin_is_rejected(self):
        result = cli(self.root, 'plan', '--request', 'request.json', '--origin', 'http://127.0.0.1')
        self.assertNotEqual(result.returncode, 0)

    def test_cli_assets_help_exposes_available_commands(self):
        result=cli(self.root,'--help')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('ingest',result.stdout);self.assertIn('balance',result.stdout)

    def test_cli_conversion_declares_source_size_separately_from_collected_output(self):
        from fixtures import png
        from PIL import Image
        (self.root/'source.png').write_bytes(png(128,64))
        request(self.root,'image-to-pixelart',parameters={'image':'source.png','image_size':{'width':128,'height':64},'output_size':{'width':32,'height':32}},outputs=[{'key':'image','path':'assets/art/converted.png','format':'png','width':32,'height':32}])
        with Server() as server:
            server.routes['POST','/v2/image-to-pixelart']=(200,image_response(32,32),{})
            submitted=cli(self.root,'submit','--request','request.json','--id','conversion','--write',server=server,extra_env={'PIXELLAB_SECRET':'fixture-secret'})
            self.assertEqual(submitted.returncode,0,submitted.stdout+submitted.stderr)
            collected=cli(self.root,'collect','--id','conversion','--write',server=server)
            self.assertEqual(collected.returncode,0,collected.stdout+collected.stderr)
            with Image.open(self.root/'assets/art/converted.png') as image:self.assertEqual(image.size,(32,32))
            body=json.loads(server.calls[0][3]);self.assertEqual(body['image_size'],{'width':128,'height':64});self.assertEqual(body['output_size'],{'width':32,'height':32})
    def test_cli_concurrent_duplicate_submit_has_one_actual_post(self):
        from concurrent.futures import ThreadPoolExecutor
        import time
        with Server() as server:
            def slow_response(handler):
                time.sleep(.15)
                raw=json.dumps(image_response()).encode()
                handler.send_response(200);handler.send_header('Content-Length',str(len(raw)));handler.end_headers();handler.wfile.write(raw)
            server.routes['POST','/v2/create-image-pixen']=slow_response
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures=[pool.submit(cli,self.root,'submit','--request','request.json','--id','race','--write',server=server,extra_env={'PIXELLAB_SECRET':'fixture-secret'}) for _ in range(2)]
                results=[f.result() for f in futures]
            self.assertTrue(any(r.returncode==0 for r in results))
            self.assertEqual(len(server.calls),1)
            for r in results:
                if r.returncode:self.assertIn('locked',r.stdout)
