# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

from flask import Flask
from flask_migrate import Migrate

from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import UnicodeConverter

from gavel_ci.settings import PROJECT_NAME_REGEX


class ProjectConverter(UnicodeConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        if PROJECT_NAME_REGEX:
            self.regex = PROJECT_NAME_REGEX


def create_app(settings_object='gavel_ci.settings'):
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config.from_object(settings_object)

    ProjectConverter.settings = settings_object
    app.url_map.converters['project'] = ProjectConverter

    from gavel_ci.models import db, User
    db.init_app(app)
    Migrate(app, db)

    from flask_login import LoginManager
    login_manager = LoginManager(app)
    login_manager.login_view = 'app.login'
    login_manager.session_protection = 'strong'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    import gavel_ci.ui
    gavel_ci.ui.register_blueprints(app)

    return app
