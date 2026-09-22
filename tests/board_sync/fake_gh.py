#!/usr/bin/env python3
"""Stateful external GitHub stand-in; exercises JSON stdin and exact gh argv.

This fixture checks selected contracts, not full GraphQL schema validation.
"""
import json
import os
from pathlib import Path
import re
import sys
import time

assert sys.argv[1:] == ['api', '--hostname', 'github.com', 'graphql', '--input', '-']
p = Path(os.environ['FAKE_GH_STATE'])
s = json.loads(p.read_text())
request = json.load(sys.stdin)
assert set(request) == {'query', 'variables'}
q, v = request['query'], request['variables']
op = re.search(r'(?:query|mutation)\s+(\w+)', q).group(1)
s.setdefault('calls', []).append({'operation': op, **request})

def save():
    p.write_text(json.dumps(s))

def error():
    save()
    print('ghp_SUPER_SECRET_TOKEN', file=sys.stderr)
    print(json.dumps({'errors': [{'message': 'ghp_SUPER_SECRET_TOKEN', 'type': 'INTERNAL' if s.get('transient') else 'FORBIDDEN'}]}))
    sys.exit(1 if s.get('http_error') else 0)

failure = s.get('failure', {})
fail = failure.get('operation') == op and failure.get('remaining', 0) > 0
if fail:
    failure['remaining'] -= 1
    if not failure.get('after'):
        error()
if s.get('sleep_on') == op:
    save()
    time.sleep(s.get('sleep_seconds',1))
if op == 'Owner':
    data = {'repositoryOwner': s.get('owner', {'id': 'USER_1', 'login': 'octocat', '__typename': 'User'})}
elif op == 'Projects':
    data = {'node': {'projectsV2': None}}
elif op == 'Project':
    if s.get('drift_on_second_project_read'):
        s['project_read_count'] = s.get('project_read_count', 0) + 1
        if s['project_read_count'] == 2 and s['items']:
            s['items'][0]['content']['title'] = 'concurrent drift during final verification'
    project = next((x for x in s['projects'] if x['id'] == v['id']), None)
    data = {'node': project}
elif op == 'CreateProject':
    i = v['input']; n = len(s['projects']) + 1
    project = {'id': f'PROJECT_{n}', 'number': n, 'title': i['title'], 'url': f'https://github.com/users/octocat/projects/{n}', 'public': False, 'readme': '', 'owner': s.get('owner', {'id':'USER_1', 'login':'octocat', '__typename':'User'})}
    if project['owner']['__typename'] == 'Organization':
        project['url'] = f'https://github.com/orgs/{project["owner"]["login"]}/projects/{n}'
    s['projects'].append(project)
    data = {'createProjectV2': {'projectV2': project}}
elif op == 'UpdateProject':
    i = v['input']; project = next(x for x in s['projects'] if x['id'] == i['projectId'])
    project.update({k: val for k, val in i.items() if k in ('title', 'public', 'readme')})
    data = {'updateProjectV2': {'projectV2': project}}
elif op in ('Fields', 'Items', 'Values'):
    data = {'node': {}}
elif op in ('CreateField', 'UpdateField'):
    i = v['input']
    if op == 'CreateField':
        assert i['dataType'] == 'SINGLE_SELECT'
        field = {'id': f'FIELD_{len(s["fields"])+1}', 'name': i['name'], '__typename': 'ProjectV2SingleSelectField', 'dataType': 'SINGLE_SELECT', 'options': []}
        s['fields'].append(field)
    else:
        field = next(f for f in s['fields'] if f['id'] == i['fieldId'])
        # Real updates must preserve unrelated option identities and metadata.
        assert all(o in i['singleSelectOptions'] for o in field['options'])
    field['options'] = [dict(o, id=o.get('id', f'{field["id"]}_OPT_{n}')) for n, o in enumerate(i['singleSelectOptions'])]
    assert len(field['options']) <= 50
    data = {('createProjectV2Field' if op == 'CreateField' else 'updateProjectV2Field'): {'projectV2Field': field}}
elif op == 'CreateDraft':
    i = v['input']; n = len(s['items'])+1
    item = {'id': f'ITEM_{n}', 'isArchived': False, 'type': 'DRAFT_ISSUE', 'content': {'__typename':'DraftIssue', 'id':f'DRAFT_{n}', 'title': i['title'], 'body':i['body']}, 'values': []}
    s['items'].append(item)
    data = {'addProjectV2DraftIssue': {'projectItem': {'id': item['id']}}}
elif op == 'UpdateDraft':
    i = v['input']; item = next(x for x in s['items'] if x['content']['id'] == i['draftIssueId'])
    assert i['draftIssueId'].startswith('DRAFT_')
    item['content'].update(title=i['title'], body=i['body'])
    data = {'updateProjectV2DraftIssue': {'draftIssue': {'id':i['draftIssueId']}}}
elif op == 'SetValue':
    i = v['input']; item = next(x for x in s['items'] if x['id'] == i['itemId'])
    assert i['itemId'].startswith('ITEM_')
    field = next(f for f in s['fields'] if f['id'] == i['fieldId'])
    assert any(o['id'] == i['value']['singleSelectOptionId'] for o in field['options'])
    item['values'] = [x for x in item['values'] if x['field']['id'] != field['id']]
    item['values'].append({'__typename':'ProjectV2ItemFieldSingleSelectValue', 'field': {'id': field['id']}, 'optionId': i['value']['singleSelectOptionId']})
    data = {'updateProjectV2ItemFieldValue': {'projectV2Item': {'id':item['id']}}}
else:
    raise AssertionError('Unrecognized operation ' + op)

def page(rows):
    at = int(v.get('cursor') or 0); size = s.get('page_size', 1)
    chunk = rows[at:at+size]; end = at + len(chunk)
    return {'nodes': chunk, 'pageInfo': {'hasNextPage': end < len(rows), 'endCursor': str(end) if chunk else None}}

if op == 'Projects':
    data['node']['projectsV2'] = page(s['projects'])
if op == 'Fields':
    data['node']['fields'] = page(s['fields'])
if op == 'Items':
    assert 'archivedStates: [ARCHIVED, NOT_ARCHIVED]' in q
    data['node']['items'] = page([{k: x[k] for k in ('id','isArchived','type','content')} for x in s['items']])
if op == 'Values':
    data['node']['fieldValues'] = page(next(x for x in s['items'] if x['id'] == v['id'])['values'])
if s.get('timeout_after') == op:
    s.pop('timeout_after')
    save()
    time.sleep(35)
if fail:
    error()
if s.get('change_source_on') == op:
    Path(s['source_path']).write_text(Path(s['source_path']).read_text() + '\nchanged\n')
    s.pop('change_source_on')
save()
print(json.dumps({'data': data}))
