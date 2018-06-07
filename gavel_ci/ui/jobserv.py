# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

from flask import Blueprint, render_template

blueprint = Blueprint('jobserv', __name__, url_prefix='/')


@blueprint.route('/')
def index():
    return render_template('index.html')
