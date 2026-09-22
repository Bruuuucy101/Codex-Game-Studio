import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from fixtures import request, png


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.path = request(self.root)
    def prepare(self):
        from ccgs.assets.request import prepare_request
        return prepare_request(self.root, self.root / '.ccgs-assets', 'request.json')
    def change(self, **values):
        raw = json.loads(self.path.read_text()); raw.update(values)
        self.path.write_text(json.dumps(raw))
    def test_request_canonical_hash_changes_with_source_bytes(self):
        (self.root / 'source.md').write_text('source one')
        self.change(source_files=['source.md'])
        first = self.prepare()
        self.assertEqual(first['inputs'][0]['sha256'], hashlib.sha256(b'source one').hexdigest())
        (self.root / 'source.md').write_text('source two')
        self.assertNotEqual(first['request_sha256'], self.prepare()['request_sha256'])
        self.assertFalse((self.root / '.ccgs-assets').exists())
    def test_request_strict_json_rejects_duplicate_nonfinite_and_unknown_fields(self):
        good = self.path.read_text()
        bad = [good.replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'),
               good.replace('64', 'NaN', 1), good.replace('64', 'Infinity', 1)]
        for raw in bad:
            with self.subTest(raw=raw[:40]):
                self.path.write_text(raw)
                with self.assertRaises(ValueError): self.prepare()
        for key in ('api_key', 'authorization', 'host', 'endpoint', 'unexpected'):
            self.path.write_text(good); self.change(**{key: 'secret'})
            with self.assertRaises(ValueError): self.prepare()
    def test_request_dimensions_and_parameters_fail_before_submission(self):
        good = self.path.read_text()
        for params in ({'description':'x','image_size':{'width':True,'height':64}},
                       {'description':'x','image_size':{'width':64.0,'height':64}},
                       {'description':'x','image_size':{'width':20,'height':64}},
                       {'description':'x','image_size':{'width':768,'height':768}},
                       {'description':'x','image_size':{'width':64,'height':64},'enhance_prompt':True}):
            self.path.write_text(good); self.change(parameters=params)
            with self.assertRaises(ValueError): self.prepare()
    def test_request_canonical_mode_requires_asset_id_spec_membership_and_art_bible(self):
        self.change(standalone=False, asset_id='ASSET-101')
        with self.assertRaises(ValueError): self.prepare()
        spec=self.root/'design/assets/specs/guardian.md'; spec.parent.mkdir(parents=True)
        bible=self.root/'design/art/art-bible.md'; bible.parent.mkdir(parents=True)
        spec.write_text('# ASSET-102\nStatus: Needed'); bible.write_text('Angular style')
        self.change(source_files=['design/assets/specs/guardian.md','design/art/art-bible.md'])
        with self.assertRaises(ValueError): self.prepare()
        spec.write_text('# ASSET-101\nStatus: Needed')
        self.assertFalse(self.prepare()['request']['standalone'])
    def test_request_paths_and_output_schema_are_confined(self):
        good=self.path.read_text()
        for path in ('../out.png','/tmp/out.png','assets/../secret.png','.ccgs-assets/out.png','assets/.hidden/out.png','assets//out.png'):
            self.path.write_text(good)
            self.change(outputs=[{'key':'image','path':path,'format':'png','width':64,'height':64}])
            with self.assertRaises(ValueError): self.prepare()
        for changes in ({'key':'wrong'},{'format':'fbx'},{'width':32},{'extra':True}):
            self.path.write_text(good)
            out=json.loads(good)['outputs'][0]; out.update(changes); self.change(outputs=[out])
            with self.assertRaises(ValueError): self.prepare()
        self.path.write_text(good)
        (self.root/'assets').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError): self.prepare()
    def test_request_input_images_are_automatically_pinned(self):
        (self.root/'input.png').write_bytes(png(128,64))
        self.change(operation='image-to-pixelart',parameters={'image':'input.png','image_size':{'width':128,'height':64},'output_size':{'width':64,'height':64}})
        plan=self.prepare()
        self.assertEqual(plan['inputs'][0]['path'],'input.png')
        self.assertEqual(plan['inputs'][0]['kind'],'image')
        (self.root/'input.png').write_bytes(png(64,64))
        with self.assertRaises(ValueError): self.prepare()
    def test_request_byte_limits_and_source_symlinks(self):
        (self.root/'source.md').write_bytes(b'x'*(2*1024*1024+1)); self.change(source_files=['source.md'])
        with self.assertRaises(ValueError): self.prepare()
        (self.root/'source.md').unlink(); (self.root/'source.md').symlink_to(self.path)
        with self.assertRaises(ValueError): self.prepare()
        self.path.write_bytes(b' '*(4*1024*1024+1))
        with self.assertRaises(ValueError): self.prepare()

    def test_request_malformed_containers_and_duplicate_outputs_raise_validation(self):
        good=self.path.read_text()
        cases=[{'provider':{}},{'operation':[]},{'outputs':[{'key':'image','path':[],'format':'png','width':64,'height':64}]},
               {'source_files':['x']*33},{'standalone':1},{'schema_version':True}]
        for change in cases:
            self.path.write_text(good);self.change(**change)
            with self.assertRaises(ValueError):self.prepare()
    def test_request_absent_pillow_blocks_text_generation_before_post(self):
        import builtins
        from unittest.mock import patch
        original=builtins.__import__
        def without_pillow(name,*args,**kwargs):
            if name=='PIL' or name.startswith('PIL.'):raise ImportError('fixture missing Pillow')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=without_pillow):
            with self.assertRaisesRegex(ValueError,'optional_dependency_required'):self.prepare()
        self.assertFalse((self.root/'.ccgs-assets').exists())
    def test_request_private_url_redaction_preserves_full_hash(self):
        from ccgs.assets.request import redact
        self.change(parameters={'description':'Reference https://example.com/a?signature=private-secret#x','image_size':{'width':64,'height':64}})
        plan=self.prepare()
        self.assertNotIn('private-secret',json.dumps(redact(plan)))
        self.assertIn('private-secret',json.dumps(plan))
        old=plan['request_sha256']
        self.change(parameters={'description':'Reference https://example.com/a?signature=second-secret#x','image_size':{'width':64,'height':64}})
        self.assertNotEqual(old,self.prepare()['request_sha256'])

    def test_request_missing_safe_filesystem_primitives_fails_before_io(self):
        import os
        from unittest.mock import patch
        from ccgs.assets.request import check_root
        with patch.object(os,'O_NOFOLLOW',None):
            with self.assertRaisesRegex(ValueError,'filesystem_primitives_unavailable'):check_root(self.root)
