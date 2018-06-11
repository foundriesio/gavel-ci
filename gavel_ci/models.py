# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

from jobserv_gavel_ci.user import User as JobServUser

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

    def authorization_bearer(self):
        return JobServUser(
            self.login, self.email, self.name, self.is_admin
        ).authorization_bearer()
