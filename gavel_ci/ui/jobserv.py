# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>
import requests

from flask import Blueprint, abort, render_template, request

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

    url = JOBSERV_URL + path
    r = requests.get(url)
    if r.status_code != 200:
        abort(make_response(r.text, r.status_code))
    return r.json()['data']


@blueprint.route('/')
def index():
    return render_template('index.html', data=_list('/projects/'))


@blueprint.route('projects/<proj>/')
def project(proj):
    return render_template('project.html', project=proj)
