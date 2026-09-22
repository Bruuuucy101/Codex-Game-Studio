"""Optional GitHub Projects transport. Queries are constants; all data is variables.

The injectable executable is a library/test boundary, never a CLI/config option.
"""
import json
import subprocess
import time


class GitHubError(ValueError):
    """Safe diagnostic: raw remote messages and stderr are deliberately excluded."""


PROJECT_FIELDS = 'id number title url public readme owner { __typename ... on User { id login } ... on Organization { id login } }'
PAGE = 'pageInfo { hasNextPage endCursor }'
# Complete documents remain inspectable for validation against GitHub's schema.
DOCUMENTS = {
    'Owner': 'query Owner($login: String!) { repositoryOwner(login: $login) { __typename id login } }',
    'Projects': 'query Projects($id: ID!, $cursor: String) { node(id: $id) { ... on User { projectsV2(first: 100, after: $cursor) { nodes { ' + PROJECT_FIELDS + ' } ' + PAGE + ' } } ... on Organization { projectsV2(first: 100, after: $cursor) { nodes { ' + PROJECT_FIELDS + ' } ' + PAGE + ' } } } }',
    'Project': 'query Project($id: ID!) { node(id: $id) { ... on ProjectV2 { ' + PROJECT_FIELDS + ' } } }',
    'Fields': 'query Fields($id: ID!, $cursor: String) { node(id: $id) { ... on ProjectV2 { fields(first: 100, after: $cursor) { nodes { __typename ... on ProjectV2FieldCommon { id name dataType } ... on ProjectV2SingleSelectField { options { id name color description } } } ' + PAGE + ' } } } }',
    'Items': 'query Items($id: ID!, $cursor: String) { node(id: $id) { ... on ProjectV2 { items(first: 100, after: $cursor, archivedStates: [ARCHIVED, NOT_ARCHIVED]) { nodes { id type isArchived content { __typename ... on DraftIssue { id title body } } } ' + PAGE + ' } } } }',
    'Values': 'query Values($id: ID!, $cursor: String) { node(id: $id) { ... on ProjectV2Item { fieldValues(first: 100, after: $cursor) { nodes { __typename ... on ProjectV2ItemFieldSingleSelectValue { optionId field { ... on ProjectV2FieldCommon { id } } } } ' + PAGE + ' } } } }',
    'CreateProject': 'mutation CreateProject($input: CreateProjectV2Input!) { createProjectV2(input: $input) { projectV2 { ' + PROJECT_FIELDS + ' } } }',
    'UpdateProject': 'mutation UpdateProject($input: UpdateProjectV2Input!) { updateProjectV2(input: $input) { projectV2 { ' + PROJECT_FIELDS + ' } } }',
    'CreateField': 'mutation CreateField($input: CreateProjectV2FieldInput!) { createProjectV2Field(input: $input) { projectV2Field { ... on ProjectV2FieldCommon { id } } } }',
    'UpdateField': 'mutation UpdateField($input: UpdateProjectV2FieldInput!) { updateProjectV2Field(input: $input) { projectV2Field { ... on ProjectV2FieldCommon { id } } } }',
    'CreateDraft': 'mutation CreateDraft($input: AddProjectV2DraftIssueInput!) { addProjectV2DraftIssue(input: $input) { projectItem { id } } }',
    'UpdateDraft': 'mutation UpdateDraft($input: UpdateProjectV2DraftIssueInput!) { updateProjectV2DraftIssue(input: $input) { draftIssue { id } } }',
    'SetValue': 'mutation SetValue($input: UpdateProjectV2ItemFieldValueInput!) { updateProjectV2ItemFieldValue(input: $input) { projectV2Item { id } } }',
}


class GitHub:
    def __init__(self, executable='gh', timeout=30):
        self.executable, self.timeout = executable, timeout

    def request(self, operation, variables):
        query = DOCUMENTS[operation]
        mutation = query.startswith('mutation')
        for attempt in range(1 if mutation else 3):
            transient = False
            try:
                p = subprocess.run([self.executable, 'api', '--hostname', 'github.com', 'graphql', '--input', '-'],
                                   input=json.dumps({'query': query, 'variables': variables}),
                                   text=True, capture_output=True, shell=False, timeout=self.timeout)
            except FileNotFoundError:
                raise GitHubError('MISSING_GH: install GitHub CLI explicitly and authenticate with read:project (preview) or project (write).') from None
            except subprocess.TimeoutExpired:
                transient = True
                reason = 'GitHub request timed out'
            except OSError:
                raise GitHubError('GitHub CLI could not execute; check installation and permissions.') from None
            else:
                try:
                    value = json.loads(p.stdout)
                except (ValueError, TypeError):
                    value = {}
                errors = value.get('errors') if isinstance(value, dict) else None
                if p.returncode == 0 and isinstance(value, dict) and not errors and isinstance(value.get('data'), dict):
                    return value['data']
                # Only recognized transient errors are retried. Do not expose raw text.
                types = {e.get('type') for e in errors or [] if isinstance(e, dict)}
                transient = bool(types & {'INTERNAL', 'SERVICE_UNAVAILABLE', 'RATE_LIMITED'}) or any(t in p.stderr for t in ('HTTP 502', 'HTTP 503', 'HTTP 504', 'connection reset', 'TLS handshake timeout'))
                reason = 'GitHub API failed; check gh authentication, project scope, access and service availability'
            if mutation:
                raise GitHubError('PARTIAL_OR_UNCERTAIN: ' + reason + '; rerun to reconcile remote state. Do not repeat creates manually.')
            if not transient or attempt == 2:
                raise GitHubError(reason + '. Raw diagnostics withheld.')
            time.sleep(0.1 * (attempt + 1))

    def pages(self, operation, identity, field):
        cursor, seen, rows = None, set(), []
        for _ in range(10000):
            data = self.request(operation, {'id': identity, 'cursor': cursor})
            node = data.get('node')
            connection = node.get(field) if isinstance(node, dict) else None
            if not isinstance(connection, dict) or not isinstance(connection.get('nodes'), list):
                raise GitHubError('GitHub project/owner inaccessible or malformed pagination response.')
            if any(not isinstance(x, dict) for x in connection['nodes']):
                raise GitHubError('GitHub returned inaccessible/redacted records; resolve access before syncing.')
            rows.extend(connection['nodes'])
            info = connection.get('pageInfo', {})
            if info.get('hasNextPage') is False:
                return rows
            cursor = info.get('endCursor')
            if not isinstance(cursor, str) or not cursor or cursor in seen:
                raise GitHubError('GitHub returned invalid pagination cursor.')
            seen.add(cursor)
        raise GitHubError('GitHub pagination exceeded safe bound.')

    def owner(self, login):
        value = self.request('Owner', {'login': login}).get('repositoryOwner')
        if not isinstance(value, dict) or value.get('__typename') not in ('User', 'Organization'):
            raise GitHubError('GitHub owner inaccessible; check login and project access.')
        return value

    def projects(self, owner_id):
        return self.pages('Projects', owner_id, 'projectsV2')

    def project(self, project_id):
        value = self.request('Project', {'id': project_id}).get('node')
        if not isinstance(value, dict) or 'number' not in value:
            raise GitHubError('GitHub project inaccessible; check project scope and access.')
        return value

    def fields(self, project_id):
        return self.pages('Fields', project_id, 'fields')

    def items(self, project_id):
        rows = self.pages('Items', project_id, 'items')
        for row in rows:
            if row.get('content') is None or row.get('type') == 'REDACTED':
                raise GitHubError('GitHub has redacted project items; ownership cannot be established. Resolve access before syncing.')
            row['values'] = self.pages('Values', row['id'], 'fieldValues')
        return rows

    def mutate(self, operation, value):
        return self.request(operation, {'input': value})
