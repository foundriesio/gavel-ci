# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>
import requests

from flask import (
    Blueprint, abort, make_response, render_template, request,
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
