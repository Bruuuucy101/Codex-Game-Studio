"""Bounded content validation and inode-proven create-only publication."""
import io
import os
from pathlib import Path
import struct
import warnings
from .request import (ARTIFACT_LIMIT, checked_path, fail, integer, parent_fd,
                      read_file, sha256, strict_json)


def require_pillow():
    try:
        from PIL import Image
        return Image
    except ImportError:
        fail('optional_dependency_required: install requirements-assets.txt in a project virtual environment')


def decode_image(raw):
    Image = require_pillow()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as img:
                if img.format not in ('PNG','JPEG') or img.width * img.height > 16_777_216:
                    fail('unsupported_image_content_or_pixel_limit')
                info = {'format': img.format.lower(), 'width': img.width, 'height': img.height}
                img.verify()
            with Image.open(io.BytesIO(raw)) as img:
                img.load()
        return info
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        fail('invalid_image_content')


def validate_glb(raw):
    if len(raw) < 20:
        fail('invalid_glb_header')
    magic, version, length = struct.unpack_from('<4sII', raw)
    if magic != b'glTF' or version != 2 or length != len(raw):
        fail('invalid_glb_header')
    offset, chunks = 12, []
    while offset < len(raw):
        if offset + 8 > len(raw):
            fail('invalid_glb_chunk')
        size, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        if size % 4 or offset + size > len(raw):
            fail('invalid_glb_chunk')
        chunks.append((kind, raw[offset:offset+size])); offset += size
    if not chunks or chunks[0][0] != 0x4e4f534a or len(chunks) > 2 or (len(chunks) == 2 and chunks[1][0] != 0x004e4942):
        fail('unsupported_glb_chunks')
    doc = strict_json(chunks[0][1], ARTIFACT_LIMIT)
    if not isinstance(doc, dict) or not isinstance(doc.get('asset'), dict) or doc['asset'].get('version') != '2.0':
        fail('invalid_glb_asset_version')
    def reject_uri(obj):
        if isinstance(obj, dict):
            if 'uri' in obj:
                fail('external_glb_uri_unsupported')
            for v in obj.values(): reject_uri(v)
        elif isinstance(obj,list):
            for v in obj: reject_uri(v)
    reject_uri(doc)
    buffers = doc.get('buffers', [])
    views = doc.get('bufferViews', [])
    if not isinstance(buffers, list) or len(buffers) > 1 or not isinstance(views,list):
        fail('invalid_glb_buffers')
    binary_length = len(chunks[1][1]) if len(chunks) == 2 else 0
    for buffer in buffers:
        if not isinstance(buffer,dict): fail('invalid_glb_buffer')
        size = integer(buffer.get('byteLength'), 0, ARTIFACT_LIMIT)
        if not size <= binary_length <= size + 3:
            fail('invalid_glb_buffer_bounds')
    if binary_length and not buffers:
        fail('unreferenced_glb_binary')
    for view in views:
        if not isinstance(view,dict) or not buffers or integer(view.get('buffer'),0,0) != 0:
            fail('invalid_glb_buffer_view')
        start = integer(view.get('byteOffset',0),0,ARTIFACT_LIMIT)
        size = integer(view.get('byteLength'),1,ARTIFACT_LIMIT)
        if start + size > buffers[0]['byteLength']:
            fail('invalid_glb_buffer_view_bounds')
        if 'byteStride' in view:
            stride = integer(view['byteStride'], 4, 252)
            if stride % 4:
                fail('invalid_glb_buffer_view_stride')
    accessors = doc.get('accessors', [])
    if not isinstance(accessors, list):
        fail('invalid_glb_accessors')
    component_sizes = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
    type_shapes = {'SCALAR': (1, 1), 'VEC2': (1, 2), 'VEC3': (1, 3),
                   'VEC4': (1, 4), 'MAT2': (2, 2), 'MAT3': (3, 3), 'MAT4': (4, 4)}
    for accessor in accessors:
        if not isinstance(accessor, dict) or 'sparse' in accessor:
            fail('unsupported_glb_sparse_accessor')
        component = accessor.get('componentType')
        shape = accessor.get('type')
        if type(component) is not int or component not in component_sizes or not isinstance(shape, str) or shape not in type_shapes:
            fail('invalid_glb_accessor_type')
        count = integer(accessor.get('count'), 1, ARTIFACT_LIMIT)
        if 'bufferView' not in accessor:
            if accessor.get('byteOffset', 0) != 0:
                fail('invalid_glb_accessor_offset')
            continue  # glTF permits zero-initialized accessors without a bufferView.
        index = integer(accessor['bufferView'], 0, len(views) - 1)
        view = views[index]
        unit = component_sizes[component]
        columns, rows = type_shapes[shape]
        column_bytes = unit * rows
        if columns > 1:
            column_bytes = (column_bytes + 3) // 4 * 4
        element_bytes = columns * column_bytes
        # Explicit stride was validated separately; implicit packing may be <4 bytes.
        stride = view.get('byteStride', element_bytes)
        start = integer(accessor.get('byteOffset', 0), 0, ARTIFACT_LIMIT)
        effective_start = view.get('byteOffset', 0) + start
        if start % unit or effective_start % unit or (columns > 1 and effective_start % 4):
            fail('invalid_glb_accessor_alignment')
        if stride < element_bytes or stride % unit or start + (count - 1) * stride + element_bytes > view['byteLength']:
            fail('invalid_glb_accessor_bounds')
    for image in doc.get('images', []):
        if not isinstance(image, dict) or 'bufferView' not in image:
            fail('unsupported_glb_image_reference')
        integer(image['bufferView'], 0, len(views) - 1)
    return {'format':'glb','version':'2.0'}


def validate_content(raw, expected, *, json_validator=None):
    if not isinstance(raw, bytes) or not raw or len(raw) > ARTIFACT_LIMIT:
        fail('artifact_byte_limit')
    format_name = expected['format']
    if format_name in ('png','jpeg'):
        result = decode_image(raw)
        if any(key in expected and result[key] != expected[key] for key in ('format','width','height')):
            fail('artifact_format_or_dimensions_mismatch')
    elif format_name == 'glb':
        result = validate_glb(raw)
    elif format_name == 'json':
        if json_validator is None:
            fail('typed_json_validator_required')
        json_validator(strict_json(raw))
        result = {'format':'json'}
    else:
        fail('unsupported_artifact_format')
    return dict(result, sha256=sha256(raw), size=len(raw))


def preflight(root, outputs, *, allow_owned=None):
    """Read-only all-target path/collision/device checks. No hash-only adoption."""
    paths = set()
    for out in outputs:
        path = checked_path(root, out['path'], output=True)
        if out['path'] in paths:
            fail('duplicate_output_destination')
        paths.add(out['path'])
        if path.parent.exists():
            for sibling in path.parent.iterdir():
                if sibling.stem == path.stem and sibling.is_symlink():
                    fail('alternate_suffix_symlink')
        if path.exists() and not (allow_owned and allow_owned(out)):
            fail('output_collision')
        ancestor = path.parent
        while not ancestor.exists():
            ancestor = ancestor.parent
        if ancestor.stat().st_dev != Path(root).stat().st_dev:
            fail('same_filesystem_required')


def prove_owned(root, destination, staged, expected_hash):
    try:
        dest = checked_path(root, destination, output=True, exists=True)
        stage = Path(staged)
        if stage.is_symlink() or not stage.is_file() or not dest.is_file():
            return False
        a, b = stage.stat(), dest.stat()
        if (a.st_dev,a.st_ino) != (b.st_dev,b.st_ino):
            return False
        return sha256(read_file(root, destination, ARTIFACT_LIMIT)) == expected_hash
    except (ValueError,OSError):
        return False


def link_capability(root, state_dir, outputs):
    """Write-time probe before POST, never silently fall back to overwrite rename."""
    import secrets
    name = 'probe-' + secrets.token_hex(16)
    source = Path(state_dir) / name
    fd = os.open(source, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.close(fd)
    try:
        for out in outputs:
            # Probe actual destination filesystem; no need to create public directories yet.
            ancestor = checked_path(root,out['path'],output=True).parent
            while not ancestor.exists(): ancestor = ancestor.parent
            target = ancestor / name
            try:
                os.link(source,target,follow_symlinks=False)
                if not os.path.samestat(source.stat(),target.stat()): fail('hardlink_unsupported')
            except OSError:
                fail('hardlink_unsupported')
            finally:
                if target.exists() and os.path.samestat(source.stat(),target.stat()): target.unlink()
    finally:
        source.unlink()


def publish(root, destination, staged, expected_hash):
    if prove_owned(root,destination,staged,expected_hash):
        return
    with parent_fd(root,destination,create=True) as (fd,name):
        if os.fstat(fd).st_dev != Path(staged).stat().st_dev:
            fail('same_filesystem_required')
        try:
            os.link(staged,name,dst_dir_fd=fd,follow_symlinks=False)
            os.fsync(fd)
        except FileExistsError:
            fail('output_collision')
        except OSError:
            fail('hardlink_publication_failed')
    if not prove_owned(root,destination,staged,expected_hash):
        fail('publication_identity_changed')


def rollback_owned(root, destination, staged, expected_hash):
    """Compatibility no-op: published paths must be retained after any failure.

    A prior inode/hash proof cannot authorize a later unlink: an artist can edit
    in place between those operations. Keep staging and the journal for recovery.
    """
    return None
