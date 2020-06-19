# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>
import logging
import re
import requests
from flask import (
    abort,
    Blueprint,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, fresh_login_required

from gavel_ci.settings import JOBSERV_URL


blueprint = Blueprint('jobserv', __name__, url_prefix='/')


def _raw_get(path, **kwargs):
    assert path[0] == '/'

    get = requests.get
    if current_user.is_authenticated:
        get = current_user.authenticated_get

    url = JOBSERV_URL + path
    return get(url, **kwargs)


def _get(path):
    r = _raw_get(path)
    if r.status_code == 401:
        abort(redirect(url_for('auth.login', next=request.url)))
    elif r.status_code != 200:
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


@blueprint.route('/projects/')
def projects_list():
    return index()


@blueprint.route('about/')
def about():
    return render_template('about.html')


@blueprint.route('status/')
def status():
    health = _get('/health/runs/')['health']
    workers = _get('/workers/')['workers']
    return render_template('status.html', health=health, workers=workers)


@blueprint.route('project/', methods=('POST',))
@fresh_login_required
def project_create():
    name = request.form['name']
    r = current_user.authenticated_post(
        JOBSERV_URL + '/projects/', json={'name': name})
    if r.status_code != 201:
        abort(make_response(r.text, r.status_code))
    return redirect(url_for('jobserv.project', proj=name))


@blueprint.route('projects/<project:proj>/')
def project(proj):
    data = _list('/projects/%s/builds/' % proj)
    return render_template('project.html', project=proj, data=data)


@blueprint.route('projects/<project:proj>/new-trigger-github/')
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


@blueprint.route('projects/<project:proj>/new-trigger-github/',
                 methods=('POST',))
@fresh_login_required
def project_create_github_trigger(proj):
    if current_user.is_admin:
        proj = _get('/projects/%s/' % proj)['project']
        _assert_form(proj, request.form)
        url = JOBSERV_URL + '/github/%s/webhook/' % proj['name']
        r = current_user.authenticated_post(url, json=request.form)
        if r.status_code != 201:
            abort(make_response(r.text, r.status_code))
        flash('Trigger created for GitHub project')
        return redirect(url_for('jobserv.project', proj=proj['name']))
    abort(404)


@blueprint.route('projects/<project:proj>/history/<run>/')
def project_run_history(proj, run):
    history = _get('/projects/%s/history/%s/' % (proj, run))['runs']
    return render_template(
        'run_history.html', project=proj, run=run, history=history)


@blueprint.route('projects/<project:proj>/builds/<int:build>/')
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
                 'console')
def console(proj, build, run):
    return render_template('console.html', proj=proj, build=build, run=run)


@blueprint.route('projects/<project:proj>/builds/<int:build>/<run>/'
                 'console/progress-pattern')
def console_progress_pattern(proj, build, run):
    r = _raw_get(
        f'/projects/{proj}/builds/{build}/runs/{run}/progress-regex')
    if r.status_code == 404:
        return ""
    elif r.status_code == 200:
        return r.json()['data']['progress-pattern']
    return r.content, r.status_code


def _progress_from_content(content, regex):
    # findall doesn't capture names so:
    matches = list(re.finditer(regex, content))
    if matches:
        current = matches[-1].group('current')
        total = matches[-1].group('total')
        try:
            current = int(current)
            total = int(total)
            if current == 0:
                return 0
            return int(current / total * 100)
        except ValueError:
            logging.warning("Unable to convert %s progress %s / %s",
                            request.url, current, total)
    return None


@blueprint.route('projects/<project:proj>/builds/<int:build>/<run>/'
                 'console/tail')
def console_tail(proj, build, run):
    response = _raw_get(
        f'/projects/{proj}/builds/{build}/runs/{run}/console.log',
        headers={
            'X-OFFSET': request.headers.get('X-OFFSET', '0'),
            'Range': request.headers.get('Range', ''),
        },
        timeout=1,
    )
    pass_through_headers = [
        (header, value)
        for header, value in response.headers.items()
        if header.lower() in (
            'cache-control',
            'content-type',
            'x-run-status',
        )
    ]

    regex = request.headers.get('X-PROGRESS-PATTERN')
    if regex:
        percent_complete = _progress_from_content(response.content, regex)
        if percent_complete is not None:
            pass_through_headers.append(
                ("x-run-progress", str(percent_complete)))
    return response.content, response.status_code, pass_through_headers

@blueprint.route('projects/<project:proj>/builds/<int:build>/<run>/'
                 'artifacts/<path:p>')
def run_artifact(proj, build, run, p):
    # Allow .html to render inside app rather than a redirect
    allow_redirects = False
    if p.endswith('.html') or p.endswith('.log') or p.endswith('.txt'):
        # show .txt, log, and .html files inline
        allow_redirects = True
    r = _raw_get('/projects/%s/builds/%d/runs/%s/%s' % (proj, build, run, p),
                 allow_redirects=allow_redirects)
    if p.endswith('.html'):
        return r.text, r.status_code, {'Content-Type': 'text/html'}
    resp = make_response(r.text, r.status_code)
    for k, v in r.headers.items():
        resp.headers[k] = v
    return resp


@blueprint.route('projects/<project:proj>/builds/<int:build>/<run>/'
                 '.simulate.sh')
def run_simulate(proj, build, run):
    r = _raw_get('/projects/%s/builds/%d/runs/%s/.simulate.sh' % (
        proj, build, run))
    resp = make_response(r.text, r.status_code)
    for k, v in r.headers.items():
        resp.headers[k] = v
    return resp


@blueprint.route('projects/<project:proj>/builds/<int:build>/<run>/rerun',
                 methods=('POST',))
@fresh_login_required
def run_rerun(proj, build, run):
    url = JOBSERV_URL + '/projects/%s/builds/%s/runs/%s/rerun' % (
        proj, build, run)
    r = current_user.authenticated_post(url)
    if r.status_code != 200:
        abort(make_response(r.text, r.status_code))
    return redirect(url_for('jobserv.run', proj=proj, build=build, run=run))


@blueprint.route('projects/<project:proj>/builds/<int:build>/<run>/cancel',
                 methods=('POST',))
@fresh_login_required
def run_cancel(proj, build, run):
    url = JOBSERV_URL + '/projects/%s/builds/%s/runs/%s/cancel' % (
        proj, build, run)
    r = current_user.authenticated_post(url)
    if r.status_code != 202:
        abort(make_response(r.text, r.status_code))
    return redirect(url_for('jobserv.run', proj=proj, build=build, run=run))


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
