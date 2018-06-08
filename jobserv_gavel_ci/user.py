# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>
import datetime
import os

import jwt


from jobserv.jsend import ApiError

JWT_SECRET_FILE = os.environ.get('JWT_SECRET_FILE')


def _jwt_secret():
    if not JWT_SECRET_FILE:
        raise RuntimeError('No JWT_SECRET_FILE defined for deployment')
    with open(JWT_SECRET_FILE) as f:
        return f.read()


class User(object):
    def __init__(self, login, email, name, is_admin):
        self.login = login
        self.email = email
        self.name = name
        self.is_admin = is_admin

    def authorization_bearer(self):
        bearer = {
            'email': self.email,
            'login': self.login,
            'name': self.name,
            'is_admin': self.is_admin,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=30)
        }
        return jwt.encode(bearer, _jwt_secret(), 'HS256').decode()

    @staticmethod
    def _authenticate_bearer(bearer):
        try:
            bearer = jwt.decode(bearer, _jwt_secret(), algorithms=['HS256'])
            return User(bearer['login'], bearer['email'], bearer['name'],
                        bearer['is_admin'])
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
        return User('gavin', 'gavin@gavelci.us', 'Gavin Gavel', True)
