# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>
import requests

from flask import (
    Blueprint, abort, jsonify, make_response, render_template, request,
)
from flask_login import current_user

from gavel_ci.settings import JOBSERV_URL

blueprint = Blueprint('jobserv', __name__, url_prefix='/')


def _get(path):
    assert path[0] == '/'

    get = requests.get
    if current_user.is_authenticated:
        get = current_user.authenticated_get

    url = JOBSERV_URL + path
    r = get(url)
    if r.status_code != 200:
        abort(make_response(r.text, r.status_code))
    return r.json()['data']


def _list(path):
    p = request.args.get('page')
    if p:
        path += '?page=%s&limit=%s' % (p, request.args.get('limit', '25'))

    data = _get(path)
    next_page = data.get('next')
    if next_page:
        # just get the query params
        data['next'] = next_page.rsplit('/', 1)[-1]
    return data


@blueprint.route('/')
def index():
    return render_template('index.html', data=_list('/projects/'))


@blueprint.route('projects/<project:proj>/')
def project(proj):
    data = _list('/projects/%s/builds/' % proj)
    return render_template('project.html', project=proj, data=data)


@blueprint.route('projects/<project:proj>/builds/<int:build>')
def build(proj, build):
    build = _get('/projects/%s/builds/%d/' % (proj, build))['build']
    return render_template('build.html', project=proj, build=build)


@blueprint.route('projects/<project:proj>/builds/<int:build>/<run>/')
def run(proj, build, run):
    run = _get('/projects/%s/builds/%d/runs/%s/' % (proj, build, run))['run']
    prefix = JOBSERV_URL + '/projects/%s/builds/%d/runs/%s/' % (
        proj, build, run['name'])
    artifacts = [x[len(prefix):] for x in run['artifacts']]
    run['artifacts'] = artifacts
    return render_template('run.html', project=proj, build=build, run=run)


@blueprint.route('projects/<project:proj>/builds/<int:build>/<run>/'
                 'artifacts/<path:p>')
def run_artifact(proj, build, run, p):
    url = JOBSERV_URL + '/projects/%s/builds/%d/runs/%s/%s' % (
        proj, build, run, p)

    # Allow .html to render inside app rather than a redirect
    get = requests.get
    if current_user.is_authenticated:
        get = current_user.authenticated_get
    r = get(url, allow_redirects=p.endswith('.html'))
    if p.endswith('.html'):
        return r.text, r.status_code, {'Content-Type': 'text/html'}
    resp = make_response(r.text, r.status_code)
    for k, v in r.headers.items():
        resp.headers[k] = v
    return resp


@blueprint.route('projects/<project:proj>/builds/<int:build>/<run>/tests/')
def tests(proj, build, run):
    get = requests.get
    if current_user.is_authenticated:
        get = current_user.authenticated_get

    reports = []
    data = _get('/projects/%s/builds/%d/runs/%s/tests/' % (proj, build, run))
    for t in data['tests']:
        reports.append(t)
        r = get(t['url'])
        if r.status_code != 200:
            flash('Unable to get test results for %s from %s' % (
                t['name'], t['url']))
        t['results'] = r.json()['data']['test']['results']

    return render_template(
        'tests.html', project=proj, build=build, run=run, reports=reports)


@blueprint.route('projects/<project:proj>/triggers/')
def triggers(proj):
    secrets = []
    for x in _get('/project-triggers/'):
        if x['project'] == proj:
            secrets.append(x)
            x['secrets'] = list(x['secrets'].keys())
    return jsonify(secrets)
