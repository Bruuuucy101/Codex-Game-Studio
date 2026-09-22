"""Strict request preparation and project-confined filesystem primitives."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit, urlunsplit

REQUEST_LIMIT = 4 * 1024 * 1024
SOURCE_LIMIT = 2 * 1024 * 1024
IMAGE_LIMIT = 16 * 1024 * 1024
ARTIFACT_LIMIT = 128 * 1024 * 1024
JSON_LIMIT = 64 * 1024 * 1024
SLUG = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}\Z')
HASH = re.compile(r'[a-f0-9]{64}\Z')


def fail(category):
    raise ValueError(category)


def strict_json(raw, limit=REQUEST_LIMIT):
    """Decode bounded UTF-8 JSON, rejecting duplicate keys and nonfinite values."""
    if not isinstance(raw, (bytes, str)) or len(raw) > limit:
        fail('json_size_limit')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail('duplicate_json_field')
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=pairs,
                           parse_constant=lambda _: fail('nonfinite_number'))
        canonical(value)  # Also rejects float exponent overflow, e.g. 1e999.
        return value
    except (UnicodeError, json.JSONDecodeError, OverflowError, RecursionError):
        fail('invalid_json')


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, UnicodeError, RecursionError):
        fail('invalid_json_value')


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def object_fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or set(value) - set(required) - set(optional):
        fail('unsupported_or_missing_fields')


def integer(value, minimum=0, maximum=2**63-1):
    if type(value) is not int or not minimum <= value <= maximum:
        fail('invalid_integer_or_dimension')
    return value


def string(value, maximum=2000, minimum=1):
    if not isinstance(value, str) or not minimum <= len(value) <= maximum or any(ord(c) < 32 and c not in '\n\t' for c in value):
        fail('invalid_string')
    return value


def identifier(value):
    if not isinstance(value, str) or not SLUG.fullmatch(value):
        fail('invalid_operation_id')
    return value


def task_id(value):
    # Opaque provider IDs; exclude path/query delimiters and control characters.
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}', value):
        fail('invalid_provider_task_id')
    return value


def relative_path(value, output=False):
    if not isinstance(value, str) or len(value) > 512 or '\\' in value or '\x00' in value:
        fail('invalid_project_path')
    parts = value.split('/')
    if any(p in ('', '.', '..') or p.startswith('.') or not re.fullmatch(r'[A-Za-z0-9_ .-]+', p) for p in parts):
        fail('invalid_project_path')
    if output and (len(parts) < 2 or parts[0] != 'assets'):
        fail('output_must_be_under_assets')
    return value


def check_root(root):
    if any(getattr(os, flag, None) is None for flag in ('O_NOFOLLOW', 'O_DIRECTORY', 'O_NONBLOCK')):
        fail('safe_filesystem_primitives_unavailable')
    root = Path(root).absolute()
    if root.is_symlink() or root.resolve() != root or not root.is_dir():
        fail('project_root_must_be_real_directory')
    return root


def checked_path(root, value, *, output=False, exists=False):
    relative_path(value, output=output)
    root = check_root(root)
    path = root
    for i, part in enumerate(value.split('/')):
        path = path / part
        try:
            info = path.lstat()
        except FileNotFoundError:
            if exists:
                fail('source_file_missing')
            continue
        if stat.S_ISLNK(info.st_mode):
            fail('symlink_path_rejected')
        if i < len(value.split('/')) - 1 and not stat.S_ISDIR(info.st_mode):
            fail('parent_not_directory')
    return path


@contextmanager
def parent_fd(root, value, *, create=False, mode=0o755, private=False):
    """Walk from a real root using dirfd + O_NOFOLLOW; keep parent open for I/O."""
    if private:
        if not isinstance(value, str) or any(p in ('', '.', '..') for p in value.split('/')):
            fail('invalid_private_path')
    else:
        relative_path(value)
    fd = os.open(check_root(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        parts = value.split('/')
        for part in parts[:-1]:
            if create:
                try:
                    os.mkdir(part, mode, dir_fd=fd)
                    os.fsync(fd)
                except FileExistsError:
                    pass
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
            if private and stat.S_IMODE(os.fstat(fd).st_mode) & 0o077:
                fail('private_directory_permissions')
        yield fd, parts[-1]
    except OSError:
        fail('unsafe_or_unavailable_path')
    finally:
        os.close(fd)


def read_file(root, value, limit, *, private=False):
    with parent_fd(root, value, private=private) as (fd, name):
        try:
            file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        except OSError:
            fail('source_file_missing_or_unsafe')
        with os.fdopen(file_fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
                fail('file_type_or_size_limit')
            if private and stat.S_IMODE(info.st_mode) & 0o077:
                fail('private_file_permissions')
            raw = stream.read(limit + 1)
            if len(raw) > limit:
                fail('file_size_limit')
            return raw


def state_path(root, state_dir):
    root = check_root(root)
    if Path(state_dir).absolute() != root / '.ccgs-assets':
        fail('private_state_must_be_project_ccgs_assets')
    if Path(state_dir).is_symlink():
        fail('symlink_state_rejected')
    return root / '.ccgs-assets'


def redact(value):
    """Public views omit complete URL query/fragment and bearer-like data fields."""
    if isinstance(value, dict):
        return {k: ('[private]' if k.lower() in {'file_token','authorization','api_key','secret','base64'} else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        # URLs may occur inside descriptions, not only dedicated URL parameters.
        def clean(match):
            url = urlsplit(match.group(0))
            host = url.hostname or ''
            return urlunsplit((url.scheme, host, url.path, '', ''))
        return re.sub(r'https?://[^\s<>"\']+', clean, value)
    return value


def get_adapter(provider, adapters=None):
    if adapters and provider in adapters:
        return adapters[provider]
    if provider == 'pixellab':
        from .pixellab import PixelLab
        return PixelLab()
    if provider == 'meshy':
        from .meshy import Meshy
        return Meshy()
    if provider == 'tripo':
        from .tripo import Tripo
        return Tripo()
    fail('unsupported_provider')


def prepare_request(root, state_dir, request_path, *, adapters=None):
    """Read a project-local request and return a canonical, private JSON plan; no writes/network."""
    root = check_root(root)
    state_path(root, state_dir)
    raw = strict_json(read_file(root, request_path, REQUEST_LIMIT))
    return prepare_value(root, state_dir, raw, adapters=adapters)


def prepare_value(root, state_dir, value, *, adapters=None):
    root = check_root(root)
    state_path(root, state_dir)
    object_fields(value, ('schema_version','provider','operation','asset_id','source_files','parameters','outputs'), ('standalone','rights_note'))
    if type(value['schema_version']) is not int or value['schema_version'] != 1:
        fail('unsupported_schema_version')
    standalone = value.get('standalone', False)
    if type(standalone) is not bool:
        fail('standalone_must_be_boolean')
    identifier(value['asset_id'])
    if not standalone and not re.fullmatch(r'ASSET-[0-9]{3,}', value['asset_id']):
        fail('canonical_asset_id_required')
    sources = value['source_files']
    if not isinstance(sources, list) or len(sources) > 32 or any(not isinstance(p,str) for p in sources) or len(set(sources)) != len(sources):
        fail('invalid_source_files')
    if 'rights_note' in value:
        string(value['rights_note'], 4000, 0)
    string(value['provider'], 32)
    string(value['operation'], 96)
    adapter = get_adapter(value['provider'], adapters)
    parameters, image_paths, expected = adapter.prepare(root, value['operation'], value['parameters'])
    inputs = {}
    source_bytes = {}
    for name in sources:
        raw = read_file(root, name, SOURCE_LIMIT)
        source_bytes[name] = raw
        inputs[name] = {'path': name, 'kind': 'source', 'sha256': sha256(raw), 'size': len(raw)}
    for name in image_paths:
        raw = read_file(root, name, IMAGE_LIMIT)
        inputs[name] = {'path': name, 'kind': 'image', 'sha256': sha256(raw), 'size': len(raw)}
    if not standalone:
        specs = [p for p in sources if p.startswith('design/assets/specs/') and p.endswith('.md')]
        if 'design/art/art-bible.md' not in sources or not specs:
            fail('canonical_spec_and_art_bible_required')
        token = re.compile(rb'(?<![A-Za-z0-9_-])' + value['asset_id'].encode() + rb'(?![A-Za-z0-9_-])')
        if not any(token.search(source_bytes[p]) for p in specs):
            fail('asset_id_absent_from_source_spec')
    outputs = value['outputs']
    if not isinstance(outputs, list) or len(outputs) > 16 or len(outputs) != len(expected):
        fail('unexpected_output_count')
    seen_keys, seen_paths = set(), set()
    for out in outputs:
        object_fields(out, ('key','path','format'), ('width','height'))
        key = identifier(out['key'])
        relative_path(out['path'], output=True)
        string(out['format'], 16)
        if key not in expected or key in seen_keys or out['path'] in seen_paths:
            fail('unexpected_or_duplicate_output')
        seen_keys.add(key); seen_paths.add(out['path'])
        path = checked_path(root, out['path'], output=True)
        contract = expected[key]
        if out['format'] not in contract['formats']:
            fail('unsupported_output_format')
        suffix = { 'png':'.png', 'jpeg':'.jpg', 'glb':'.glb', 'json':'.json' }[out['format']]
        if path.suffix.lower() not in ([suffix,'.jpeg'] if suffix == '.jpg' else [suffix]):
            fail('output_suffix_mismatch')
        for dimension in ('width','height'):
            if dimension in contract:
                if dimension not in out or integer(out[dimension],1,100000) != contract[dimension]:
                    fail('output_dimensions_mismatch')
            elif dimension in out:
                fail('unexpected_output_dimensions')
    normalized = dict(value, standalone=standalone, parameters=parameters)
    dependencies = []
    loaded_dependencies = {}
    for job in adapter.dependency_ids(parameters):
        from .jobs import load_dependency
        loaded = load_dependency(root, state_dir, job, adapters=adapters)
        dependencies.append(loaded['pin'])
        loaded_dependencies[job] = loaded
    local_validator = getattr(adapter, 'validate_local_dependencies', None)
    if local_validator is not None:
        if not callable(local_validator):
            fail('invalid_adapter_local_dependency_validator')
        local_validator(value['operation'], parameters, loaded_dependencies)
    plan = {'schema_version':1, 'request': normalized,
            'inputs': sorted(inputs.values(), key=lambda x:x['path']),
            'dependencies': dependencies}
    plan['request_sha256'] = sha256(canonical(plan))
    return plan


def verify_fresh(root, plan):
    for item in plan['inputs']:
        limit = ARTIFACT_LIMIT if item['kind'] == 'artifact' else (IMAGE_LIMIT if item['kind'] == 'image' else SOURCE_LIMIT)
        raw = read_file(root, item['path'], limit)
        if sha256(raw) != item['sha256'] or len(raw) != item['size']:
            fail('source_changed_since_plan')
