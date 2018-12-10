# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>

from flask import Blueprint, render_template
from flask_login import current_user, login_required

blueprint = Blueprint('settings', __name__, url_prefix='/settings')


@blueprint.route('/')
@login_required
def index():
    return render_template('settings.html', user=current_user)
