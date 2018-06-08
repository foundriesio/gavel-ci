# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

import datetime
import secrets

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

from jobserv.jsend import ApiError

db = SQLAlchemy()


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

    @staticmethod
    def _authenticate_token(token):
        try:
            return ApiToken.query.filter(ApiToken.value == token).one().user
        except NoResultFound:
            return None

    @classmethod
    def authenticate(clazz, request_headers):
        auth = request_headers.get('Authorization')
        if auth:
            if auth.startswith('token '):
                return clazz._authenticate_token(auth.split(' ', 1)[1])
            else:
                ApiError('400', 'Invalid Authorization header')


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
