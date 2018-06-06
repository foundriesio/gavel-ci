# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

from flask import Flask
from flask_migrate import Migrate

from werkzeug.contrib.fixers import ProxyFix


def create_app(settings_object='gavel_ci.settings'):
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config.from_object(settings_object)

    from gavel_ci.models import db
    db.init_app(app)
    Migrate(app, db)

    import gavel_ci.ui
    gavel_ci.ui.register_blueprints(app)

    return app
