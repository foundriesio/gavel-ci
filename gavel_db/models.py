# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

import datetime
import os
import secrets

import jwt

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

from jobserv.jsend import ApiError

JWT_SECRET_FILE = os.environ.get('JWT_SECRET_FILE')
INTERNAL_USER_ID = os.environ.get('INTERNAL_USER_ID')

db = SQLAlchemy()


def _jwt_secret():
    if not JWT_SECRET_FILE:
        raise RuntimeError('No JWT_SECRET_FILE defined for deployment')
    with open(JWT_SECRET_FILE) as f:
        return f.read()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    login = db.Column(db.String(128), nullable=True)
    name = db.Column(db.String(128), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    tokens = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    api_tokens = db.relationship('ApiToken')

    def create_token(self, description):
        value = secrets.token_urlsafe()
        db.session.add(ApiToken(self, description, value))
        db.session.commit()
        return value

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
    def _authenticate_token(token):
        try:
            return ApiToken.query.filter(ApiToken.value == token).one().user
        except NoResultFound:
            return None

    @staticmethod
    def _authenticate_bearer(bearer):
        try:
            bearer = jwt.decode(bearer, _jwt_secret(), algorithms=['HS256'])
            u = User()
            u.email = bearer['email']
            u.name = bearer['name']
            u.is_admin = bearer['is_admin']
            return u
        except jwt.PyJWTError as e:
            raise ApiError(401, str(e))

    @classmethod
    def authenticate(clazz, request_headers):
        auth = request_headers.get('Authorization')
        if auth:
            if auth.startswith('token '):
                return clazz._authenticate_token(auth.split(' ', 1)[1])
            elif auth and auth.startswith('Bearer '):
                return clazz._authenticate_bearer(auth.split(' ', 1)[1])
            else:
                ApiError('400', 'Invalid Authorization header')

    @classmethod
    def get_internal(clazz):
        if not INTERNAL_USER_ID:
            raise RuntimeError('No INTERNAL_USER_ID defined for deployment')
        return clazz.query.get(int(INTERNAL_USER_ID))


class ApiToken(db.Model):
    __tablename__ = 'apitokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    description = db.Column(db.String(80), nullable=True)
    value = db.Column(db.String(80), nullable=False)

    user = db.relationship(User)

    def __init__(self, user, description, value):
        self.user_id = user.id
        self.description = description
        self.value = value
