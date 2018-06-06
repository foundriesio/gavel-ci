# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from gavel_ci.models import User, db

blueprint = Blueprint('auth', __name__, url_prefix='/auth')


@blueprint.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.test'))

    email = request.args['email']
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User()
        user.email = email
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect(url_for('auth.test'))


@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.test'))


@blueprint.route('/test')
def test():
    return render_template('index.html')
