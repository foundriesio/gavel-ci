# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

import requests

from flask import request

from jobserv.jsend import ApiError
from jobserv.models import Project

from gavel_db.models import User


def projects_list():
    """User see list of all Projects."""
    return Project.query


def project_can_access(project_path):
    """User can see Builds of all Projects."""
    return True


def run_can_access_secrets(run):
    """Can user access .rundef.json for a Run."""
    try:
        assert_internal_user()
    except ApiError:
        return False
    return True


def health_can_access(health_path):
    """User has access to all health endpoints."""
    return True


def assert_internal_user():
    u = User.authenticate(request.headers)
    if not u or not u.is_admin:
        raise ApiError(403, 'You are not allowed to perform this operation')


def assert_can_promote(project, build_id):
    assert_internal_user()


def internal_get(url, *args, **kwargs):
    headers = kwargs.setdefault('headers', {})
    headers['Authorization'] = \
        'Bearer ' + User.get_internal().authorization_bearer()
    return requests.get(url, *args, **kwargs)


def internal_post(url, *args, **kwargs):
    headers = kwargs.setdefault('headers', {})
    headers['Authorization'] = \
        'Bearer ' + User.get_internal().authorization_bearer()
    return requests.get(url, *args, **kwargs)
