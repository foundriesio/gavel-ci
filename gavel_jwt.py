# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>
import datetime
import os

import jwt
import requests


JWT_SECRET_FILE = os.environ.get('JWT_SECRET_FILE')


def _jwt_secret():
    if not JWT_SECRET_FILE:
        raise RuntimeError('No JWT_SECRET_FILE defined for deployment')
    with open(JWT_SECRET_FILE) as f:
        return f.read()


class User(object):
    """This class is used by both the JobServ and GavelCI sources. This means
       it *can't* depend on code in either module or we'll have a circular
       dependency. Its basically the glue so the two projects can understand
       what JWT is being passed between each other.
    """
    def __init__(self, login, email, name, is_admin):
        self.login = login
        self.email = email
        self.name = name
        self.is_admin = is_admin

    def __str__(self):
        return self.name

    def authorization_bearer(self):
        bearer = {
            'email': self.email,
            'login': self.login,
            'name': self.name,
            'is_admin': self.is_admin,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=30)
        }
        return jwt.encode(bearer, _jwt_secret(), 'HS256')

    def authenticated_get(self, url, *args, **kwargs):
        headers = kwargs.setdefault('headers', {})
        headers['Authorization'] = 'Bearer ' + self.authorization_bearer()
        return requests.get(url, *args, **kwargs)

    def authenticated_post(self, url, *args, **kwargs):
        headers = kwargs.setdefault('headers', {})
        headers['Authorization'] = 'Bearer ' + self.authorization_bearer()
        return requests.post(url, *args, **kwargs)
