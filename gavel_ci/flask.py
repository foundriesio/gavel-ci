# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

from blinker import Namespace
from flask import Flask, has_request_context, request
from flask_migrate import Migrate
import json_logging
from werkzeug.routing import PathConverter

event_signals = Namespace()
user_logged_in = event_signals.signal('user_logged_in')

class CustomLogFormatterMixin:
    """
    A common mixin to customize json_logging formatters to include a context from `log_add_ctx`.
    It makes sure that the context values are propagated to all logs within the request context.
    """

    def _format_log_object(self, record, request_util):
        log_obj = super()._format_log_object(record, request_util)
        if has_request_context() and hasattr(request, "logctx"):
            log_obj.update(request.logctx)
        return log_obj


class CustomJSONLogWebFormatter(CustomLogFormatterMixin, json_logging.JSONLogWebFormatter):
    pass


class CustomJSONRequestLogFormatter(CustomLogFormatterMixin, json_logging.JSONRequestLogFormatter):
    pass



def create_app(settings_object='gavel_ci.settings'):
    app = Flask(__name__)
    app.config.from_object(settings_object)

    app.url_map.converters['project'] = PathConverter

    # Reset json_logging's internal state before initialization.
    # This ensures json_logging is correctly configured each time the app is created,
    # addressing the issue with its use of global variables.
    # init loggers conditionally, just once, because json_logging goes mad otherwise
    if json_logging._current_framework is None:
        json_logging.init_flask(custom_formatter=CustomJSONLogWebFormatter, enable_json=True)
        json_logging.config_root_logger()
    # init instrumentation unconditionally, as it is a different app every time.
    json_logging.init_request_instrument(
        app, custom_formatter=CustomJSONRequestLogFormatter, exclude_url_patterns=[r"/healthz"]
    )
    _monkey_patch_json_logging_request_logger()

    from gavel_ci.models import db, User
    db.init_app(app)
    Migrate(app, db)

    from flask_login import LoginManager
    login_manager = LoginManager(app)
    login_manager.login_view = 'app.login'
    login_manager.refresh_view = 'auth.login'
    login_manager.session_protection = 'strong'

    @login_manager.user_loader
    def load_user(user_id):
        u = User.query.get(int(user_id))
        request.logctx = {"user": u.login} 
        return u

    import gavel_ci.ui
    gavel_ci.ui.register_blueprints(app)

    return app


def _monkey_patch_json_logging_request_logger():
    # Monkey-patch a memory leak in `json_logging` causing indefinite handlers during app reloading.
    # see https://github.com/bobbui/json-logging-python/blob/master/json_logging/__init__.py#L165
    # TODO: This needs to be removed once it is fixed upstream.
    import logging  # noqa

    bad_logger = logging.getLogger("flask-request-logger")
    bad_logger.handlers = [bad_logger.handlers[0]]