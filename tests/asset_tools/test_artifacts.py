import json
from pathlib import Path
import struct
import tempfile
import unittest
from fixtures import png


def glb(doc=None, binary=b'\0\0\0\0'):
    doc = doc or {'asset':{'version':'2.0'},'buffers':[{'byteLength':4}], 'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':4}]}
    raw=json.dumps(doc).encode(); raw+=b' '*((-len(raw))%4)
    chunks=struct.pack('<II',len(raw),0x4e4f534a)+raw
    if binary is not None: chunks+=struct.pack('<II',len(binary),0x004e4942)+binary
    return struct.pack('<4sII',b'glTF',2,12+len(chunks))+chunks


class ArtifactTests(unittest.TestCase):
    def test_artifact_image_fully_decodes_and_matches_expected_content(self):
        from ccgs.assets.artifacts import validate_content
        self.assertEqual(validate_content(png(),{'format':'png','width':64,'height':64})['width'],64)
        for data, expected in [(png()[:50],{'format':'png'}),(png(),{'format':'jpeg'}),(png(),{'format':'png','width':32,'height':64})]:
            with self.assertRaises(ValueError): validate_content(data,expected)
    def test_artifact_glb_checks_bounds_version_and_external_uris(self):
        from ccgs.assets.artifacts import validate_content
        self.assertEqual(validate_content(glb(),{'format':'glb'})['format'],'glb')
        bad=[glb()[:-1],glb({'asset':{'version':'1.0'}}),glb({'asset':{'version':'2.0'},'buffers':[{'byteLength':500}]}),
             glb({'asset':{'version':'2.0'},'buffers':[{'byteLength':4,'uri':'https://example.com/a'}]}),
             glb({'asset':{'version':'2.0'},'buffers':[{'byteLength':4}],'bufferViews':[{'buffer':0,'byteLength':8}]})]
        for data in bad:
            with self.assertRaises(ValueError): validate_content(data,{'format':'glb'})

    def test_artifact_glb_accessor_cannot_exceed_referenced_buffer_view(self):
        from ccgs.assets.artifacts import validate_content
        doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':4}],
             'bufferViews':[{'buffer':0,'byteLength':4}],
             'accessors':[{'bufferView':0,'componentType':5126,'count':2,'type':'SCALAR'}]}
        with self.assertRaisesRegex(ValueError,'accessor'):
            validate_content(glb(doc),{'format':'glb'})
    def test_artifact_alternate_suffix_symlink_fails_preflight(self):
        from ccgs.assets.artifacts import preflight
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); (root/'assets/art').mkdir(parents=True)
            (root/'assets/art/out.jpg').symlink_to(root/'elsewhere')
            with self.assertRaisesRegex(ValueError,'symlink'):
                preflight(root,[{'path':'assets/art/out.png'}])

    def test_artifact_jpeg_decodes_fully_and_rejects_truncation(self):
        import io
        from PIL import Image
        from ccgs.assets.artifacts import validate_content
        stream=io.BytesIO();Image.new('RGB',(32,64),(20,30,40)).save(stream,'JPEG')
        raw=stream.getvalue()
        self.assertEqual(validate_content(raw,{'format':'jpeg','width':32,'height':64})['format'],'jpeg')
        with self.assertRaises(ValueError):validate_content(raw[:40],{'format':'jpeg'})

    def test_artifact_glb_rejects_invalid_explicit_stride(self):
        from ccgs.assets.artifacts import validate_content
        for stride in (1,2,3,5,6,255):
            with self.subTest(stride=stride):
                doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':16}],
                     'bufferViews':[{'buffer':0,'byteLength':16,'byteStride':stride}],
                     'accessors':[{'bufferView':0,'componentType':5121,'count':2,'type':'SCALAR'}]}
                with self.assertRaises(ValueError):
                    validate_content(glb(doc,binary=b'\0'*16),{'format':'glb'})

    def test_artifact_glb_rejects_unaligned_effective_accessor_offsets(self):
        from ccgs.assets.artifacts import validate_content
        for offset,component,shape in ((1,5123,'SCALAR'),(2,5126,'SCALAR'),(1,5121,'MAT2')):
            with self.subTest(offset=offset,component=component,shape=shape):
                doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':16}],
                     'bufferViews':[{'buffer':0,'byteOffset':offset,'byteLength':12}],
                     'accessors':[{'bufferView':0,'componentType':component,'count':1,'type':shape}]}
                with self.assertRaises(ValueError):
                    validate_content(glb(doc,binary=b'\0'*16),{'format':'glb'})

    def test_artifact_glb_keeps_valid_implicit_and_explicit_layouts(self):
        from ccgs.assets.artifacts import validate_content
        for view in ({'buffer':0,'byteLength':16}, {'buffer':0,'byteLength':16,'byteStride':4}):
            with self.subTest(view=view):
                doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':16}],
                     'bufferViews':[view],
                     'accessors':[{'bufferView':0,'componentType':5121,'count':4,'type':'SCALAR'}]}
                self.assertEqual(validate_content(glb(doc,binary=b'\0'*16),{'format':'glb'})['format'],'glb')

    def test_artifact_rollback_compatibility_does_not_unlink_after_proof_edit(self):
        from unittest.mock import patch
        from ccgs.assets import artifacts
        from ccgs.assets.request import sha256
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            target=root/'assets/art/native.png'
            target.parent.mkdir(parents=True)
            stage=root/'stage.bin'
            stage.write_bytes(png())
            target.hardlink_to(stage)
            original=artifacts.prove_owned
            def edit_after_proof(*args,**kwargs):
                valid=original(*args,**kwargs)
                target.write_bytes(b'artist edit after ownership proof')
                return valid
            with patch.object(artifacts,'prove_owned',side_effect=edit_after_proof):
                artifacts.rollback_owned(root,'assets/art/native.png',stage,sha256(png()))
            self.assertTrue(target.is_file(), 'no proof may authorize later automatic unlink')
            self.assertIn(target.read_bytes(),(png(),b'artist edit after ownership proof'))
