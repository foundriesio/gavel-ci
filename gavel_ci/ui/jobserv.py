# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>
import requests

from flask import (
    Blueprint, abort, flash, jsonify, make_response, redirect, render_template,
    request, url_for
)
from flask_login import current_user

from gavel_ci.settings import JOBSERV_URL

blueprint = Blueprint('jobserv', __name__, url_prefix='/')


def _list(path):
    assert path[0] == '/'

    url = JOBSERV_URL + path
    page = request.args.get('page')
    if page:
        limit = request.args.get('limit', '25')
        url += '?page=%s&limit=%s' % (page, limit)

    r = requests.get(url)
    if r.status_code != 200:
        abort(make_response(r.text, r.status_code))

    data = r.json()['data']
    next_page = data.get('next')
    if next_page:
        # just get the query params
        data['next'] = next_page.rsplit('/', 1)[-1]
    return data


def _get(path):
    assert path[0] == '/'

    headers = {}
    if current_user.is_authenticated:
        headers['Authorization'] = \
            'Bearer ' + current_user.authorization_bearer()

    url = JOBSERV_URL + path
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        abort(make_response(r.text, r.status_code))
    return r.json()['data']


@blueprint.route('/')
def index():
    return render_template('index.html', data=_list('/projects/'))


@blueprint.route('about/')
def about():
    return render_template('about.html')


@blueprint.route('status/')
def status():
    health = _get('/health/runs/')
    workers = _get('/workers/')['workers']
    return render_template('status.html', health=health, workers=workers)


@blueprint.route('project/', methods=('POST',))
def project_create():
    name = request.form['name']
    headers = {}
    if current_user.is_authenticated:
        headers['Authorization'] = \
            'Bearer ' + current_user.authorization_bearer()

    url = JOBSERV_URL + '/projects/'
    r = requests.post(url, headers=headers, json={'name': name})
    if r.status_code != 201:
        abort(make_response(r.text, r.status_code))
    return redirect(url_for('jobserv.project', proj=name))


@blueprint.route('projects/<proj>/')
def project(proj):
    data = _list('/projects/%s/builds/' % proj)
    return render_template('project.html', project=proj, data=data)


@blueprint.route('projects/<proj>/new-trigger-github/')
def project_define_github_trigger(proj):
    if current_user.is_authenticated and current_user.is_admin:
        proj = _get('/projects/%s/' % proj)['project']
        return render_template('github-trigger.html', project=proj)
    abort(404)


def _assert_form(proj, form):
    required = {
        'owner': 'GithHub Project Owner',
        'project': 'GitHub Project',
        'githubtok': 'GitHub Personal Access Token',
    }
    missing = []
    for x in required.keys():
        if x not in form:
            missing.append(required[x])
    if missing:
        flash('Missing required fields: %s', ', '.join(missing))
        abort(redirect(url_for(
            'jobserv.project_define_github_trigger', proj=proj['name'])))


@blueprint.route('projects/<proj>/new-trigger-github/', methods=('POST',))
def project_create_github_trigger(proj):
    if current_user.is_authenticated and current_user.is_admin:
        proj = _get('/projects/%s/' % proj)['project']
        _assert_form(proj, request.form)
        headers = {
            'Authorization': 'Bearer ' + current_user.authorization_bearer(),
        }
        url = JOBSERV_URL + '/projects/%s/gh_trigger/' % proj['name']
        r = requests.post(url, headers=headers, json=request.form)
        if r.status_code != 201:
            abort(make_response(r.text, r.status_code))
        flash('Trigger created for GitHub project')
        return redirect(url_for('jobserv.project', proj=proj['name']))
    abort(404)


@blueprint.route('projects/<proj>/builds/<int:build>')
def build(proj, build):
    build = _get('/projects/%s/builds/%d/' % (proj, build))['build']
    return render_template('build.html', project=proj, build=build)


@blueprint.route('projects/<proj>/builds/<int:build>/<run>/')
def run(proj, build, run):
    run = _get('/projects/%s/builds/%d/runs/%s/' % (proj, build, run))['run']
    prefix = JOBSERV_URL + '/projects/%s/builds/%d/runs/%s/' % (
        proj, build, run['name'])
    artifacts = [x[len(prefix):] for x in run['artifacts']]
    run['artifacts'] = artifacts
    return render_template('run.html', project=proj, build=build, run=run)


@blueprint.route('projects/<proj>/builds/<int:build>/<run>/artifacts/<path:p>')
def run_artifact(proj, build, run, p):
    url = JOBSERV_URL + '/projects/%s/builds/%d/runs/%s/%s' % (
        proj, build, run, p)

    # Allow .html to render inside app rather than a redirect
    r = requests.get(url, allow_redirects=p.endswith('.html'))
    if p.endswith('.html'):
        return r.text, r.status_code, {'Content-Type': 'text/html'}
    resp = make_response(r.text, r.status_code)
    for k, v in r.headers.items():
        resp.headers[k] = v
    return resp


@blueprint.route('projects/<proj>/builds/<int:build>/<run>/.simulate.sh')
def run_simulate(proj, build, run):
    url = JOBSERV_URL + '/projects/%s/builds/%d/runs/%s/.simulate.sh' % (
        proj, build, run)

    # Allow .html to render inside app rather than a redirect
    r = requests.get(url)
    resp = make_response(r.text, r.status_code)
    for k, v in r.headers.items():
        resp.headers[k] = v
    return resp


@blueprint.route('projects/<proj>/builds/<int:build>/<run>/tests/')
def tests(proj, build, run):
    reports = []
    data = _get('/projects/%s/builds/%d/runs/%s/tests/' % (proj, build, run))
    for t in data['tests']:
        reports.append(t)
        r = requests.get(t['url'])
        if r.status_code != 200:
            raise NotImplementedError()
        t['results'] = r.json()['data']['test']['results']

    return render_template(
        'tests.html', project=proj, build=build, run=run, reports=reports)


@blueprint.route('projects/<proj>/triggers/')
def triggers(proj):
    secrets = []
    for x in _get('/project-triggers/'):
        if x['project'] == proj:
            secrets.append(x)
            x['secrets'] = list(x['secrets'].keys())
    return jsonify(secrets)
