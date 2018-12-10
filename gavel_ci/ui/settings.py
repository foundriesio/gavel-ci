# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, fresh_login_required, login_required

blueprint = Blueprint('settings', __name__, url_prefix='/settings')


@blueprint.route('/')
@login_required
def index():
    return render_template('settings.html', user=current_user)


@blueprint.route('/token/delete/<int:token>/')
@fresh_login_required
def token_delete(token):
    if not current_user.delete_token(token):
        flash('Could not find api token "%d" to delete' % token)
    return redirect(url_for('settings.index'))


@blueprint.route('/token/', methods=('POST',))
@fresh_login_required
def token_create():
    desc = request.form.get('description')
    if not desc:
        flash('You must enter a description for the token')
        return redirect(url_for('settings.index'))

    v = current_user.create_token(desc)
    flash('New token created: ' + v)
    flash(
        'Make sure you save the value, you won\'t be able to access it again.')
    return redirect(url_for('settings.index'))
