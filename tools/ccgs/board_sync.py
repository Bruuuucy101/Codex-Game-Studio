"""Preview-first projection with owned state, conservative recovery and no pruning."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import tempfile
import uuid
from urllib.parse import quote, unquote

from .board_github import GitHub
from .board_snapshot import build_snapshot, validate_snapshot

STATE_DIR = '.ccgs-board'
OPTIONS = {'Stage': ['Backlog', 'Ready', 'In Progress', 'In Review', 'Blocked', 'Done', 'Deferred'],
           'Type': ['Logic', 'Integration', 'Visual', 'UI', 'Config'], 'Size': ['S', 'M', 'L']}
MARKER = re.compile(r'<!-- ccgs-board:v1 namespace=([A-Za-z0-9._-]+) path=([^\s<>]+) key=([a-f0-9]{64}) -->')
CONFIG_KEYS = {'schema_version', 'host', 'owner', 'owner_id', 'owner_type', 'project_id', 'project_number', 'project_url', 'namespace'}


def fail(message):
    raise ValueError(message)


def token(value, name, pattern=r'[A-Za-z0-9._-]{1,100}'):
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        fail('INVALID_BOARD_' + name.upper())
    return value


def state_dir(root, create=False):
    root = Path(root).absolute()
    for path in [root, *root.parents]:
        if path.is_symlink():
            fail('UNSAFE_BOARD_PATH: symlink root/ancestor')
    if not root.is_dir():
        fail('UNSAFE_BOARD_PATH: root is not a directory')
    directory = root / STATE_DIR
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        fail('UNSAFE_BOARD_PATH: .ccgs-board must be an owned directory')
    if create:
        directory.mkdir(mode=0o700, exist_ok=True)
    return directory


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail('INVALID_BOARD_STATE: duplicate JSON key')
        result[key] = value
    return result


def load(root, name):
    path = state_dir(root) / name
    if path.is_symlink():
        fail('UNSAFE_BOARD_PATH: symlink state')
    if not path.exists():
        return None
    if not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > 5 * 1024 * 1024:
        fail('INVALID_BOARD_STATE: state must be bounded regular JSON')
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
        with os.fdopen(fd) as stream:
            value = json.load(stream, object_pairs_hook=unique_object)
    except (OSError, ValueError):
        fail('INVALID_BOARD_STATE: cannot read owned JSON')
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int or value.get('schema_version') != 1:
        fail('INVALID_BOARD_STATE: unknown schema; preserve and inspect file')
    if name != 'board.config.json' and value.get('kind') != name.removesuffix('.json'):
        fail('INVALID_BOARD_STATE: unowned file; preserve and inspect it')
    if name == 'state.json':
        pending = value.get('pending_create')
        if pending is not None:
            if not isinstance(pending, dict) or pending.get('action') not in ('create_card', 'create_field'):
                fail('INVALID_BOARD_STATE: malformed pending create intent')
            token(pending.get('project_id'), 'state_project_id', r'[A-Za-z0-9_=-]{1,200}')
            if pending['action'] == 'create_card':
                token(pending.get('key'), 'state_key', r'[a-f0-9]{64}')
            elif pending.get('field') not in (*OPTIONS, 'Epic'):
                fail('INVALID_BOARD_STATE: unknown pending field')
        intent = value.get('setup_intent')
        if intent is not None:
            if not isinstance(intent, dict):
                fail('INVALID_BOARD_STATE: malformed setup intent')
            token(intent.get('owner_id'), 'state_owner_id', r'[A-Za-z0-9_=-]{1,200}')
            token(intent.get('namespace'), 'state_namespace')
            marker = intent.get('marker')
            if not isinstance(marker, str) or not re.fullmatch(r'<!-- ccgs-board-setup:[a-f0-9]{32} -->', marker):
                fail('INVALID_BOARD_STATE: malformed setup evidence')
            title = intent.get('title')
            if not isinstance(title, str) or not title.strip() or len(title) > 180 or any(ord(c) < 32 for c in title):
                fail('INVALID_BOARD_STATE: malformed setup title')
            if intent.get('temporary_title') != title + ' [ccgs-' + marker.split(':')[1].split(' ')[0] + ']':
                fail('INVALID_BOARD_STATE: inconsistent setup evidence')
            if 'project_id' in intent:
                token(intent['project_id'], 'state_project_id', r'[A-Za-z0-9_=-]{1,200}')
    return value


def save(root, name, value):
    directory = state_dir(root, True)
    # Never replace unknown/unowned existing state or a symlink.
    load(root, name)
    value = dict(value, schema_version=1)
    if name != 'board.config.json':
        value['kind'] = name.removesuffix('.json')
    fd, temp = tempfile.mkstemp(prefix='.pending-', dir=directory)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, directory / name)
        # Persist rename before a remote mutation can depend on its intent.
        if os.name == 'posix':
            dfd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


@contextmanager
def lock(root):
    path = state_dir(root, True) / 'lock'
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        fail('BOARD_LOCKED: inspect .ccgs-board/lock/owner.json; never remove a live lock. After independently confirming the recorded host/process has stopped, manually remove that lock directory and rerun reconciliation.')
    owner = {'pid': os.getpid(), 'host': socket.gethostname(), 'token': uuid.uuid4().hex}
    try:
        (path / 'owner.json').write_text(json.dumps(owner))
        yield
    finally:
        try:
            if json.loads((path / 'owner.json').read_text()) == owner:
                (path / 'owner.json').unlink(); path.rmdir()
        except (OSError, ValueError):
            pass  # An externally altered lock belongs to its new owner.


def config_validate(config):
    if not isinstance(config, dict) or set(config) != CONFIG_KEYS or type(config.get('schema_version')) is not int or config.get('schema_version') != 1 or config.get('host') != 'github.com':
        fail('INVALID_BOARD_CONFIG: unsupported keys/schema/host')
    token(config['owner'], 'owner', r'[A-Za-z0-9][A-Za-z0-9-]{0,99}')
    token(config['namespace'], 'namespace')
    for key in ('owner_id', 'project_id'):
        token(config[key], key, r'[A-Za-z0-9_=-]{1,200}')
    if config['owner_type'] not in ('User', 'Organization') or type(config['project_number']) is not int or config['project_number'] <= 0:
        fail('INVALID_BOARD_CONFIG: owner type or project number')
    segment = 'users' if config['owner_type'] == 'User' else 'orgs'
    if config['project_url'] != f'https://github.com/{segment}/{config["owner"]}/projects/{config["project_number"]}':
        fail('INVALID_BOARD_CONFIG: project URL does not match pinned identity')
    return config


def config_for(owner, project, namespace):
    return config_validate({'schema_version':1, 'host':'github.com', 'owner':owner['login'], 'owner_id':owner['id'],
                            'owner_type':owner['__typename'], 'project_id':project['id'], 'project_number':project['number'],
                            'project_url':project['url'], 'namespace':namespace})


def verify_project(config, project):
    expected = config_for(project['owner'], project, config['namespace'])
    if config != expected:
        fail('BOARD_IDENTITY_CONFLICT: remote project no longer matches pinned config')


def setup(root, owner, namespace, number=None, title=None, write=False, github=None):
    token(owner, 'owner', r'[A-Za-z0-9][A-Za-z0-9-]{0,99}'); token(namespace, 'namespace')
    if (number is None) == (title is None) or (number is not None and (type(number) is not int or number < 1)):
        fail('SETUP_REQUIRES_NUMBER_OR_TITLE')
    if title is not None and (not isinstance(title, str) or not title.strip() or len(title) > 180 or any(ord(c)<32 for c in title)):
        fail('INVALID_BOARD_TITLE: use 1–180 printable characters')
    gh = github or GitHub()
    if write:
        with lock(root):
            return _setup(root, owner, namespace, number, title, True, gh)
    return _setup(root, owner, namespace, number, title, False, gh)


def _setup(root, owner_name, namespace, number, title, write, gh):
    existing = load(root, 'board.config.json')
    if existing:
        config_validate(existing)
        if existing['owner'].lower() != owner_name.lower() or existing['namespace'] != namespace or (number is not None and number != existing['project_number']):
            fail('BOARD_CONFIG_CONFLICT: existing config will not be replaced')
        project = gh.project(existing['project_id']); verify_project(existing, project)
        if title is not None and title != project['title']:
            fail('BOARD_CONFIG_CONFLICT: title differs; use pinned project number')
        return {'status':'VERIFIED' if write else 'PREVIEW', 'config':existing, 'changes':[]}
    owner = gh.owner(owner_name)
    projects = gh.projects(owner['id'])
    state = load(root, 'state.json') or {}
    intent = state.get('setup_intent')
    if intent:
        if not isinstance(intent, dict) or intent.get('owner_id') != owner['id'] or intent.get('namespace') != namespace or (title is not None and intent.get('title') != title):
            fail('SETUP_INTENT_CONFLICT: preserve .ccgs-board/state.json and resolve the prior setup')
        if number is not None:
            # Explicit adoption can resolve an ambiguous lost creation result.
            candidates = [p for p in projects if p['number'] == number]
        else:
            candidates = [p for p in projects if p['id'] == intent.get('project_id') or p['title'] == intent.get('temporary_title') or intent.get('marker') == p.get('readme')]
        if len(candidates) != 1:
            fail('SETUP_UNCERTAIN: do not repeat creation. Inspect owner projects, then explicitly adopt the intended --number; candidates: ' + ', '.join(str(p['number']) for p in projects))
        project = candidates[0]
        owned_creation = (project['id'] == intent.get('project_id') or project['title'] == intent.get('temporary_title') or project.get('readme') == intent.get('marker'))
        if write and owned_creation:
            gh.mutate('UpdateProject', {'projectId':project['id'], 'title':intent['title'], 'public':False, 'readme':intent['marker']})
            project = gh.project(project['id'])
            if project.get('public') is not False or project.get('readme') != intent['marker'] or project['title'] != intent['title']:
                fail('SETUP_VERIFICATION_FAILED: rerun to reconcile')
    else:
        candidates = [p for p in projects if p['number'] == number] if number is not None else [p for p in projects if p['title'] == title]
        if len(candidates) > 1:
            fail('SETUP_AMBIGUOUS: specify --number; candidates: ' + ', '.join(str(p['number']) for p in candidates))
        if candidates:
            project = candidates[0]
        elif number is not None:
            fail('GitHub project number inaccessible or missing; check permissions')
        elif not write:
            return {'status':'PREVIEW', 'changes':[{'action':'create_private_project','owner':owner['login'],'title':title,'namespace':namespace}]}
        else:
            key = uuid.uuid4().hex
            intent = {'owner_id':owner['id'], 'namespace':namespace, 'title':title, 'temporary_title':title + ' [ccgs-' + key + ']', 'marker':'<!-- ccgs-board-setup:' + key + ' -->'}
            save(root, 'state.json', {'setup_intent':intent, 'status':'SETUP_PENDING'})
            result = gh.mutate('CreateProject', {'ownerId':owner['id'], 'title':intent['temporary_title'], 'clientMutationId':key})
            project = result['createProjectV2']['projectV2']
            intent['project_id'] = project['id']
            save(root, 'state.json', {'setup_intent':intent, 'status':'SETUP_PENDING'})
            gh.mutate('UpdateProject', {'projectId':project['id'], 'public':False, 'readme':intent['marker'], 'title':title})
            project = gh.project(project['id'])
            if project.get('public') is not False or project.get('readme') != intent['marker'] or project['title'] != title:
                fail('SETUP_VERIFICATION_FAILED: rerun to reconcile')
    config = config_for(owner, project, namespace)
    verify_project(config, gh.project(project['id']))
    if write:
        save(root, 'board.config.json', config)
        save(root, 'state.json', {'status':'SETUP_COMPLETE'})
    return {'status':'VERIFIED' if write else 'PREVIEW', 'config':config, 'changes':[]}


def identity(namespace, path):
    return hashlib.sha256((namespace + '\0' + path).encode()).hexdigest()


def desired(namespace, story):
    path = story['path']; key = identity(namespace, path)
    marker = f'<!-- ccgs-board:v1 namespace={namespace} path={quote(path, safe="/")} key={key} -->'
    body = (marker + '\n\nSource: `' + path + '`\nEpic: ' + story['raw_metadata']['Epic'] +
            '\n\nThis draft is a read-only projection of the local story. Edit the canonical story to change managed content.\n')
    return {'key':key, 'path':path, 'title':story['title'], 'body':body, 'fields':story['normalized']}


def managed_items(items, namespace):
    managed = {}
    for item in items:
        content = item['content']
        if content.get('__typename') != 'DraftIssue':
            continue
        markers = list(MARKER.finditer(content.get('body') or ''))
        owned = [m for m in markers if m[1] == namespace]
        if not owned:
            continue
        if len(owned) != 1:
            fail('DUPLICATE_BOARD_MARKER: one managed identity per draft is required')
        marker = owned[0]; path, key = unquote(marker[2]), marker[3]
        parts = Path(path).parts
        if (len(parts) != 4 or parts[:2] != ('production', 'epics') or '..' in parts or
                quote(path, safe='/') != marker[2] or identity(namespace, path) != key):
            fail('INVALID_BOARD_MARKER: inspect managed draft identity')
        if key in managed:
            fail('DUPLICATE_BOARD_MARKER: resolve duplicate managed cards before any mutation')
        managed[key] = dict(item, path=path)
    return managed


def field_plan(fields, stories):
    required = dict(OPTIONS, Epic=sorted({s['normalized']['Epic'] for s in stories}))
    by_name, changes = {}, []
    for name, wanted in required.items():
        matches = [f for f in fields if f.get('name') == name]
        if len(matches) > 1:
            fail('BOARD_FIELD_CONFLICT: duplicate field ' + name)
        field = matches[0] if matches else None
        if field and (field.get('__typename') != 'ProjectV2SingleSelectField' or field.get('dataType') != 'SINGLE_SELECT'):
            fail('BOARD_FIELD_CONFLICT: ' + name + ' must be a single-select field')
        options = field.get('options', []) if field else []
        if len({o['name'] for o in options}) != len(options):
            fail('BOARD_FIELD_CONFLICT: duplicate option names in ' + name)
        missing = [n for n in wanted if n not in {o['name'] for o in options}]
        if len(options) + len(missing) > 50:
            fail('BOARD_OPTION_LIMIT: ' + name + ' exceeds 50 options; existing options will not be removed')
        by_name[name] = field
        if (not field and wanted) or missing:
            changes.append({'action':'create_field' if not field else 'extend_field', 'field':name,
                            'options':[{k:o[k] for k in ('id','name','color','description')} for o in options] +
                                      [{'name':n,'color':'GRAY','description':''} for n in missing]})
    return by_name, changes


def plan(config, snapshot, fields, items):
    managed = managed_items(items, config['namespace'])
    by_name, changes = field_plan(fields, snapshot['stories'])
    wanted = [desired(config['namespace'], s) for s in snapshot['stories']]
    archived = []
    for record in wanted:
        item = managed.get(record['key'])
        if item and item['isArchived']:
            archived.append(record['path']); continue
        if not item:
            changes.append({'action':'create_card', 'path':record['path']})
        elif item['content']['title'] != record['title'] or item['content']['body'] != record['body']:
            changes.append({'action':'update_card', 'path':record['path']})
        values = {v['field']['id']:v.get('optionId') for v in item['values'] if v.get('__typename') == 'ProjectV2ItemFieldSingleSelectValue'} if item else {}
        for name, value in record['fields'].items():
            field = by_name[name]
            option = next((o['id'] for o in field['options'] if o['name']==value), None) if field else None
            if not field or option is None or values.get(field['id']) != option:
                changes.append({'action':'set_field', 'path':record['path'], 'field':name, 'value':value})
    paths = {r['path'] for r in wanted}
    stale = sorted(i['path'] for i in managed.values() if i['path'] not in paths and (snapshot['epic'] is None or i['path'].split('/')[2] == snapshot['epic']))
    return {'changes':changes, 'stale':stale, 'archived':sorted(archived)}, managed, by_name


def sync(root, epic=None, write=False, github=None):
    gh = github or GitHub()
    if write:
        with lock(root):
            return _sync(root, epic, True, gh)
    return _sync(root, epic, False, gh)


def _sync(root, epic, write, gh):
    config = config_validate(load(root, 'board.config.json'))
    snapshot = build_snapshot(root, epic)
    verify_project(config, gh.project(config['project_id']))
    fields, items = gh.fields(config['project_id']), gh.items(config['project_id'])
    result, managed, by_name = plan(config, snapshot, fields, items)
    result.update(status='PREVIEW', snapshot=snapshot, project_url=config['project_url'])
    state = load(root, 'state.json') or {}
    pending = state.get('pending_create')
    if pending:
        if pending.get('project_id') != config['project_id']:
            fail('BOARD_STATE_CONFLICT: pending operation belongs to another project')
        resolved = ((pending.get('action') == 'create_card' and pending.get('key') in managed) or
                    (pending.get('action') == 'create_field' and by_name.get(pending.get('field')) is not None))
        if not resolved:
            fail('BOARD_CREATE_UNCERTAIN: remote create not visible. Restore access/wait and rerun; inspect state.json and the remote board before explicitly clearing an unresolved intent. No create was retried.')
    if not write:
        return result
    # Check every owned state file before any remote write, including cache output.
    load(root, 'mapping.json')
    validate_snapshot(root, snapshot)
    original_changes = result['changes']
    completed = 0
    save(root, 'state.json', {'status':'APPLYING', 'snapshot_sha256':snapshot['sha256'], 'completed':completed})
    # Re-read and re-plan after each mutation. Creates are never repeated on failure.
    # This also refreshes option IDs and catches drift, duplicates and conflicts.
    limit = len(original_changes) + 20
    try:
        while result['changes']:
            if completed >= limit:
                fail('BOARD_REMOTE_DRIFT: remote changes prevented convergence; rerun after other writers stop')
            change = result['changes'][0]; action = change['action']
            validate_snapshot(root, snapshot)
            pending = None
            if action in ('create_field', 'extend_field'):
                payload = {'singleSelectOptions':change['options']}
                if action == 'create_field':
                    payload.update(projectId=config['project_id'], name=change['field'], dataType='SINGLE_SELECT')
                    operation = 'CreateField'; pending = {'action':action,'field':change['field'],'project_id':config['project_id']}
                else:
                    payload['fieldId'] = by_name[change['field']]['id']; operation = 'UpdateField'
            else:
                record = desired(config['namespace'], next(s for s in snapshot['stories'] if s['path']==change['path']))
                item = managed.get(record['key'])
                if action == 'create_card':
                    operation = 'CreateDraft'; payload = {'projectId':config['project_id'], 'title':record['title'], 'body':record['body']}
                    pending = {'action':action,'key':record['key'],'project_id':config['project_id']}
                elif action == 'update_card':
                    operation = 'UpdateDraft'; payload = {'draftIssueId':item['content']['id'], 'title':record['title'], 'body':record['body']}
                else:
                    field = by_name[change['field']]
                    option = next(o['id'] for o in field['options'] if o['name']==change['value'])
                    operation = 'SetValue'; payload = {'projectId':config['project_id'], 'itemId':item['id'], 'fieldId':field['id'], 'value':{'singleSelectOptionId':option}}
            save(root, 'state.json', {'status':'APPLYING', 'snapshot_sha256':snapshot['sha256'], 'completed':completed, 'pending_create':pending})
            gh.mutate(operation, payload); completed += 1
            fields, items = gh.fields(config['project_id']), gh.items(config['project_id'])
            result, managed, by_name = plan(config, snapshot, fields, items)
            if pending:
                resolved = pending.get('key') in managed if action == 'create_card' else by_name.get(change['field']) is not None
                if not resolved:
                    fail('BOARD_CREATE_UNCERTAIN: successful response but create is not visible; rerun to reconcile')
            save(root, 'state.json', {'status':'APPLYING', 'snapshot_sha256':snapshot['sha256'], 'completed':completed})
        validate_snapshot(root, snapshot)
        verify_project(config, gh.project(config['project_id']))
        # Includes a final independent read even for unchanged runs.
        result, managed, _ = plan(config, snapshot, gh.fields(config['project_id']), gh.items(config['project_id']))
        if result['changes']:
            fail('BOARD_VERIFICATION_FAILED: remote drift; rerun to reconcile')
        mapping = {key:{'item_id':item['id'],'content_id':item['content']['id'],'path':item['path']} for key,item in managed.items()}
        save(root, 'mapping.json', {'project_id':config['project_id'], 'namespace':config['namespace'], 'items':mapping})
        save(root, 'state.json', {'status':'VERIFIED', 'snapshot_sha256':snapshot['sha256'], 'completed':completed})
    except (ValueError, OSError, KeyError, TypeError):
        current = load(root, 'state.json') or {}
        current.update(status='PARTIAL_OR_UNCERTAIN', completed=completed)
        save(root, 'state.json', current)
        raise
    return dict(result, status='VERIFIED', applied=original_changes, mutation_count=completed, snapshot=snapshot, project_url=config['project_url'])
