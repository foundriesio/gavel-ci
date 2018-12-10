# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

import datetime
import secrets

import bcrypt

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

from gavel_jwt import User as JWTUser

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=True)
    name = db.Column(db.String(128), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    tokens = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    api_tokens = db.relationship('ApiToken')

    def authenticated_get(self, url, *args, **kwargs):
        return JWTUser(
            self.login, self.email, self.name, self.is_admin
        ).authenticated_get(url, *args, **kwargs)

    def authenticated_post(self, url, *args, **kwargs):
        return JWTUser(
            self.login, self.email, self.name, self.is_admin
        ).authenticated_post(url, *args, **kwargs)

    def create_token(self, description):
        value = secrets.token_urlsafe()
        db.session.add(ApiToken(self, description, value))
        db.session.commit()
        return value

    def delete_token(self, token_id):
        for t in self.api_tokens:
            if t.id == token_id:
                db.session.delete(t)
                db.session.commit()
                return True


class ApiToken(db.Model):
    __tablename__ = 'apitokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    description = db.Column(db.String(80), nullable=True)
    last_used = db.Column(db.DateTime, nullable=True)
    value = db.Column(db.String(80), nullable=False)

    user = db.relationship(User)

    def __init__(self, user, description, value):
        self.user_id = user.id
        self.description = description
        self.value = bcrypt.hashpw(value.encode(), bcrypt.gensalt())

    @classmethod
    def find_user(clazz, user, token):
        token = token.encode()
        tokens = clazz.query.join(User).filter(User.login == user)
        for t in tokens:
            if bcrypt.checkpw(token, t.value.encode()):
                return t.user
