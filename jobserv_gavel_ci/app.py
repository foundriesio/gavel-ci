# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>
import secrets

import requests

from flask import request

from jobserv.app import app
from jobserv.flask import permissions
from jobserv.jsend import ApiError, get_or_404, jsendify
from jobserv.models import Project, ProjectTrigger, TriggerTypes, db

app = app


def _register_github_hook(project, url, api_token, hook_token, server_name):
    data = {
        'name': 'web',
        'active': True,
        'events': [
            'pull_request',
            'pull_request_review_comment',
            'issue_comment',
        ],
        'config': {
            'url': 'https://%s/github/%s/' % (server_name, project.name),
            'content_type': 'json',
            'secret': hook_token,
        }
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'token ' + api_token,
    }

    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code != 201:
        raise ApiError(resp.status_code, resp.json())


@app.route('/projects/<project:proj>/gh_trigger/', methods=('POST',))
def project_create_trigger(proj):
    u = permissions.assert_internal_user()
    p = get_or_404(Project.query.filter_by(name=proj))

    d = request.get_json() or {}
    required = ('githubtok', 'owner', 'project')
    missing = []
    for x in required:
        if x not in d:
            missing.append(x)
    if missing:
        raise ApiError(401, 'Missing parameters: %s' % ','.join(missing))

    hook_url = 'https://api.github.com/repos/%s/%s/hooks'
    hook_url = hook_url % (d.pop('owner'), d.pop('project'))

    d['webhook-key'] = secrets.token_urlsafe()
    dr = df = None
    try:
        dr = d.pop('definition_repo')
        df = d.pop('definition_file')
    except KeyError:
        pass

    db.session.add(ProjectTrigger(
        u.email, TriggerTypes.github_pr.value, p, dr, df, d))

    _register_github_hook(
        p, hook_url, d['githubtok'], d['webhook-key'], 'api.gavelci.us')
    db.session.commit()
    return jsendify({}, 201)
