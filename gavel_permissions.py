# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>
import os

import jwt

from flask import request

from gavel_jwt import User
from jobserv.jsend import ApiError
from jobserv.models import Project


JWT_SECRET_FILE = os.environ.get('JWT_SECRET_FILE')


def _jwt_secret():
    if not JWT_SECRET_FILE:
        raise RuntimeError('No JWT_SECRET_FILE defined for deployment')
    with open(JWT_SECRET_FILE) as f:
        return f.read()


class JobServUser(User):
    @staticmethod
    def _authenticate_bearer(bearer):
        try:
            bearer = jwt.decode(bearer, _jwt_secret(), algorithms=['HS256'])
            return JobServUser(bearer['login'], bearer['email'],
                               bearer['name'], bearer['is_admin'])
        except jwt.PyJWTError as e:
            raise ApiError(401, str(e))

    @classmethod
    def authenticate(clazz, request_headers):
        auth = request_headers.get('Authorization')
        if auth:
            if auth and auth.startswith('Bearer '):
                return clazz._authenticate_bearer(auth.split(' ', 1)[1])
            else:
                ApiError('400', 'Invalid Authorization header')

    @staticmethod
    def get_internal():
        return JobServUser('gavin', 'gavin@gavelci.us', 'Gavin Gavel', True)


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
    u = JobServUser.authenticate(request.headers)
    if not u or not u.is_admin:
        raise ApiError(403, 'You are not allowed to perform this operation')
    return u


def assert_can_promote(project, build_id):
    assert_internal_user()


def assert_can_build(project):
    assert_internal_user()


def internal_get(url, *args, **kwargs):
    return JobServUser.get_internal().authenticated_get(url, *args, **kwargs)


def internal_post(url, *args, **kwargs):
    return JobServUser.get_internal().authenticated_post(url, *args, **kwargs)
