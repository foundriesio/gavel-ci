# Copyright (C) 2018 Open Source Foundries
# Author: Andy Doan <andy@opensourcefoundries.com>

BLUEPRINTS = ()


def register_blueprints(app):
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)
