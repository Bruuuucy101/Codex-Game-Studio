import base64
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from fixtures import Server, png, request, image_response


class PixelLabTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.root=Path(self.tmp.name).resolve()
        (self.root/'image.png').write_bytes(png()); (self.root/'mask.png').write_bytes(png())
    def test_pixellab_six_operations_exact_wire_and_result_envelopes(self):
        from ccgs.assets.pixellab import PixelLab
        cases=[('create-image-pixen',{'description':'x','image_size':{'width':64,'height':64},'seed':-1},False),
               ('create-image-pixflux',{'description':'x','image_size':{'width':64,'height':64},'init_image':'image.png','init_image_strength':50},False),
               ('create-image-pixflux-background',{'description':'x','image_size':{'width':64,'height':64}},True),
               ('generate-ui-v2',{'description':'x','image_size':{'width':64,'height':64},'color_palette':'red'},True),
               ('image-to-pixelart',{'image':'image.png','image_size':{'width':64,'height':64},'output_size':{'width':32,'height':32}},False),
               ('inpaint-v3',{'description':'x','inpainting_image':'image.png','mask_image':'mask.png','crop_to_mask':False},True)]
        with Server() as server:
            adapter=PixelLab()
            for op,params,async_result in cases:
                with self.subTest(op=op):
                    normalized,paths,expected=adapter.prepare(self.root,op,params)
                    value={'background_job_id':'job-123','status':'processing'} if async_result else image_response()
                    server.routes['POST','/v2/'+op]=(202 if async_result else 200,value,{})
                    plan={'request':{'operation':op,'parameters':normalized},'inputs':[{'path':p,'sha256':hashlib.sha256((self.root/p).read_bytes()).hexdigest(),'size':(self.root/p).stat().st_size} for p in paths]}
                    result=adapter.submit(self.root,plan,{},server.transport(),credential='fixture-secret',deadline=None)
                    self.assertEqual(result.status,'pending' if async_result else 'generated')
                    body=json.loads(server.calls[-1][3])
                    self.assertNotIn('image.png',json.dumps(body))
                    if op=='inpaint-v3':
                        self.assertEqual(body['inpainting_image']['size'],{'width':64,'height':64})
                        self.assertEqual(body['mask_image']['image']['type'],'base64')
                        self.assertFalse(body['crop_to_mask'])
                    if op=='image-to-pixelart': self.assertEqual(expected['image']['width'],32)
    def test_pixellab_async_completed_failed_unknown_and_experimental_decoder(self):
        from ccgs.assets.pixellab import PixelLab
        with Server() as server:
            adapter=PixelLab()
            for op in ['create-image-pixflux-background','generate-ui-v2','inpaint-v3']:
                for status,response,want in [('processing',None,'pending'),('failed',None,'failed'),('completed',image_response(),'generated'),('completed',{'unrecognized':'https://x/a?secret=1'},'unsupported_provider_result')]:
                    server.routes['GET','/v2/background-jobs/job-123']=(200,{'id':'job-123','created_at':'2026-09-21T00:00:00Z','status':status,'last_response':response},{})
                    result=adapter.poll({'request':{'operation':op}},'job-123',server.transport(),credential='x',deadline=None)
                    self.assertEqual(result.status,want)
                if op!='create-image-pixflux-background':
                    server.routes['GET','/v2/background-jobs/job-123']=(200,{'id':'job-123','created_at':'now','status':'completed','last_response':{'images':[image_response()['image']]}},{})
                    result=adapter.poll({'request':{'operation':op}},'job-123',server.transport(),credential='x',deadline=None)
                    self.assertEqual(result.status,'generated')
                    self.assertEqual(result.data['decoder'],'experimental-single-image-v1')
    def test_pixellab_square_ui_no_crop_and_mask_dimensions_enforced(self):
        from ccgs.assets.pixellab import PixelLab
        adapter=PixelLab()
        for op,params in [('generate-ui-v2',{'description':'x','image_size':{'width':128,'height':64}}),
                          ('inpaint-v3',{'description':'x','inpainting_image':'image.png','mask_image':'mask.png','crop_to_mask':True})]:
            with self.assertRaises(ValueError): adapter.prepare(self.root,op,params)
        (self.root/'mask.png').write_bytes(png(32,32))
        with self.assertRaises(ValueError): adapter.prepare(self.root,'inpaint-v3',{'description':'x','inpainting_image':'image.png','mask_image':'mask.png'})
    def test_pixellab_presets_are_explicit_hashed_text_no_fanout(self):
        from ccgs.assets.request import prepare_request
        hashes=[]
        for preset in ['forest','desert','dungeon','city','space','underwater']:
            request(self.root,parameters={'description':'x','image_size':{'width':64,'height':64},'background_preset':preset})
            plan=prepare_request(self.root,self.root/'.ccgs-assets','request.json')
            self.assertIn(preset,plan['request']['parameters']['description'].lower())
            hashes.append(plan['request_sha256'])
        self.assertEqual(len(set(hashes)),6)
    def test_pixellab_balance_fractional_and_error_envelope(self):
        from ccgs.assets.pixellab import PixelLab
        with Server() as server:
            server.routes['GET','/v2/balance']=(200,{'credits':{'usd':1.25},'subscription':{'status':'active','generations':2.5,'total':100}},{})
            value=PixelLab().balance(server.transport(),credential='x')
            self.assertEqual(value['credits']['usd'],1.25)
            server.routes['GET','/v2/balance']=(200,{'error':'secret raw provider body'},{})
            with self.assertRaises(ValueError) as error: PixelLab().balance(server.transport(),credential='x')
            self.assertNotIn('secret raw',str(error.exception))

    def test_pixellab_wire_image_rechecks_pinned_bytes_before_post(self):
        from ccgs.assets.pixellab import PixelLab
        from ccgs.assets.request import prepare_request
        request(self.root,parameters={'description':'x','image_size':{'width':64,'height':64},'init_image':'image.png'},operation='create-image-pixflux')
        plan=prepare_request(self.root,self.root/'.ccgs-assets','request.json')
        (self.root/'image.png').write_bytes(png(32,32))
        with Server() as server:
            server.routes['POST','/v2/create-image-pixflux']=(200,image_response(),{})
            with self.assertRaises(ValueError):PixelLab().submit(self.root,plan,{},server.transport(),credential='x',deadline=None)
            self.assertEqual(server.calls,[])
