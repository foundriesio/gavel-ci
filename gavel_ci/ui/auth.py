# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>
import json

from urllib.parse import urlparse, urljoin

from flask import Blueprint, redirect, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from requests_oauthlib import OAuth2Session

from gavel_ci.flask import user_logged_in
from gavel_ci.models import User, db
from gavel_ci.settings import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET

blueprint = Blueprint('auth', __name__, url_prefix='/auth')


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


@blueprint.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('jobserv.index'))

    github = OAuth2Session(GITHUB_CLIENT_ID)
    authorization_url, state = github.authorization_url(
        'https://github.com/login/oauth/authorize')

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    destination = request.args.get('next')
    # is_safe_url should check if the url is safe for redirects.
    # See http://flask.pocoo.org/snippets/62/ for an example.
    if is_safe_url(destination):
        session['next'] = destination
    return redirect(authorization_url)


@blueprint.route("/gh-authorized")
def callback():
    github = OAuth2Session(GITHUB_CLIENT_ID, state=session['oauth_state'])
    token = github.fetch_token('https://github.com/login/oauth/access_token',
                               client_secret=GITHUB_CLIENT_SECRET,
                               authorization_response=request.url)

    data = github.get('https://api.github.com/user').json()
    user = User.query.filter_by(login=data['login']).first()
    if user is None:
        user = User()
        user.login = data['login']
        db.session.add(user)
    user.email = data.get('email')
    user.name = data['name']
    user.tokens = json.dumps(token)
    db.session.commit()
    user_logged_in.send(user)
    login_user(user)
    destination = session.get('next')
    if destination:
        return redirect(destination)
    return redirect(url_for('jobserv.index'))


@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('jobserv.index'))
