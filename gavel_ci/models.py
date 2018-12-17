# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

import datetime

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

    def authenticated_get(self, url, *args, **kwargs):
        return JWTUser(
            self.login, self.email, self.name, self.is_admin
        ).authenticated_get(url, *args, **kwargs)

    def authenticated_post(self, url, *args, **kwargs):
        return JWTUser(
            self.login, self.email, self.name, self.is_admin
        ).authenticated_post(url, *args, **kwargs)
